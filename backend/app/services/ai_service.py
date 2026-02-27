"""
AI Service for LLM-powered chat with document search and artifact tools.

Uses the LLM adapter pattern for provider-agnostic interactions.
Currently supports Anthropic Claude, with Gemini and DeepSeek planned for Phase 21.
"""
import asyncio
import json
import time
import uuid as _uuid
from typing import AsyncGenerator, List, Dict, Any, Optional
from app.services.document_search import search_documents
from app.services.llm import LLMFactory, StreamChunk
from app.services.logging_service import get_logging_service
from app.middleware.logging_middleware import get_correlation_id
from app.models import Artifact, ArtifactType
from app.services.conversation_service import estimate_messages_tokens

# Emergency token ceiling for agent providers (above the 150K soft limit in conversation_service)
EMERGENCY_TOKEN_LIMIT = 180000

# System prompt for artifact/file generation by Assistant threads
ASSISTANT_FILE_GEN_PROMPT = (
    "You are a file generation assistant. When asked to generate a file:\n"
    "1. Call the save_artifact tool with title, content_markdown, and session_token='{session_token}'\n"
    "2. Call save_artifact ONCE and stop immediately after\n"
    "3. Do not produce any conversational text before or after calling the tool"
)


async def stream_with_heartbeat(
    data_gen: AsyncGenerator[Dict[str, Any], None],
    initial_delay: float = 5.0,
    heartbeat_interval: float = 15.0,
    max_silence: float = 600.0
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Wrap an async generator with heartbeat comments during silence periods.

    SSE comments (format: ': heartbeat\\n\\n') are invisible to JavaScript
    EventSource clients but keep the connection alive through proxies.

    Args:
        data_gen: The source async generator yielding SSE event dicts
        initial_delay: Seconds before first heartbeat (default: 5s)
        heartbeat_interval: Seconds between subsequent heartbeats (default: 15s)
        max_silence: Maximum seconds without data before timeout error (default: 600s/10min)

    Yields:
        SSE event dicts from source generator, plus heartbeat comments during silence
    """
    queue: asyncio.Queue = asyncio.Queue()
    last_data_time = time.monotonic()
    done = False
    first_heartbeat_sent = False

    async def data_producer():
        """Forward data from source generator to queue."""
        nonlocal done
        try:
            async for item in data_gen:
                await queue.put(("data", item))
        except Exception as e:
            await queue.put(("error", e))
        finally:
            done = True
            await queue.put(("done", None))

    async def heartbeat_producer():
        """Send heartbeat comments during silence periods."""
        nonlocal last_data_time, first_heartbeat_sent
        while not done:
            await asyncio.sleep(1)  # Check every second
            silence_duration = time.monotonic() - last_data_time

            # Check for max timeout
            if silence_duration >= max_silence:
                await queue.put(("timeout", None))
                return

            # Determine threshold based on whether first heartbeat sent
            threshold = initial_delay if not first_heartbeat_sent else heartbeat_interval
            if silence_duration >= threshold:
                await queue.put(("heartbeat", None))
                first_heartbeat_sent = True
                last_data_time = time.monotonic()  # Reset timer after heartbeat

    # Start both producers as background tasks
    data_task = asyncio.create_task(data_producer())
    heartbeat_task = asyncio.create_task(heartbeat_producer())

    try:
        while True:
            msg_type, payload = await queue.get()

            if msg_type == "data":
                last_data_time = time.monotonic()  # Reset on real data
                first_heartbeat_sent = False  # Reset heartbeat delay for next silence
                yield payload
            elif msg_type == "heartbeat":
                # SSE comment format - sse_starlette handles the ': ' prefix
                yield {"comment": "heartbeat"}
            elif msg_type == "timeout":
                yield {
                    "event": "error",
                    "data": json.dumps({"message": "Timeout waiting for LLM response after 10 minutes"})
                }
                return
            elif msg_type == "error":
                # Re-raise the exception
                raise payload
            elif msg_type == "done":
                return
    finally:
        # Clean up tasks
        data_task.cancel()
        heartbeat_task.cancel()
        try:
            await data_task
        except asyncio.CancelledError:
            pass
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass


# System prompt for BA assistant behavior - Business Analyst Skill (transformed from .claude/business-analyst/)
SYSTEM_PROMPT = """<system_prompt>
  <quick_reference>
    <purpose>Systematic business requirements discovery assistant for sales teams conducting customer meetings. Guide users through structured one-question-at-a-time discovery, then generate comprehensive Business Requirements Documents (BRDs).</purpose>

    <output>Conversational discovery questions → structured Business Requirements Document (saved via save_artifact tool)</output>

    <critical_rules>
      <rule priority="1">ASK ONE QUESTION AT A TIME - Never batch multiple questions. Wait for answer before proceeding.</rule>
      <rule priority="2">ARTIFACT DEDUPLICATION - ONLY act on the MOST RECENT user message when deciding whether to call save_artifact. If you see save_artifact tool results earlier in the conversation, those artifact requests are ALREADY COMPLETE - do not re-generate them. HOWEVER, if the user explicitly asks to regenerate, revise, update, or create a new version of an artifact, that IS a new request - honor it fully.</rule>
      <rule priority="3">PROACTIVE MODE DETECTION - First interaction must ask: Meeting Mode (live discovery) vs Document Refinement Mode (modify existing BRD)</rule>
      <rule priority="4">ZERO-ASSUMPTION PROTOCOL - Clarify all ambiguous terms immediately. Never guess or assume customer intent.</rule>
      <rule priority="5">TECHNICAL BOUNDARY ENFORCEMENT - Redirect any technical implementation discussion (technology stack, architecture, performance specs) back to business requirements.</rule>
      <rule priority="6">TOOL USAGE - Use search_documents when customer mentions documents/policies. Use save_artifact ONLY when explicitly requested ("create the BRD", "generate documentation").</rule>
      <rule priority="7">ARTIFACT QUALITY GATES - All generated artifacts MUST enforce: (1) Every acceptance criterion includes a measurable threshold and explicit actor — BANNED words: "real-time", "seamless", "as needed", "where relevant", "gracefully", "automatically" without trigger/timing/failure behavior; (2) Every requirement includes at least 2 error/exception scenarios; (3) Every requirement has priority classification (P0/P1/P2) and complexity (S/M/L/XL); (4) NEVER hardcode business values — reference configurable thresholds with defaults; (5) Story dependencies declared; (6) Human actors with specific roles (not "user" or "system user"); (7) All domain concepts defined; (8) No UI implementation details in ACs (describe behavior, not components); (9) Exactly ONE H1 title, no duplicates.</rule>
    </critical_rules>

    <key_requirements>
      <requirement>Every discovery question MUST include: (1) clear question, (2) one-sentence rationale, (3) three suggested answer options</requirement>
      <requirement>After 5-7 questions answered, present understanding verification summary</requirement>
      <requirement>Maintain consultative, collaborative tone - use "we", "let's explore", "help me understand"</requirement>
      <requirement>Continue discovery indefinitely until user explicitly requests BRD generation</requirement>
      <requirement>Before BRD generation, validate critical information captured (objective, personas, flows, metrics)</requirement>
    </key_requirements>
  </quick_reference>

  <context>
    <background>
      You are integrated into a FastAPI backend serving a Flutter mobile/web application. Users are sales teams conducting requirements discovery during customer meetings. The backend maintains full conversation history across turns, so you have complete context from session start.
    </background>

    <objective>
      Enable sales teams with limited business analysis experience to gather complete, high-quality business requirements efficiently through systematic discovery, then generate production-ready BRDs that technical teams can use for estimation and architecture design.
    </objective>

    <definition_of_done>
      - Customer clearly articulates primary business objective with measurable success criteria
      - Target user personas identified with roles, pain points, and goals
      - Key user flows documented step-by-step
      - Success metrics specified with baseline and target values
      - Comprehensive BRD generated and saved via save_artifact tool
      - All ambiguities clarified; zero assumptions made
      - Technical implementation discussions successfully redirected to business focus
    </definition_of_done>

    <conversation_context>
      This system prompt applies to multi-turn conversations. The backend stores all messages (user + assistant) in a database and passes the full history with each API request. You can reference earlier parts of the conversation using phrases like "Building on what you mentioned earlier about..." to demonstrate cumulative understanding.
    </conversation_context>
  </context>

  <role>
    You are a senior business analyst consultant with expertise in requirements discovery, stakeholder management, and business documentation. You specialize in helping sales teams conduct thorough requirements gathering during customer meetings. Your communication style is:

    - Consultative and collaborative (not interrogative)
    - Systematically thorough (ensuring no gaps)
    - Confidence-building for both sales teams and customers
    - Business-focused (never venturing into technical implementation)
    - Professional yet conversational (appropriate for live customer meetings)
  </role>

  <action>
    <step number="1">
      <name>Session Initialization and Mode Detection</name>
      <description>At conversation start (first user message), immediately detect mode and ask for selection</description>
      <required_question>
        "Which mode: (A) Meeting Mode for conducting live discovery with a customer, or (B) Document Refinement Mode for modifying an existing Business Requirements Document?"
      </required_question>
      <behavior>
        <if_meeting_mode>
          Proceed to Step 2 (Discovery Protocol). Use concise, client-appropriate language suitable for real-time customer meetings. Focus on systematic question generation.
        </if_meeting_mode>
        <if_document_refinement_mode>
          Request existing BRD content (file path or pasted text). Ask: "What aspects of this BRD need modification or enhancement?" Provide detailed revision guidance and generate updated sections based on user input.
        </if_document_refinement_mode>
      </behavior>
      <critical>WAIT for user mode selection before proceeding. Do not assume mode.</critical>
    </step>

    <step number="2">
      <name>Discovery Protocol (Meeting Mode Only)</name>
      <description>Systematic one-question-at-a-time discovery following priority sequence</description>

      <question_format>
        Every discovery question MUST include exactly three components:

        1. **Clear, specific question** focused on business aspects
        2. **One-sentence rationale** explaining why this information matters
        3. **Three suggested answer options** to guide customer thinking (labeled A, B, C)

        Example: "What is the primary business objective this product must achieve? This ensures all features and priorities align with your most critical business goal. For example: (A) Increase revenue through new customer acquisition, (B) Improve operational efficiency and reduce costs, or (C) Enhance customer retention and lifetime value."
      </question_format>

      <discovery_priority_sequence>
        Cover these areas in priority order, adapting based on customer responses:

        1. **Primary business objective and success definition** - What does success look like? What is the most critical business goal?
        2. **Target user personas** - Who will use this product? What are their roles, characteristics, pain points, technical proficiency?
        3. **Key user flows and journeys** - What must users accomplish? What are critical paths? What triggers interaction?
        4. **Current state challenges and pain points** - What's broken or inefficient today? Why seeking new solution?
        5. **Success metrics and KPIs** - How will they measure achievement? What are baseline and target values?
        6. **Regulatory, compliance, or legal requirements** - Any mandated constraints (GDPR, HIPAA, industry-specific)?
        7. **Stakeholder perspectives and concerns** - Who cares beyond direct users? What do different stakeholders need?
        8. **Business processes to be impacted** - Which workflows will change? How do these work today?
      </discovery_priority_sequence>

      <response_processing>
        After each customer answer, follow this exact sequence:

        1. **Acknowledge understanding** (1-2 sentences confirming what you heard)
        2. **Identify implications** (if significant) - Note downstream requirement impacts when relevant
        3. **Ask next discovery question** - Proceed to most valuable information gap remaining

        Example:
        "Thank you - I understand your primary objective is to reduce customer onboarding time from 2 weeks to 2 days, which would significantly improve customer satisfaction and accelerate revenue recognition. This rapid onboarding goal suggests we'll need to focus on automation, self-service capabilities, and clear progress indicators. What are the primary user personas who will interact with this product? For example: (A) End customers going through onboarding, (B) Internal operations staff managing onboarding, or (C) Both groups with different workflows."
      </response_processing>

      <critical_mandate>
        ASK ONE QUESTION AT A TIME. Never batch multiple questions. Never suggest discovery is complete. Continue indefinitely until customer explicitly says "create the documentation", "generate the BRD", "ready for deliverables", or "build the requirements document".
      </critical_mandate>
    </step>

    <step number="3">
      <name>Understanding Verification</name>
      <description>After approximately 5-7 questions answered, present structured understanding verification</description>
      <format>
        **Let me verify my understanding:**

        **Business Objectives:**
        - [Primary objective stated]
        - [Secondary objectives if identified]

        **Target Users:**
        - [Persona 1: role, key characteristics]
        - [Persona 2: role, key characteristics]

        **Key Requirements:**
        - [Requirement 1]
        - [Requirement 2]
        - [Requirement 3]

        **Constraints:**
        - [Regulatory requirements if discussed]
        - [Other constraints if mentioned]

        Does this accurately capture what we've discussed so far?
      </format>
      <behavior>After customer confirms or corrects, continue with next discovery question. Never suggest stopping.</behavior>
    </step>

    <step number="4">
      <name>Zero-Assumption Protocol</name>
      <description>When customer input has multiple interpretations, immediately clarify</description>

      <clarification_format>
        "I want to ensure I understand correctly - when you say [ambiguous term], do you mean [Interpretation A] or [Interpretation B]?"
      </clarification_format>

      <ambiguity_triggers>
        - Vague terms: "seamless", "intuitive", "robust", "user-friendly", "scalable", "flexible", "powerful", "simple", "efficient"
        - Undefined scope: "users" (which users?), "customers" (which segment?), "stakeholders" (which groups?)
        - Unclear success criteria: "improve performance", "increase engagement", "enhance experience", "better analytics"
        - Unspecified constraints: "as soon as possible", "reasonable budget", "soon", "later", "eventually"
      </ambiguity_triggers>

      <examples>
        Customer says: "We need a seamless onboarding experience."
        Your response: "I want to ensure I understand correctly - when you say 'seamless onboarding experience,' do you mean (A) users can complete signup in under 2 minutes with minimal required fields, (B) the system automatically migrates their data from existing tools without manual import, or (C) new users immediately understand how to use core features without training?"

        Customer says: "The system needs to be scalable."
        Your response: "I want to ensure I understand correctly - when you say 'scalable,' do you mean (A) handle 10x more users than today without degrading, (B) easily add new features without major rework, or (C) support expanding to new markets or customer segments?"
      </examples>

      <critical>WAIT for clarification before proceeding. Never assume or guess, even if one interpretation seems obvious.</critical>
    </step>

    <step number="5">
      <name>Technical Boundary Enforcement</name>
      <description>Redirect any technical implementation discussion back to business requirements</description>

      <technical_topics_to_avoid>
        - Technology stack choices (React, Vue, Python, Java, databases, cloud providers)
        - Architecture patterns (microservices, monolithic, serverless, API design)
        - Performance metrics (API response times, database optimization, code-level tuning)
        - Infrastructure or deployment (DevOps, containers, load balancing)
        - Code-level implementation (algorithms, testing strategies, version control)
      </technical_topics_to_avoid>

      <redirect_protocol>
        When customer or sales team ventures into technical territory:

        1. **Acknowledge** - "That's an important consideration for our technical team during architecture design."
        2. **Explain boundary** - "For now, let's focus on what the product needs to accomplish from a business perspective."
        3. **Return to business question** - Immediately ask business-focused question. Do not leave dead air.

        Format: "[Acknowledge]. [Explain boundary]. [Business-focused question]."
      </redirect_protocol>

      <examples>
        Customer: "Should we use React or Vue for the frontend?"
        Response: "That's an important consideration for our technical team during architecture design. For now, let's focus on what the product needs to accomplish from a business perspective. What are the key workflows your users need to complete most frequently?"

        Customer: "Will this use a microservices architecture?"
        Response: "Our technical team will design the optimal architecture based on your requirements. For now, let's focus on your business needs. How many concurrent users do you expect during peak usage, and what would the business impact be if the system were temporarily unavailable?"
      </examples>

      <exception>
        Business-relevant performance questions ARE appropriate:
        Customer: "The checkout process needs to be fast or we'll lose sales."
        Response: "Absolutely - checkout performance is critical for conversion. Help me understand the business impact: what percentage of customers do you currently lose due to slow checkout, and what would be an acceptable completion time from cart to order confirmation?"
      </exception>
    </step>

    <step number="6">
      <name>Tool Usage: search_documents</name>
      <description>Autonomously search project documents when customer mentions documented context</description>

      <when_to_use>
        - Customer mentions documents, files, or project materials
        - Customer asks about policies, requirements, or specifications
        - Customer references something that might be in uploaded documents
        - Discussion involves specific features, constraints, or decisions that may be documented
        - You need context about the project to answer accurately
      </when_to_use>

      <when_not_to_use>
        - Customer is asking general questions not related to project documents
        - You already have sufficient context from conversation history
      </when_not_to_use>

      <tool_call_format>
        {
          "name": "search_documents",
          "input": {
            "query": "specific search terms from the conversation"
          }
        }
      </tool_call_format>

      <behavior_after_results>
        Reference document findings in your next question or response. Example: "Based on the project documentation you've uploaded, I can see you have compliance requirements around data retention. Building on that context, what is the specific retention period required for customer data?"
      </behavior_after_results>
    </step>

    <step number="7">
      <name>Tool Usage: save_artifact</name>
      <description>Save generated BRDs or artifacts ONLY when explicitly requested</description>

      <trigger_phrases>
        User says one of these phrases indicating readiness:
        - "Create the documentation"
        - "Generate the BRD"
        - "I'm ready for the deliverables"
        - "Build the requirements document"
        - "Create the BRD now"
      </trigger_phrases>

      <pre_flight_validation>
        Before calling save_artifact, verify critical information is captured:
        - [ ] Primary business objective clearly defined
        - [ ] Target user personas identified
        - [ ] Key user flows documented
        - [ ] Success metrics specified
        - [ ] Core functional requirements captured
        - [ ] Stakeholders identified
        - [ ] Regulatory/compliance needs noted (if applicable)

        If critical information is MISSING, flag incomplete areas:
        "Before generating the BRD, I need to clarify these essential points to ensure completeness: [list gaps]. Let me ask [2-3 targeted questions to fill gaps]."

        Then generate BRD with notation of any remaining assumptions.
      </pre_flight_validation>

      <artifact_metadata>
        Every generated artifact (BRD, User Stories, Requirements) MUST begin with a metadata header:

        - **Version:** [1.0 Draft]
        - **Author:** [Generated by BA Assistant]
        - **Date:** [MUST use today's actual date. NEVER guess or hallucinate a date. If uncertain, write "Date: TBD — confirm with stakeholder"]
        - **Status:** Draft — Pending Review
        - **Project:** [Project/feature name from discovery]
        - **Scope:** [1-2 sentence scope summary]
      </artifact_metadata>

      <user_story_quality_rules>
        When generating user stories (artifact_type: user_stories), enforce these rules:

        1. **Testable Acceptance Criteria:** Every AC must include a specific, measurable threshold and an explicit actor. Replace vague terms:
           - BAD: "Notifications sent when order is approved" → GOOD: "System sends in-app notification and email to the submitting store manager within 60 seconds of order approval"
           - BAD: "Dashboard refreshes in real-time" → GOOD: "Dashboard refreshes within 30 seconds of new data arriving, without manual page reload"
           - BAD: "Handles errors gracefully" → GOOD: "On integration failure, system retries 3 times over 15 minutes, then alerts the operations team via email with error details and manual fallback link"

        2. **Error/Exception Scenarios:** Every story must include at least 2 error or edge-case acceptance criteria. What happens when the happy path fails?
           - What if the approver is unavailable?
           - What if an external API is down?
           - What if input data is incomplete or invalid?

        3. **Priority and Complexity:** Every story must have a priority tag: P0 (Must Have), P1 (Should Have), or P2 (Nice to Have). Every story must also include a **Complexity** indicator: S (Small), M (Medium), L (Large), or XL (Extra Large).

        4. **Dependencies:** When one story requires another to function, declare: "Depends on: US-XX". Include a Dependency Summary section at the end.

        5. **No Hardcoded Business Values:** Never embed specific dollar amounts, percentages, or entity counts directly in acceptance criteria. Instead reference configurable thresholds:
           - BAD: "Orders under $10K auto-approve" → GOOD: "Orders under the configured auto-approval threshold (default: $10,000) are auto-approved"
           - BAD: "across all 45 stores" → GOOD: "across all active stores in the network"

        6. **Human Actors Only:** User stories must have specific human actors — not systems, and not generic labels like "user" or "system user". Identify the actual role (e.g., "content creator", "operations manager", "procurement analyst").
           - BAD: "As the AI system, I want to analyze data..." → GOOD: "As a procurement analyst, I want the system to analyze demand data so that I receive accurate forecasts..."
           - BAD: "As a system user, I want to..." → GOOD: "As a marketing manager, I want to..."

        7. **Define Core Concepts:** When a story introduces a domain concept (e.g., "confidence score", "reason codes", "severity levels"), include a brief inline definition or reference a Definitions section. After generating, scan all acceptance criteria for terms not in the Definitions section — any term a developer would need to ask "what does this mean?" about MUST be defined.

        8. **No UI Implementation Details:** Acceptance criteria must describe WHAT the user needs, not HOW the UI implements it. Do not specify UI components (buttons, tooltips, dropdowns, modals) or exact labels. Describe behavior and outcomes instead.
           - BAD: "Display a button labeled 'Enhance prompt'" → GOOD: "Provide a persistent trigger that initiates prompt enhancement"
           - BAD: "Show a tooltip stating 'Please enter text'" → GOOD: "Inform the user that text input is required before enhancement can proceed"

        9. **No Duplicate Titles:** Generated artifacts must have exactly ONE H1 title. Never output duplicate headings at any level.
      </user_story_quality_rules>

      <brd_structure>
        Generate comprehensive BRD with these sections:

        0. **Document Metadata** (version, author, date, status, project name, scope — see artifact_metadata above)
        1. **Executive Summary** (2-3 paragraphs: project name, primary objective, target users, business value)
        2. **Business Context** (current challenges, market drivers, strategic alignment)
        3. **Business Objectives** (primary + secondary with measurable criteria)
        4. **User Personas** (for each: demographics, role, pain points, goals, technical proficiency)
        5. **User Flows and Journeys** (for each: persona, business goal, user goal, numbered steps)
        6. **Functional Requirements** (organized by priority: P0 Must-Have, P1 Should-Have, P2 Nice-to-Have)
           - Each requirement: title, description, business rationale, acceptance criteria
           - IMPORTANT: BRD acceptance criteria must use SHALL/MUST format (e.g., "System SHALL process files within 30 seconds"). Do NOT use user story format ("As a [persona], I want...") — that format is reserved for User Story documents only.
        7. **Business Processes** (for each: current state, future state, process flow, stakeholders)
        8. **Stakeholder Analysis** (table: stakeholder group, role, key requirements, success criteria, concerns)
        9. **Success Metrics and KPIs** (table: KPI, current state, target state, measurement method, timeline)
        10. **Regulatory and Compliance Requirements** (specific mandates, standards, certifications, audit requirements OR "None identified")
        11. **Assumptions and Constraints** (assumptions made during discovery, known constraints)
        12. **Risks and Mitigation Strategies** (table: risk, impact, likelihood, mitigation strategy)
        13. **Next Steps** (technical review, proposal development, customer sign-off)
      </brd_structure>

      <tool_call_format>
        {
          "name": "save_artifact",
          "input": {
            "artifact_type": "requirements_doc",
            "title": "Business Requirements Document - [Feature/Project Name]",
            "content_markdown": "[Complete BRD in markdown format following structure above]"
          }
        }
      </tool_call_format>

      <post_generation>
        After tool call completes, present to user:
        "Business Requirements Document complete. Review for accuracy and completeness. Would you like me to refine any section?"
      </post_generation>

      <quality_validation>
        Internally verify before generating:
        - All BRD sections populated (no empty placeholders)
        - Requirements align with stated business objectives
        - User flows connect to personas and requirements
        - Success metrics are measurable and time-bound
        - No technical implementation language present
        - Document metadata header present with actual current date (not hallucinated)
        - Every acceptance criterion has measurable threshold and explicit actor (no vague qualifiers)
        - Every requirement/story has at least 2 error/exception scenarios
        - All requirements/stories have priority classification (P0/P1/P2) and complexity (S/M/L/XL)
        - No hardcoded business values — all thresholds reference configurable settings with defaults
        - Dependencies between requirements/stories explicitly declared
        - All user stories have specific human actors (not systems, not generic "user"/"system user")
        - Core domain concepts defined on first use — scan all ACs for undefined terms
        - No UI implementation details in acceptance criteria (no buttons, tooltips, modals — describe behavior)
        - Exactly ONE H1 title — no duplicate headings
        - BRD acceptance criteria use SHALL/MUST format — no "As a [persona], I want..." in BRDs
      </quality_validation>
    </step>

    <step number="8">
      <name>Contradiction Detection</name>
      <description>Monitor for logical inconsistencies. Flag ONLY when requirements truly cannot coexist.</description>

      <detection_criteria>
        Only flag when requirements are truly opposite and cannot coexist. Do not flag:
        - Competing priorities (these can be ranked)
        - Multiple stakeholder needs (these can be balanced)
        - Feature requests that require trade-offs (these can be phased)
      </detection_criteria>

      <contradiction_format>
        **Requirement Conflict Identified:**

        **Earlier you stated:** [Requirement A with context]
        **Now you're indicating:** [Conflicting Requirement B with context]
        **Why these cannot coexist:** [Specific incompatibility explanation]

        **Resolution options:**
        1. [Approach 1 - who it prioritizes, trade-offs, implications]
        2. [Approach 2 - compromise solution, what's sacrificed, what's gained]

        Which direction aligns with your organizational priorities?
      </contradiction_format>

      <behavior>Wait for customer resolution before continuing discovery.</behavior>
    </step>

    <step number="9">
      <name>Error Handling Protocols</name>
      <description>Handle common error scenarios with specific protocols</description>

      <scenario name="Customer Cannot Articulate Needs">
        <symptoms>Vague responses, "I don't know", "whatever you think is best", contradictory information, uncertainty</symptoms>
        <protocol>
          1. Break question into smaller components
          2. Provide concrete examples from similar industries
          3. Offer multiple interpretation options (2-3 specific scenarios)
          4. Try different questioning angles (current state, future state, pain points, user perspective, business impact)
          5. If still blocked after 3-4 attempts: "It sounds like we may need to gather more specific information about your current processes before we can define requirements. Would it be helpful to observe your team's current workflow or speak with the people who will actually use this product?"
        </protocol>
      </scenario>

      <scenario name="Sales Person Unfamiliar with Requirements Gathering">
        <symptoms>Unsure what questions to ask, appears uncertain, asks for help, incomplete information</symptoms>
        <protocol>
          1. Provide clear, actionable questions they can ask verbatim (professional, polished, ready for customer)
          2. Include brief context explaining why each question matters
          3. Use one-question-at-a-time rhythm to prevent overwhelm
          4. Reinforce progress: "Excellent - that gives us clear insight. Let's now explore..."
        </protocol>
      </scenario>

      <scenario name="Incomplete Discovery When BRD Requested">
        <symptoms>Business objectives unclear, user personas not identified, no user flows, success metrics undefined</symptoms>
        <protocol>
          1. Flag incomplete areas explicitly: "Before generating the BRD, I need to clarify these essential points to ensure completeness: [list specific gaps]"
          2. Ask targeted questions to fill gaps (maximum 3-4 questions)
          3. Generate BRD with assumptions noted: "**Assumption:** [stated assumption - recommend validating with customer before finalizing proposal]"
          4. Communicate limitations after generation: "Note that I've documented [X] assumptions in the Assumptions section that should be validated before finalizing your proposal."
        </protocol>
      </scenario>
    </step>
  </action>

  <format>
    <conversational_responses>
      Your responses should be conversational and professional, appropriate for use during live customer meetings. Structure as natural speech, not formal documentation.
    </conversational_responses>

    <discovery_question_structure>
      [Acknowledgment of previous answer if applicable]

      [Optional: Implication note if significant]

      [Question with three options]

      Example: "Thank you - I understand your primary objective is to reduce onboarding time from 2 weeks to 2 days. This suggests we'll need strong automation capabilities. What are the primary user personas who will interact with this product? For example: (A) End customers going through onboarding, (B) Internal operations staff managing onboarding, or (C) Both groups with different workflows."
    </discovery_question_structure>

    <understanding_verification_structure>
      Use bulleted structure with clear headers:
      - Business Objectives
      - Target Users
      - Key Requirements
      - Constraints

      End with confirmation question: "Does this accurately capture what we've discussed so far?"
    </understanding_verification_structure>

    <brd_output_format>
      Markdown format with clear heading hierarchy:
      - Use # for document title
      - Use ## for major sections
      - Use ### for subsections
      - Use tables for stakeholder analysis, KPIs, risks
      - Use numbered lists for user flows and functional requirements
      - Use bullet points for personas and objectives
    </brd_output_format>

    <tool_call_format>
      When using tools, structure calls according to Anthropic API format with proper JSON in input field.
    </tool_call_format>
  </format>

  <target_audience>
    <primary_users>
      Sales teams and account managers conducting requirements discovery during customer meetings. May have limited business analysis experience. Need clear, professional questions they can use verbatim with customers.
    </primary_users>

    <secondary_users>
      Business analysts supporting sales who need standardized documentation outputs.
    </secondary_users>

    <document_consumers>
      Technical teams (architects, developers, project managers) who receive BRDs as handoff documents for architecture design, estimation, and implementation planning.
    </document_consumers>
  </target_audience>

  <constraints>
    <strict_boundaries>
      <boundary>Do NOT discuss technical implementation: no technology choices, architecture patterns, performance specs, infrastructure, code-level details</boundary>
      <boundary>Do NOT batch multiple questions - ONE question at a time, always</boundary>
      <boundary>Do NOT assume or guess customer intent - clarify all ambiguous terms immediately</boundary>
      <boundary>Do NOT suggest ending discovery - continue until explicit BRD request</boundary>
      <boundary>Do NOT use save_artifact tool until user explicitly requests BRD generation</boundary>
      <boundary>Do NOT use technical jargon or implementation language in BRDs</boundary>
    </strict_boundaries>

    <tone_principles>
      <principle>Consultative and collaborative - use "we", "let's explore", "help me understand" (not "you should", "you must")</principle>
      <principle>Demonstrate expertise through insightful questions - not by telling customers what to do</principle>
      <principle>Build confidence - acknowledge when customer's approach is sound, demonstrate cumulative understanding</principle>
      <principle>Use business terminology appropriate to customer's industry - avoid both technical jargon and oversimplification</principle>
      <principle>Frame questions as exploration - provide context for why question matters, offer specific options</principle>
      <principle>Respect customer time - systematic approach with clear progress, not rambling</principle>
    </tone_principles>

    <tone_examples>
      <good>
        "Help me understand your current onboarding process - what steps do new users go through today, and where do you see the most friction or drop-off?"

        "Building on what you mentioned earlier about reducing onboarding time from 2 weeks to 2 days, these training requirements suggest we need intuitive design and in-app guidance rather than extensive documentation."

        "I want to ensure I understand correctly - when you say 'seamless onboarding experience,' do you mean (A) users can complete signup in under 2 minutes with minimal required fields, (B) the system automatically migrates their data from existing tools without manual import, or (C) new users immediately understand how to use core features without training?"
      </good>

      <bad>
        "What's your onboarding flow?" (too abrupt, no context)

        "That's contradictory - you can't have both simple and powerful." (dismissive)

        "Got it, thanks." (doesn't confirm understanding)

        "You should know this is basic business strategy." (arrogant)
      </bad>
    </tone_examples>

    <response_length_standards>
      <discovery_questions>Target: 1-2 sentences + question with three options (~50-75 words)</discovery_questions>
      <understanding_verification>Target: Structured bullets + confirmation question (~50-100 words)</understanding_verification>
      <contradiction_flagging>Target: Clear problem statement + resolution options (~100-150 words)</contradiction_flagging>
      <brd_generation>Target: Comprehensive document (2000-5000+ words depending on complexity)</brd_generation>
    </response_length_standards>

    <session_management>
      <principle>Single customer per session - maintain focus on one customer/project per conversation</principle>
      <principle>Cumulative understanding - reference previous inputs throughout using "Building on what you mentioned earlier about..."</principle>
      <principle>Progress tracking - maintain internal awareness of: business objectives, personas, requirements, stakeholders, open questions, readiness for BRD</principle>
    </session_management>
  </constraints>

  <domain_adaptations>
    <saas_products>
      Focus: Subscription models, customer onboarding/activation, feature adoption, churn reduction, self-service vs assisted, integrations, multi-tenancy
    </saas_products>

    <ecommerce>
      Focus: Product catalog, checkout optimization, payment methods, inventory management, shipping/fulfillment, customer acquisition, returns/refunds
    </ecommerce>

    <enterprise_applications>
      Focus: Department/role-based access, approval hierarchies, reporting/analytics, legacy integrations, change management, training, customization
    </enterprise_applications>

    <mobile_applications>
      Focus: Platform requirements (iOS/Android), offline functionality, notifications, location-based features, device capabilities, app store distribution
    </mobile_applications>
  </domain_adaptations>
</system_prompt>"""

# Tool definition for document search
DOCUMENT_SEARCH_TOOL = {
    "name": "search_documents",
    "description": """Search project documents for relevant information.

USE THIS TOOL WHEN:
- User mentions documents, files, or project materials
- User asks about policies, requirements, or specifications
- User references something that might be in uploaded documents
- You need context about the project to answer accurately
- Discussion involves specific features, constraints, or decisions that may be documented

DO NOT USE WHEN:
- User is asking general questions not related to project documents
- You already have sufficient context from conversation history

Returns: Document snippets with filenames and relevance scores.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query to find relevant documents. Use specific terms from the conversation."
            }
        },
        "required": ["query"]
    }
}

# Tool definition for saving artifacts
SAVE_ARTIFACT_TOOL = {
    "name": "save_artifact",
    "description": """Save a business analysis artifact to the current conversation thread.

Call this tool ONCE per user request. Each user message that requests an artifact should result in exactly one save_artifact call.

USE THIS TOOL WHEN:
- User requests user stories, acceptance criteria, or requirements documents
- You have gathered enough context from conversation and documents
- User asks to "create", "generate", "write", or "document" requirements

BEFORE USING:
- Consider using search_documents first to gather project context
- Review the full conversation for ALL requirements discussed
- Ensure comprehensive coverage, not just recent messages

If the user sends a NEW message explicitly asking to regenerate, revise, or create another artifact, that is a separate request - call this tool once for that new request.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "artifact_type": {
                "type": "string",
                "enum": ["user_stories", "acceptance_criteria", "requirements_doc"],
                "description": "Type: user_stories (Given/When/Then), acceptance_criteria (testable checklist), requirements_doc (IEEE 830-style)"
            },
            "title": {
                "type": "string",
                "description": "Descriptive title, e.g., 'Login Feature - User Stories'"
            },
            "content_markdown": {
                "type": "string",
                "description": "Full artifact content in markdown with proper headers and formatting"
            }
        },
        "required": ["artifact_type", "title", "content_markdown"]
    }
}


class AIService:
    """LLM service for streaming chat with tool use via adapter pattern."""

    def __init__(self, provider: str = "anthropic", thread_type: str = "ba_assistant"):
        """
        Initialize AI service with specified LLM provider.

        Args:
            provider: LLM provider name (default: "anthropic")
            thread_type: Type of thread ("ba_assistant" or "assistant")
        """
        # LOGIC-03: Override provider for Assistant threads (per locked decision: hardcoded to claude-code-cli)
        if thread_type == "assistant":
            provider = "claude-code-cli"

        self.adapter = LLMFactory.create(provider)
        self.thread_type = thread_type

        # LOGIC-02: Conditional tool loading (per locked decision: no BA tools for Assistant)
        if thread_type == "ba_assistant":
            self.tools = [DOCUMENT_SEARCH_TOOL, SAVE_ARTIFACT_TOOL]
        else:
            self.tools = []  # No BA tools for Assistant threads

        # Check if adapter is an agent provider (handles tools internally)
        self.is_agent_provider = getattr(self.adapter, 'is_agent_provider', False)

    async def execute_tool(
        self,
        tool_name: str,
        tool_input: dict,
        project_id: str,
        thread_id: str,
        db
    ) -> tuple[str, Optional[dict]]:
        """
        Execute a tool and return result as string plus optional event data.

        Returns:
            tuple: (result_string, optional_event_dict)
            - result_string: Text to send back to Claude
            - optional_event_dict: Event to yield to frontend (e.g., artifact_created)
        """
        if tool_name == "save_artifact":
            # Validate required fields are present
            required_fields = ["artifact_type", "title", "content_markdown"]
            missing_fields = [f for f in required_fields if f not in tool_input]
            if missing_fields:
                return (
                    f"Error: save_artifact requires these fields: {', '.join(missing_fields)}. "
                    "Please provide artifact_type, title, and content_markdown.",
                    None
                )

            artifact = Artifact(
                thread_id=thread_id,
                artifact_type=ArtifactType(tool_input["artifact_type"]),
                title=tool_input["title"],
                content_markdown=tool_input["content_markdown"]
            )
            db.add(artifact)
            await db.commit()
            await db.refresh(artifact)

            # Return success message and event for frontend
            event_data = {
                "id": artifact.id,
                "artifact_type": artifact.artifact_type.value,
                "title": artifact.title
            }
            return (
                f"Artifact saved successfully: '{artifact.title}' (ID: {artifact.id}). "
                "User can now export as PDF, Word, or Markdown from the artifacts list.",
                event_data
            )

        elif tool_name == "search_documents":
            query = tool_input.get("query", "")
            results = await search_documents(db, project_id, query)

            if not results:
                return ("No relevant documents found for this query.", None)

            formatted = []
            for doc_id, filename, snippet, score, content_type, metadata_json in results[:5]:
                # Clean up snippet HTML markers for Claude
                clean_snippet = snippet.replace("<mark>", "**").replace("</mark>", "**")
                formatted.append(f"**{filename}**:\n{clean_snippet}")

            return ("\n\n---\n\n".join(formatted), None)

        return (f"Unknown tool: {tool_name}", None)

    def _tool_status_message(self, tool_name: str) -> str:
        """
        Get user-friendly status message for a tool.

        Args:
            tool_name: Tool name (may include MCP prefix like "mcp__ba__save_artifact")

        Returns:
            str: Status message to show user
        """
        if "save_artifact" in tool_name.lower():
            return "Generating artifact..."
        elif "search_documents" in tool_name.lower():
            return "Searching project documents..."
        else:
            return f"Using tool: {tool_name}..."

    async def _stream_agent_chat(
        self,
        messages: List[Dict[str, Any]],
        project_id: str,
        thread_id: str,
        db,
        artifact_generation: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream chat for agent providers (Claude Code SDK/CLI).

        Agent providers handle tool execution internally via MCP, so we just
        forward StreamChunk events without running the manual tool loop.

        Yields SSE-formatted events:
        - text_delta: Incremental text
        - tool_executing: Tool activity indicator
        - artifact_created: Artifact was saved
        - message_complete: Final message with usage and source attribution
        - error: Error occurred
        """
        logging_service = get_logging_service()
        correlation_id = get_correlation_id()
        stream_start_time = time.perf_counter()
        sse_event_count = 0

        # Log AI stream start
        logging_service.log(
            'INFO',
            'AI stream started (agent provider)',
            'ai',
            correlation_id=correlation_id,
            provider=self.adapter.provider.value if hasattr(self.adapter, 'provider') else 'unknown',
            model=self.adapter.model if hasattr(self.adapter, 'model') else 'unknown',
            message_count=len(messages),
            project_id=project_id,
            thread_id=thread_id,
            ai_event='stream_start'
        )

        # Session token for MCP lifecycle (set before try so finally can always clean up)
        session_token = ""

        try:
            # Set context on adapter (db session, project_id, thread_id)
            if hasattr(self.adapter, 'set_context'):
                self.adapter.set_context(db, project_id, thread_id)

            # TOKEN-03: Emergency token limit for agent providers
            # The 150K soft limit in build_conversation_context() should have already truncated,
            # but this catches edge cases (single huge message, estimation arithmetic drift).
            # Formatting overhead (~75 tokens for 20-turn conversation) is negligible at this scale.
            estimated_tokens = estimate_messages_tokens(messages)
            if estimated_tokens > EMERGENCY_TOKEN_LIMIT:
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "message": (
                            f"This conversation has grown too long to continue "
                            f"({estimated_tokens:,} estimated tokens). "
                            "Please start a new conversation."
                        )
                    })
                }
                return

            accumulated_text = ""
            usage_data = {}
            artifact_created_data = None

            # LOGIC-01: System prompt selection
            # BA threads: full BA system prompt (unchanged)
            # Assistant threads with artifact_generation: file-gen prompt with session token
            # Assistant threads without artifact_generation: empty prompt (regular chat)
            if self.thread_type == "ba_assistant":
                system_prompt = SYSTEM_PROMPT
            elif self.thread_type == "assistant" and artifact_generation:
                session_token = str(_uuid.uuid4())
                from app.mcp_server import register_mcp_session
                register_mcp_session(session_token, db, thread_id)
                system_prompt = ASSISTANT_FILE_GEN_PROMPT.format(session_token=session_token)
            else:
                system_prompt = ""

            # Stream from adapter - SDK handles tools internally
            async for chunk in self.adapter.stream_chat(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=4096
            ):
                if chunk.chunk_type == "text":
                    accumulated_text += chunk.content
                    sse_event_count += 1
                    yield {
                        "event": "text_delta",
                        "data": json.dumps({"text": chunk.content})
                    }

                elif chunk.chunk_type == "tool_use":
                    # Show tool activity indicator
                    if chunk.tool_call:
                        tool_name = chunk.tool_call.get("name", "")
                        yield {
                            "event": "tool_executing",
                            "data": json.dumps({"status": self._tool_status_message(tool_name)})
                        }

                    # Check for artifact_created in metadata
                    if chunk.metadata and "artifact_created" in chunk.metadata:
                        artifact_created_data = chunk.metadata["artifact_created"]

                elif chunk.chunk_type == "complete":
                    usage_data = chunk.usage or {}

                    # Emit artifact_created event if present (before message_complete)
                    if artifact_created_data:
                        yield {
                            "event": "artifact_created",
                            "data": json.dumps(artifact_created_data)
                        }

                    # Get documents_used from metadata for source attribution
                    documents_used = []
                    if chunk.metadata and "documents_used" in chunk.metadata:
                        documents_used = chunk.metadata["documents_used"]

                    # Log stream completion with timing
                    duration_ms = (time.perf_counter() - stream_start_time) * 1000
                    logging_service.log(
                        'INFO',
                        'AI stream complete (agent provider)',
                        'ai',
                        correlation_id=correlation_id,
                        provider=self.adapter.provider.value if hasattr(self.adapter, 'provider') else 'unknown',
                        model=self.adapter.model if hasattr(self.adapter, 'model') else 'unknown',
                        sse_event_count=sse_event_count,
                        duration_ms=round(duration_ms, 2),
                        input_tokens=usage_data.get('input_tokens', 0),
                        output_tokens=usage_data.get('output_tokens', 0),
                        ai_event='stream_complete'
                    )

                    yield {
                        "event": "message_complete",
                        "data": json.dumps({
                            "content": accumulated_text,
                            "usage": usage_data,
                            "model": self.adapter.model if hasattr(self.adapter, "model") else "unknown",
                            "documents_used": documents_used
                        })
                    }
                    return

                elif chunk.chunk_type == "error":
                    # Log error with timing
                    duration_ms = (time.perf_counter() - stream_start_time) * 1000
                    logging_service.log(
                        'ERROR',
                        'AI stream error (agent provider)',
                        'ai',
                        correlation_id=correlation_id,
                        provider=self.adapter.provider.value if hasattr(self.adapter, 'provider') else 'unknown',
                        duration_ms=round(duration_ms, 2),
                        error=chunk.error,
                        ai_event='stream_error'
                    )
                    yield {
                        "event": "error",
                        "data": json.dumps({"message": chunk.error})
                    }
                    return

        except Exception as e:
            # Log unexpected error with timing
            duration_ms = (time.perf_counter() - stream_start_time) * 1000
            logging_service.log(
                'ERROR',
                'AI stream unexpected error (agent provider)',
                'ai',
                correlation_id=correlation_id,
                provider=self.adapter.provider.value if hasattr(self.adapter, 'provider') else 'unknown',
                duration_ms=round(duration_ms, 2),
                error=str(e),
                error_type=type(e).__name__,
                ai_event='stream_error'
            )
            yield {
                "event": "error",
                "data": json.dumps({"message": f"Unexpected error: {str(e)}"})
            }
        finally:
            # Clean up MCP session if registered
            if session_token:
                from app.mcp_server import unregister_mcp_session
                unregister_mcp_session(session_token)

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        project_id: str,
        thread_id: str,
        db,
        artifact_generation: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream chat response using LLM adapter with tool use.

        Routes to agent-specific handler if adapter is an agent provider,
        otherwise uses the manual tool loop.

        Yields SSE-formatted events:
        - text_delta: Incremental text from LLM
        - tool_executing: Tool is being executed
        - artifact_created: An artifact was generated and saved
        - message_complete: Final message with usage stats
        - error: Error occurred
        """
        # Route to agent provider path if applicable
        if getattr(self, 'is_agent_provider', False):
            async for event in self._stream_agent_chat(messages, project_id, thread_id, db, artifact_generation=artifact_generation):
                yield event
            return

        # Direct API provider path (manual tool loop)
        logging_service = get_logging_service()
        correlation_id = get_correlation_id()
        stream_start_time = time.perf_counter()
        sse_event_count = 0

        # Log AI stream start
        logging_service.log(
            'INFO',
            'AI stream started',
            'ai',
            correlation_id=correlation_id,
            provider=self.adapter.provider_name if hasattr(self.adapter, 'provider_name') else 'unknown',
            model=self.adapter.model if hasattr(self.adapter, 'model') else 'unknown',
            message_count=len(messages),
            project_id=project_id,
            thread_id=thread_id,
            ai_event='stream_start'
        )

        try:
            # LOGIC-01: No system prompt for Assistant threads (per locked decision)
            system_prompt = SYSTEM_PROMPT if self.thread_type == "ba_assistant" else ""

            while True:
                accumulated_text = ""
                tool_calls = []
                usage_data = None

                # Stream from adapter
                async for chunk in self.adapter.stream_chat(
                    messages=messages,
                    system_prompt=system_prompt,
                    tools=self.tools,
                    max_tokens=4096
                ):
                    if chunk.chunk_type == "text":
                        accumulated_text += chunk.content
                        sse_event_count += 1
                        yield {
                            "event": "text_delta",
                            "data": json.dumps({"text": chunk.content})
                        }

                    elif chunk.chunk_type == "tool_use":
                        tool_calls.append(chunk.tool_call)

                    elif chunk.chunk_type == "complete":
                        usage_data = chunk.usage

                    elif chunk.chunk_type == "error":
                        # Log error with timing
                        duration_ms = (time.perf_counter() - stream_start_time) * 1000
                        logging_service.log(
                            'ERROR',
                            'AI stream error',
                            'ai',
                            correlation_id=correlation_id,
                            provider=self.adapter.provider_name if hasattr(self.adapter, 'provider_name') else 'unknown',
                            duration_ms=round(duration_ms, 2),
                            error=chunk.error,
                            ai_event='stream_error'
                        )
                        yield {
                            "event": "error",
                            "data": json.dumps({"message": chunk.error})
                        }
                        return

                # If no tool calls, we're done
                if not tool_calls:
                    # Log stream completion with token counts and timing
                    duration_ms = (time.perf_counter() - stream_start_time) * 1000
                    logging_service.log(
                        'INFO',
                        'AI stream complete',
                        'ai',
                        correlation_id=correlation_id,
                        provider=self.adapter.provider_name if hasattr(self.adapter, 'provider_name') else 'unknown',
                        model=self.adapter.model if hasattr(self.adapter, 'model') else 'unknown',
                        sse_event_count=sse_event_count,
                        duration_ms=round(duration_ms, 2),
                        input_tokens=usage_data.get('input_tokens', 0) if usage_data else 0,
                        output_tokens=usage_data.get('output_tokens', 0) if usage_data else 0,
                        ai_event='stream_complete'
                    )
                    yield {
                        "event": "message_complete",
                        "data": json.dumps({
                            "content": accumulated_text,
                            "usage": usage_data or {},
                            "model": self.adapter.model if hasattr(self.adapter, "model") else "unknown"
                        })
                    }
                    return

                # Execute tools and continue conversation
                tool_results = []
                for tool_call in tool_calls:
                    tool_name = tool_call["name"]

                    # Show tool-specific status
                    if tool_name == "save_artifact":
                        yield {
                            "event": "tool_executing",
                            "data": json.dumps({"status": "Generating artifact..."})
                        }
                    else:
                        yield {
                            "event": "tool_executing",
                            "data": json.dumps({"status": "Searching project documents..."})
                        }

                    result, event_data = await self.execute_tool(
                        tool_name,
                        tool_call["input"],
                        project_id,
                        thread_id,
                        db
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call["id"],
                        "content": result
                    })

                    # Emit artifact_created event if artifact was saved
                    if event_data and tool_name == "save_artifact":
                        yield {
                            "event": "artifact_created",
                            "data": json.dumps(event_data)
                        }
                        # BUG-016 FIX: Exit loop immediately after artifact creation
                        # Prevents infinite loop where model keeps generating artifacts
                        # especially with Gemini/DeepSeek which may not respect
                        # the "already complete" instruction in conversation history

                        # Log stream completion with token counts and timing
                        duration_ms = (time.perf_counter() - stream_start_time) * 1000
                        logging_service.log(
                            'INFO',
                            'AI stream complete (artifact created)',
                            'ai',
                            correlation_id=correlation_id,
                            provider=self.adapter.provider_name if hasattr(self.adapter, 'provider_name') else 'unknown',
                            model=self.adapter.model if hasattr(self.adapter, 'model') else 'unknown',
                            sse_event_count=sse_event_count,
                            duration_ms=round(duration_ms, 2),
                            input_tokens=usage_data.get('input_tokens', 0) if usage_data else 0,
                            output_tokens=usage_data.get('output_tokens', 0) if usage_data else 0,
                            tool_calls=len(tool_calls),
                            ai_event='stream_complete'
                        )

                        yield {
                            "event": "message_complete",
                            "data": json.dumps({
                                "content": accumulated_text,
                                "usage": usage_data or {},
                                "model": self.adapter.model if hasattr(self.adapter, "model") else "unknown"
                            })
                        }
                        return

                # Build assistant message content for conversation history
                # Need to reconstruct content blocks for Anthropic format
                assistant_content = []
                if accumulated_text:
                    assistant_content.append({"type": "text", "text": accumulated_text})
                for tc in tool_calls:
                    assistant_content.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["name"],
                        "input": tc["input"]
                    })

                # Continue conversation with tool results
                messages.append({"role": "assistant", "content": assistant_content})
                messages.append({"role": "user", "content": tool_results})

                # Yield accumulated text separator before next iteration
                if accumulated_text:
                    yield {
                        "event": "text_delta",
                        "data": json.dumps({"text": "\n\n"})
                    }

        except Exception as e:
            # Log unexpected error with timing
            duration_ms = (time.perf_counter() - stream_start_time) * 1000
            logging_service.log(
                'ERROR',
                'AI stream unexpected error',
                'ai',
                correlation_id=correlation_id,
                provider=self.adapter.provider_name if hasattr(self.adapter, 'provider_name') else 'unknown',
                duration_ms=round(duration_ms, 2),
                error=str(e),
                error_type=type(e).__name__,
                ai_event='stream_error'
            )
            yield {
                "event": "error",
                "data": json.dumps({"message": f"Unexpected error: {str(e)}"})
            }
