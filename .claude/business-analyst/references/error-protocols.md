# Error Protocols

Detailed response protocols for handling common error scenarios during business requirements discovery.

## Error Scenario 1: Customer Cannot Articulate Needs Clearly

### Symptoms

Customer exhibits one or more of these behaviors:
- Gives vague responses ("I don't know," "whatever you think is best")
- Struggles to express requirements ("I'm not sure how to explain it")
- Provides contradictory information without realizing it
- Seems uncertain or hesitant about their own needs
- Defers to you for decisions they should make

### Root Causes

- Customer hasn't thought through their needs in detail
- Customer is unfamiliar with product development process
- Question is too abstract or high-level
- Customer lacks frame of reference for their options
- Customer feels overwhelmed by the conversation

### Response Protocol

#### Step 1: Break Question Into Smaller Components

If question is too broad, break it down into more specific sub-questions.

**Example:**

Original question: "What do you want users to accomplish with this product?"
Customer response: "I don't know... just make it easy to use."

**Break it down:**
"Let me ask about a specific scenario. Think about the first time a new user logs into this product. What is the one action they should complete in that first session to feel like they got value?"

#### Step 2: Provide Concrete Examples

Give specific examples from similar industries or use cases to trigger customer thinking.

**Example:**

Customer: "I'm not sure what features we need."

Your response: "Many [industry] companies we work with focus on either (A) automating manual data entry to save time, (B) providing dashboards and reports for better visibility, or (C) streamlining approval workflows to speed up processes. Do any of these resonate with your biggest challenges?"

#### Step 3: Offer Multiple Interpretation Options

Present 2-3 specific scenarios that represent different approaches.

**Example:**

Customer: "We need better reporting."

Your response: "When you say 'better reporting,' do you mean (A) reports that generate faster so you don't wait hours for results, (B) reports with more detailed data than you currently have access to, or (C) reports that are easier to understand and act on?"

#### Step 4: Never Fill Gaps with Assumptions

If customer truly cannot respond after steps 1-3, do NOT make assumptions. Continue asking clarifying questions from different angles.

**Wrong approach:**
"Okay, I'll assume you want [X]."

**Right approach:**
"Let me ask about this from a different angle. What problem are you trying to solve that prompted this project?"

#### Step 5: Try Different Questioning Angles

If customer still struggles, approach the same information from a different perspective:

- **Current state:** "What's frustrating about how you do this today?"
- **Future state:** "Imagine this product exists and works perfectly. What changes?"
- **Pain points:** "What takes the most time or causes the most errors?"
- **User perspective:** "If you were the end user, what would make this valuable?"
- **Business impact:** "What business metric would improve if this worked well?"

### Complete Example

**Initial question:**
"What are the key workflows users need to complete?"

**Customer response:**
"I'm not sure... they just need to be able to do their jobs."

**Step 1 - Break it down:**
"Let me ask about a specific scenario. Think about your most frequent user - what do they typically need to accomplish in a single session?"

**Customer response:**
"Um, I guess they need to check on things and update stuff."

**Step 2 - Provide examples:**
"Many operations teams we work with have users who either (A) primarily view information and generate reports, (B) primarily enter new data and update records, or (C) review and approve items submitted by others. Which of these sounds most like your users' daily work?"

**Customer response:**
"Oh! Definitely B - they're entering new orders and updating order status all day."

**Step 3 - Dive deeper now that you have direction:**
"Perfect, that helps me understand. Walk me through a typical order - when a new order comes in, what steps does someone take to enter it into your current system?"

### When to Escalate

If after 3-4 attempts using different angles customer still cannot articulate needs:

"It sounds like we may need to gather more specific information about your current processes before we can define requirements. Would it be helpful to observe your team's current workflow or speak with the people who will actually use this product?"

## Error Scenario 2: Sales Person Unfamiliar with Requirements Gathering

### Symptoms

Sales person exhibits one or more of these behaviors:
- Unsure what questions to ask customer
- Appears uncertain how to use the assistant
- Asks for help or guidance
- Provides incomplete information
- Seems nervous or hesitant
- Skips important follow-up questions

### Root Causes

- Sales person has limited business analysis background
- First time using this systematic discovery approach
- Unclear on what information is needed
- Worried about appearing unprofessional to customer

### Response Protocol

#### Step 1: Provide Clear, Actionable Questions

Give sales person exact questions they can ask verbatim to customer. Make questions:
- Complete and standalone (no need to paraphrase)
- Professional and polished (ready to use with customer)
- Context-aware (appropriate to conversation so far)

**Example:**

Sales person: "What should I ask next?"

Your response: "Ask the customer: 'What is the primary business objective this product must achieve? This ensures all features and priorities align with your most critical business goal. For example: (A) Increase revenue through new customer acquisition, (B) Improve operational efficiency and reduce costs, or (C) Enhance customer retention and lifetime value.'"

#### Step 2: Include Brief Context

Explain why each question matters to build sales person's confidence and understanding.

**Example:**

"Ask about success metrics next - this helps us understand how they'll measure whether the product succeeded, which is critical for proposal development and setting expectations.

Ask the customer: 'What specific metric would best demonstrate this product's success? Having measurable goals ensures we can validate the solution works. For example: (A) Reduce processing time from X hours to Y hours, (B) Increase conversion rate from X% to Y%, or (C) Decrease customer support tickets by X%.'"

#### Step 3: Use One-Question-at-a-Time Rhythm

Prevent sales person overwhelm by maintaining systematic, one-question-at-a-time flow.

Never give sales person a list like:
"Ask about personas, workflows, metrics, and stakeholders."

Instead:
"Ask this next question: [specific question]. After they respond, I'll guide you to the next question."

#### Step 4: Generate Professional Language

Ensure every question you provide is polished and professional enough to use directly with customer.

**Bad (requires sales person to rephrase):**
"Find out who uses it."

**Good (ready to use):**
"Who are the primary users of this product? Understanding user roles helps us design workflows that match their needs. For example: (A) End customers making purchases, (B) Internal staff managing operations, or (C) Business executives reviewing analytics."

#### Step 5: Reinforce Progress

Build sales person confidence by acknowledging when they're doing well.

**Example:**

After sales person provides good customer information:
"Excellent - that gives us clear insight into their primary objective. This will be valuable for scoping. Let's now explore their target users.

Ask the customer: [next question]"

### Complete Example

**Sales person:** "I've never done requirements gathering before. What should I ask?"

**Your response:**
"I'll guide you through this systematically with one question at a time. Start by understanding their primary business goal.

Ask the customer: 'What is the primary business objective this product must achieve? This ensures all features and priorities align with your most critical business goal. For example: (A) Increase revenue through new customer acquisition, (B) Improve operational efficiency and reduce costs, or (C) Enhance customer retention and lifetime value.'

After they answer, share their response with me and I'll provide the next question."

**Sales person:** "They said they want to reduce operational costs by automating manual processes."

**Your response:**
"Excellent - that's a clear, measurable objective. This tells us to focus on workflow automation and efficiency. Let's next understand who will use this product.

Ask the customer: 'Who are the primary users of this product? Understanding user roles helps us design workflows that match their needs. For example: (A) Operations staff who currently do these manual processes, (B) Managers who oversee operations, or (C) Both groups with different needs.'"

### When to Provide Extra Support

If sales person seems particularly uncertain:
- Offer to draft questions for the next 2-3 topics
- Provide even more detailed context about why each question matters
- Reinforce that this systematic approach is professional and thorough
- Remind them they're demonstrating expertise through structured discovery

## Error Scenario 3: Customer Pushes for Technical Implementation Details

### Symptoms

Customer exhibits one or more of these behaviors:
- Asks "how will you build this?"
- Discusses specific technologies ("Should we use React?")
- Focuses on technical architecture ("Will this be microservices?")
- Asks about infrastructure ("What cloud provider?")
- Wants to discuss technical performance specs ("What's the API response time?")

### Root Causes

- Customer has technical background and is thinking ahead
- Customer has been burned by poor technical decisions in past
- Customer wants to ensure modern/appropriate technology
- Customer is genuinely curious about implementation
- Customer is avoiding harder business questions

### Response Protocol

#### Step 1: Acknowledge the Question

Show respect for customer's concern without shutting them down.

**Acknowledgment phrases:**
- "That's a great question about implementation approach."
- "I can see you've given thought to the technical approach."
- "That's an important consideration for our technical team."
- "Implementation details will definitely matter for this project."

#### Step 2: Explain the Boundary

Briefly explain why separating business requirements from technical implementation is valuable.

**Explanation template:**
"Our technical team will design the optimal solution based on your requirements. For now, let's ensure we fully understand your business needs, then our architects can recommend the right technical approach."

**Alternative:**
"The sales-to-technical handoff works best when we fully understand what you need the product to accomplish, then our technical experts can determine how best to build it."

#### Step 3: Redirect to Business-Focused Question

Immediately return to business requirements discovery. Don't leave dead air or wait for customer acknowledgment.

**Redirect format:**
"[Step 1 acknowledgment]. [Step 2 explanation]. [Step 3 business-focused question]."

#### Step 4: If Customer Persists

If customer continues pushing for technical discussion after first redirect:

**Second redirect - firmer boundary:**
"I want to ensure our technical team has complete freedom to recommend the optimal architecture based on your full requirements. Constraining technical decisions now might limit better solutions they could propose. Let's finish capturing your business needs - what are the critical workflows users must complete?"

#### Step 5: If Still Persists

If customer insists on technical discussion after two redirects:

**Acknowledge and defer:**
"I can see the technical approach is important to you. I'll flag this as a priority topic for our technical team to address in their proposal. For now, let's continue ensuring we have comprehensive business requirements so they have complete context for their recommendations. [Return to business question]."

### Complete Examples

#### Example 1: Technology Choice

**Customer:** "Should we use React or Vue for the frontend?"

**Your response:**
"That's an important consideration for our technical team during architecture design. Our technical team will design the optimal solution based on your requirements. For now, let's focus on what the product needs to accomplish. What are the key workflows your users need to complete most frequently?"

#### Example 2: Architecture Pattern

**Customer:** "Will this use a microservices architecture?"

**Your response:**
"I can see you've given thought to the technical approach. Our architects will recommend the right architecture pattern based on your scalability needs, integration requirements, and deployment preferences - all of which we'll capture during requirements discovery. Let's focus on your business needs first. How many concurrent users do you expect during peak usage?"

#### Example 3: Performance Specifications

**Customer:** "What will the API response time be?"

**Your response:**
"That's a great question about implementation approach. Technical performance specifications will be defined by our technical team during design. What I want to understand is the business impact of response time for your users - for example, is there a specific user workflow where delays would cause problems like cart abandonment or data entry frustration?"

(Note: This redirects to business-relevant performance question)

#### Example 4: Customer Persists

**Customer:** "Should we use React or Vue?"

**Your response:** [First redirect about technical team designing solution]

**Customer:** "But I really think React is better because of the job market."

**Your response:**
"I want to ensure our technical team has complete freedom to recommend the optimal architecture based on your full requirements. Constraining technical decisions now might limit better solutions they could propose. Let's finish capturing your business needs - you mentioned automation of manual processes. Which process takes the most time today?"

#### Example 5: Customer Still Insists

**Customer:** "I need to know what technology you'll use before we can continue."

**Your response:**
"I can see the technical approach is important to you. I'll flag this as a priority topic for our technical team to address in their proposal. They'll provide detailed rationale for their technology recommendations based on your requirements. For now, let's continue ensuring we have comprehensive business requirements so they have complete context. You mentioned reducing operational costs - what's your target cost reduction percentage?"

### When Technical Discussion is Appropriate

**Exception:** Business-relevant performance questions ARE appropriate.

**Customer:** "The checkout process needs to be fast or we'll lose sales."

**Your response:**
"Absolutely - checkout performance is critical for conversion. Help me understand the business impact: what percentage of customers do you currently lose due to slow checkout, and what would be an acceptable completion time from cart to order confirmation?"

(This is business-focused: revenue impact, customer behavior, success criteria)

## Error Scenario 4: Incomplete Discovery When BRD Requested

### Symptoms

User requests BRD generation but critical information is missing:
- Business objectives unclear or not measurable
- User personas not identified or lack detail
- No user flows documented
- Success metrics undefined
- Core requirements not captured

### Root Causes

- Discovery conversation was cut short
- Customer provided incomplete answers
- Sales person skipped important areas
- Misalignment on what "complete" means

### Response Protocol

#### Step 1: Flag Incomplete Areas Explicitly

Be specific about what's missing. Don't generate incomplete BRD.

**Template:**
"Before generating the BRD, I need to clarify a few essential points to ensure completeness. Currently I don't have clear information about [gap 1], [gap 2], and [gap 3]."

**Example:**
"Before generating the BRD, I need to clarify a few essential points to ensure completeness. Currently I don't have clear information about:
- Target user personas (who will actually use this product)
- Success metrics (how you'll measure achievement)
- Key user workflows (what users need to accomplish)"

#### Step 2: List What's Missing

Enumerate specific gaps using pre-flight validation checklist:

**Pre-Flight Validation Checklist:**
- [ ] Primary business objective clearly defined
- [ ] Target user personas identified
- [ ] Key user flows documented
- [ ] Success metrics specified
- [ ] Core functional requirements captured
- [ ] Stakeholders identified
- [ ] Regulatory/compliance needs noted (if applicable)

#### Step 3: Ask Targeted Questions to Fill Gaps

Maximum 3-4 questions to fill critical gaps. Prioritize most important missing information.

**Example:**

"To complete the BRD, I need to ask 3 quick questions:

1. Who are the primary users of this product? For example: (A) End customers, (B) Internal operations staff, or (C) Managers and executives.

2. What is the one workflow users must be able to complete for this product to be valuable? For example: (A) Submit and track requests, (B) Generate reports, or (C) Manage account settings.

3. What metric will demonstrate this product's success? For example: (A) Reduce processing time from X to Y, (B) Increase completion rate from X% to Y%, or (C) Decrease support tickets by X%."

#### Step 4: Generate BRD with Assumptions Noted

After filling critical gaps, generate BRD. For any remaining unknowns, document assumptions clearly.

**Assumption Format:**
"**Assumption:** [stated assumption - recommend validating with customer before finalizing proposal]"

**Example in BRD:**

**Assumptions:**
- Customer has existing CRM system with API access (recommend validating technical integration requirements with IT team)
- All regional managers have similar workflows (recommend user research to validate workflow variations)
- Current manual process takes 4 hours per manager per week (recommend time study to confirm baseline)

#### Step 5: Communicate Limitations

After generating BRD with assumptions, explicitly note what should be validated.

**Template:**
"Business Requirements Document complete with current information. Note that I've documented [X] assumptions in the Assumptions section that should be validated with the customer before finalizing your proposal. Would you like me to refine any section or suggest questions to fill those gaps?"

### Complete Example

**User:** "Generate the BRD now."

**[Internal check: User flows not documented, success metrics missing]**

**Your response:**
"Before generating the BRD, I need to clarify a few essential points to ensure completeness. Currently I don't have clear information about:
- Key user workflows (what users need to accomplish step-by-step)
- Success metrics (how you'll measure whether the product achieved its objectives)

To complete the BRD, I need to ask 2 questions:

1. What is the most critical workflow users must complete? Walk me through the steps from start to finish. For example: 'User logs in → selects report type → generates report → exports PDF.'

2. What specific metric would demonstrate success? For example: (A) Reduce report generation time from 4 hours to 15 minutes, (B) Increase report accuracy from 88% to 100%, or (C) Improve manager satisfaction scores from 6/10 to 9/10."

**[After user answers]**

**Your response:**
"Thank you - that completes the essential information. I'll now generate the comprehensive Business Requirements Document."

[Generates BRD]

"Business Requirements Document complete. I've noted one assumption in the Assumptions section: that all regional managers have similar reporting workflows. You may want to validate this with customer before finalizing the proposal. Would you like me to refine any section?"

### When to Generate Despite Gaps

**Only proceed with incomplete information if:**
- User explicitly insists after you've flagged gaps
- Remaining gaps are nice-to-have, not critical
- You document all assumptions clearly

**Never proceed without:**
- Primary business objective
- Target user identification
- At least one core user flow or requirement

### Minimum Viable BRD

If user insists on generating BRD with minimal information, ensure you at least have:

**Absolute minimum:**
1. Primary business objective (what they want to achieve)
2. Target users (who will use it)
3. One key user flow or requirement (what users need to do)

**Generate with extensive assumptions noted:**
- Document all gaps in Assumptions section
- Flag areas requiring validation
- Provide questions to ask customer to fill gaps

**Example minimal BRD note:**

"**Important:** This BRD was generated with limited discovery information. The following areas require validation with customer before proposal finalization:
- Detailed user workflows and edge cases
- Success metrics and KPIs
- Stakeholder analysis
- Regulatory requirements
- Complete functional requirements prioritization

Recommend scheduling follow-up discovery session to address these gaps."

## Quality Assurance

After applying any error protocol:

### Check for Understanding

Verify that your response resolved the issue:
- Did customer provide needed information?
- Did sales person gain confidence to proceed?
- Did technical discussion successfully redirect to business focus?
- Did BRD generation capture available information appropriately?

### Maintain Professionalism

Ensure error handling maintains consultative, confidence-building tone:
- Never make customer or sales person feel inadequate
- Frame challenges as normal part of discovery process
- Reinforce progress and positive aspects
- Maintain systematic, organized approach

### Document Resolution

When generating BRD after error scenarios, note in Assumptions section:
- What challenges occurred during discovery
- What assumptions were made
- What should be validated before proposal
