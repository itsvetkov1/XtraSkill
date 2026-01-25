# Discovery Framework

Complete guidance for systematic business requirements gathering through structured, one-question-at-a-time discovery.

## Discovery Priority Sequence

Cover these areas in priority order, adapting based on customer responses:

### 1. Primary Business Objective and Success Definition

**What to discover:**
- What does success look like for this product?
- What is the most critical business goal?
- How will they know if the product succeeded?

**Example questions:**
- "What is the primary business objective this product must achieve? This ensures all features and priorities align with your most critical business goal. For example: (A) Increase revenue through new customer acquisition, (B) Improve operational efficiency and reduce costs, or (C) Enhance customer retention and lifetime value."

### 2. Target User Personas

**What to discover:**
- Who will use this product?
- What are their roles, characteristics, and pain points?
- What is their technical proficiency level?

**Example questions:**
- "Who are the primary users of this product? Understanding user roles helps us design workflows that match their needs. For example: (A) End customers making purchases, (B) Internal staff managing operations, or (C) Business executives reviewing analytics."

### 3. Key User Flows and Journeys

**What to discover:**
- What must users accomplish with this product?
- What are the critical paths users will take?
- What triggers their interaction with the product?

**Example questions:**
- "What is the most critical action users need to complete in this product? This helps us prioritize which workflows must work flawlessly. For example: (A) Complete a purchase transaction, (B) Submit a request for approval, or (C) Generate and export a report."

### 4. Current State Challenges and Pain Points

**What to discover:**
- What's broken or inefficient today?
- Why are they seeking a new solution?
- What problems are costing them time or money?

**Example questions:**
- "What is the biggest challenge with your current approach that this product should solve? This ensures we address your most pressing pain point. For example: (A) Manual processes taking too much time, (B) Lack of visibility into key metrics, or (C) Customer frustration with current experience."

### 5. Success Metrics and KPIs

**What to discover:**
- How will they measure achievement?
- What are baseline values today?
- What are target values they want to reach?

**Example questions:**
- "What specific metric would best demonstrate this product's success? Having measurable goals ensures we can validate the solution works. For example: (A) Reduce processing time from X hours to Y hours, (B) Increase conversion rate from X% to Y%, or (C) Decrease customer support tickets by X%."

### 6. Regulatory, Compliance, or Legal Requirements

**What to discover:**
- Any mandated constraints (GDPR, HIPAA, industry-specific)?
- Certifications needed?
- Audit requirements?

**Example questions:**
- "Are there any regulatory or compliance requirements this product must meet? This ensures we account for mandated constraints from the start. For example: (A) GDPR data privacy requirements, (B) Healthcare HIPAA compliance, or (C) Financial industry regulations like SOC 2."

### 7. Stakeholder Perspectives and Concerns

**What to discover:**
- Who cares about this product beyond direct users?
- What do different stakeholders need?
- What are their concerns or worries?

**Example questions:**
- "Beyond direct users, who else has a stake in this product's success? Understanding all stakeholder perspectives ensures the solution meets everyone's needs. For example: (A) Executive leadership measuring ROI, (B) IT team managing security and infrastructure, or (C) Finance team controlling budget and costs."

### 8. Business Processes to be Impacted

**What to discover:**
- Which workflows will change?
- How do these processes work today?
- What inefficiencies exist in current processes?

**Example questions:**
- "What business process will this product change most significantly? Understanding process impact helps us design solutions that integrate smoothly. For example: (A) Order fulfillment and shipping, (B) Customer onboarding and activation, or (C) Financial reporting and reconciliation."

## Domain-Specific Adaptation

Adapt questioning approaches to each domain's unique characteristics.

### For SaaS Products

**Focus areas:**
- Subscription model and pricing tiers
- Customer onboarding and activation flows
- Feature adoption goals
- Churn reduction strategies
- Self-service vs assisted service balance
- Customer system integrations
- Multi-tenancy needs

**Example questions:**
- "What is the primary driver for customers to upgrade from a free to paid tier? Understanding monetization strategy helps align feature value with pricing. For example: (A) Advanced features like reporting or automation, (B) Usage limits like number of users or data storage, or (C) Service level like priority support or uptime guarantees."

### For E-commerce Solutions

**Focus areas:**
- Product catalog complexity
- Checkout flow optimization
- Payment method requirements
- Inventory management integration
- Shipping and fulfillment workflows
- Customer acquisition channels
- Return and refund processes

**Example questions:**
- "What is the most common reason customers abandon their cart before completing purchase? This helps us optimize the checkout experience. For example: (A) Unexpected shipping costs or fees, (B) Complicated checkout process requiring too many steps, or (C) Limited payment method options."

### For Enterprise Applications

**Focus areas:**
- Department/role-based access and workflows
- Approval hierarchies and governance
- Reporting and analytics requirements
- Legacy system integrations
- Change management and adoption strategy
- Training and support requirements
- Customization and configuration needs

**Example questions:**
- "How many levels of approval are typically required for [key business process]? Understanding approval hierarchies ensures we build appropriate governance. For example: (A) Single approver (direct manager), (B) Two-level approval (manager + department head), or (C) Multi-level approval (manager + department head + executive)."

### For Mobile Applications

**Focus areas:**
- Platform requirements (iOS, Android, both)
- Offline functionality needs
- Notification strategy and use cases
- Location-based features
- Device-specific capabilities (camera, sensors)
- App store distribution strategy

**Example questions:**
- "How critical is offline functionality for your users? This determines architecture approach for data sync. For example: (A) Must work fully offline with background sync, (B) Read-only access offline with online-only editing, or (C) Online-only with graceful error handling when disconnected."

## Response Processing Protocols

After each customer answer, follow this exact sequence:

### Step 1: Acknowledge Understanding

Confirm what you heard in 1-2 sentences.

**Example:**
"Thank you - I understand your primary objective is to reduce customer onboarding time from 2 weeks to 2 days, which would significantly improve customer satisfaction and accelerate revenue recognition."

### Step 2: Identify Implications (if significant)

Note downstream requirement impacts when relevant.

**Example:**
"This rapid onboarding goal suggests we'll need to focus on automation, self-service capabilities, and clear progress indicators so customers know exactly where they are in the process."

**When to include implications:**
- Customer answer creates clear downstream requirements
- Answer constrains or enables certain approaches
- Answer connects to previously discussed requirements

**When to skip implications:**
- Answer is straightforward with no significant downstream impact
- Would be stating the obvious
- Risk over-explaining or sounding condescending

### Step 3: Ask Next Discovery Question

Proceed to most valuable information gap remaining.

Use the Discovery Priority Sequence as a guide, but adapt based on:
- What customer has already revealed
- Natural conversation flow
- Areas needing clarification or depth

**Never suggest discovery is complete.** Continue indefinitely until customer explicitly requests BRD generation.

## Technical Boundary Enforcement

### Topics to Avoid (Technical Implementation Layer)

**Technology stack choices:**
- Programming languages (React, Vue, Python, Java)
- Databases (SQL, NoSQL, PostgreSQL, MongoDB)
- Cloud providers (AWS, Azure, Google Cloud)
- Frameworks and libraries

**Architecture patterns:**
- Microservices vs monolithic
- Serverless vs container-based
- Client-server architecture
- API design patterns

**Performance metrics (unless business-relevant):**
- API response times
- Database query optimization
- Code-level performance tuning
- Infrastructure scaling

**Infrastructure or deployment:**
- DevOps pipelines
- Container orchestration
- Server configuration
- Load balancing

**Code-level implementation:**
- Algorithms and data structures
- Code organization patterns
- Testing strategies
- Version control approaches

### Exception for Business-Relevant Performance

**Acceptable (business impact focus):**
- "Checkout must complete quickly to minimize cart abandonment"
- "Reports should generate fast enough for real-time decision making"
- "System must handle 1000 concurrent users during peak shopping season"

**Too technical (implementation focus):**
- "API response time under 200ms with p99 latency optimization"
- "Database queries optimized with proper indexing strategies"
- "Load balancer configured for horizontal scaling"

### Topics to Maintain (Business Requirements Layer)

**Business objectives and outcomes:**
- Revenue goals
- Cost reduction targets
- Customer satisfaction improvements
- Market share gains

**User needs and workflows:**
- What users need to accomplish
- How users currently work
- Pain points in existing processes
- User experience goals

**Success criteria and KPIs:**
- Measurable business metrics
- Target values and timelines
- Baseline current state
- How success will be validated

**Business process improvements:**
- Workflow efficiency gains
- Automation opportunities
- Process simplification
- Cross-team collaboration improvements

**Functional capabilities required:**
- What the product must do
- Features needed to achieve objectives
- Integration points with other business systems
- Data inputs and outputs

### Redirect Protocol

When customer or sales team ventures into technical territory:

**Redirect Format:**
"That's an important consideration for our technical team during architecture design. For now, let's focus on what the product needs to accomplish from a business perspective. [Return immediately to business-focused question]"

**Examples:**

Customer: "Should we use React or Vue for the frontend?"
Response: "That's an important consideration for our technical team during architecture design. For now, let's focus on what the product needs to accomplish from a business perspective. What are the key workflows your users need to complete most frequently?"

Customer: "Will this use a microservices architecture?"
Response: "Our technical team will design the optimal architecture based on your requirements. For now, let's focus on what the product needs to accomplish. How many concurrent users do you expect during peak usage, and what would the business impact be if the system were temporarily unavailable?"

## Zero-Assumption Protocol

### When to Apply

Apply immediate clarification when customer input has multiple interpretations:

**Vague terms:** "seamless," "intuitive," "robust," "user-friendly," "scalable," "flexible," "powerful," "simple," "efficient"

**Undefined scope:** "users" (which users?), "customers" (which segment?), "stakeholders" (which groups?), "system" (which system?)

**Unclear success criteria:** "improve performance," "increase engagement," "enhance experience," "better analytics," "more visibility"

**Unspecified constraints:** "as soon as possible," "reasonable budget," "soon," "later," "eventually"

### Clarification Format

**Template:**
"I want to ensure I understand correctly - when you say [ambiguous term], do you mean [Interpretation A] or [Interpretation B]?"

**Examples:**

Customer says: "We need a seamless onboarding experience."
Your response: "I want to ensure I understand correctly - when you say 'seamless onboarding experience,' do you mean (A) users can complete signup in under 2 minutes with minimal required fields, (B) the system automatically migrates their data from existing tools without manual import, or (C) new users immediately understand how to use core features without training?"

Customer says: "The system needs to be scalable."
Your response: "I want to ensure I understand correctly - when you say 'scalable,' do you mean (A) handle 10x more users than today without degrading, (B) easily add new features without major rework, or (C) support expanding to new markets or customer segments?"

Customer says: "We want to improve engagement."
Your response: "I want to ensure I understand correctly - when you say 'improve engagement,' do you mean (A) increase frequency of user logins from X per week to Y per week, (B) increase time spent in the product from X minutes to Y minutes per session, or (C) increase feature adoption from X% of users to Y% of users?"

### Disambiguation Guidelines

**Always offer 2-3 specific interpretations** rather than open-ended questions.

**Good (specific options):**
"When you say 'users,' do you mean (A) end customers making purchases, (B) internal staff managing operations, or (C) both groups with different workflows?"

**Bad (too open-ended):**
"When you say 'users,' who specifically do you mean?"
(Problem: Doesn't guide customer thinking, may get vague response)

**Ground interpretations in concrete examples:**
- Use measurable outcomes where possible
- Reference specific features or workflows
- Include timelines, numbers, or percentages when relevant

**Wait for clarification before proceeding.** Never assume or guess, even if one interpretation seems obvious.

## Cumulative Understanding

### Reference Previous Inputs

Throughout conversation, demonstrate comprehension by referencing earlier customer statements:

**Connection phrases:**
- "Building on what you mentioned earlier about..."
- "This connects to the [requirement] we discussed..."
- "Given your goal of [previous objective], this suggests..."
- "Earlier you indicated [previous statement], so..."

**Example:**
Customer mentions wanting to reduce onboarding time (question 5), then later discusses user training needs (question 15).

Your response: "Building on what you mentioned earlier about reducing onboarding time from 2 weeks to 2 days, these training requirements suggest we need intuitive design and in-app guidance rather than extensive documentation. Should the product include interactive tutorials or tooltips to accelerate learning?"

### Maintain Consistency

Track and ensure consistency across:
- Business objectives and stated requirements
- User personas and their needs
- Success metrics and feature priorities
- Stakeholder concerns and proposed solutions

Flag contradictions when they truly cannot coexist (see Contradiction Detection in SKILL.md).

### Progress Awareness

Maintain internal awareness of:

**Coverage completeness:**
- Which discovery priority areas have been covered
- Which areas need more depth
- Which areas haven't been addressed yet

**Information quality:**
- Specific, measurable information vs vague statements
- Concrete examples vs abstract concepts
- Detailed workflows vs high-level descriptions

**Readiness for BRD:**
- Are business objectives clear and measurable?
- Are user personas sufficiently detailed?
- Are functional requirements captured with rationale?
- Are success metrics defined with baselines and targets?
