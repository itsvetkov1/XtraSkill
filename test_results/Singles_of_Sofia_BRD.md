# Business Requirements Document
## Singles of Sofia Mobile Application

**Document Version:** 1.0 (In Progress)
**Date:** January 17, 2026
**Project:** Singles of Sofia Community Platform MVP
**Status:** Preliminary - Further Discovery Required

---

## Executive Summary

Singles of Sofia is developing a hybrid Flutter mobile application to transform their event-based matchmaking service into an ongoing community platform. The app will enable event participants to stay connected between events, receive updates and engaging content from organizers, and build meaningful one-on-one connections with people they met at Singles of Sofia events.

**Primary Business Objective:** Build a community platform that increases brand loyalty and reduces marketing costs for future events by keeping participants engaged, encouraging repeat attendance through organic community connections, and reducing reliance on external marketing channels.

---

## 1. Business Objectives

### 1.1 Primary Objective
Build a sustainable community platform that:
- Increases brand loyalty among Singles of Sofia participants
- Reduces marketing costs for future events through organic engagement and word-of-mouth
- Keeps participants engaged between events rather than treating them as one-time attendees

### 1.2 Secondary Objectives
- Enable post-event connections between participants who met at Singles of Sofia events
- Provide efficient content distribution channel for organizers to reach engaged participants
- Create safer, structured alternative to traditional dating apps by leveraging in-person event foundation
- Increase repeat event attendance through ongoing community engagement

### 1.3 Success Definition
**Note:** Success metrics and KPIs to be defined in continued discovery session.

---

## 2. User Personas

### 2.1 Persona 1: Event Participant

**Demographics:**
- Age range: 21-45 years old
- Diverse tech comfort levels (from basic smartphone users to tech-savvy professionals)
- Located in Sofia, Bulgaria (or willing to travel for events)

**Motivations:**
- Seeking structured, safer dating alternatives to traditional dating apps
- Value in-person connections and curated matchmaking over endless swiping
- Want to maintain connections with interesting people they met at events
- Interested in being part of a community of like-minded singles

**Behaviors:**
- Attend Singles of Sofia events (clubs/bars with equal male-female ratio)
- Complete compatibility questionnaires during events
- Meet multiple people during structured matchmaking activities
- Comfortable with social media-style content consumption

**Pain Points:**
- Losing touch with people they connected with after events end
- Limited ways to continue conversations with promising matches
- Missing updates about future events from Singles of Sofia
- Traditional dating apps feel unsafe, impersonal, or overwhelming

**Needs from App:**
- Simple, intuitive interface suitable for varying tech comfort levels
- Safe, permission-based way to reconnect with specific people from past events
- Regular engaging content that keeps Singles of Sofia top-of-mind
- Privacy controls and ability to decline/block unwanted connections
- Easily accessible information about upcoming events

### 2.2 Persona 2: Event Organizer/Administrator

**Role:**
- Singles of Sofia staff responsible for event management and participant engagement
- Content creators and community managers

**Responsibilities:**
- Promote upcoming Singles of Sofia events
- Maintain participant engagement between events
- Build and nurture community atmosphere
- Drive repeat attendance and brand loyalty

**Pain Points (Assumed - to be validated):**
- Time-consuming manual communication via email/social media
- Limited visibility into which participants are actively engaged
- Difficulty distributing content efficiently to past participants

**Needs from App:**
- Admin dashboard for publishing content quickly
- Ability to post multiple content types (event announcements, community content, tips, stories)
- Social media-style content management (posts, potentially reels/video)
- **Note:** Specific admin workflow needs to be explored in continued discovery

---

## 3. Functional Requirements

### 3.1 User-Facing Features

#### 3.1.1 Home Screen / Content Feed
**Description:** Social media-style feed where participants consume content published by organizers.

**Requirements:**
- Display posts in chronological or algorithmically-sorted feed format
- Support multiple content types:
  - Event announcements (upcoming events, registration, venue details)
  - Community content (success stories, dating tips, participant spotlights)
  - Sofia nightlife and lifestyle content
  - Potentially video content (reels) if feasible
- Content must be viewable by all active app users
- Feed should refresh to show new content
- Users can scroll through historical content

**Priority:** High (MVP Core Feature)

#### 3.1.2 Event Participant List
**Description:** View list of all participants from events the user has attended.

**Requirements:**
- Display all participants from each event user attended
- Show participant basic information (photo, name - specific fields to be determined)
- Organize by event or show combined list (to be determined)
- Allow user to initiate chat request with any listed participant
- Indicate connection status with each person:
  - Not requested
  - Request pending
  - Request accepted (chat available)
  - Request declined (appears as pending to requester)
  - Blocked

**Priority:** High (MVP Core Feature)

**Open Questions for Next Session:**
- How should participant list be organized (by event, chronological, alphabetical)?
- What participant information is visible before chat connection?

#### 3.1.3 Chat Request and Approval System
**Description:** Permission-based system for initiating private conversations with other participants.

**Requirements:**
- User can send chat request to any participant from their event list
- Recipient receives notification of chat request
- Recipient can:
  - Accept request (opens chat window between both users)
  - Decline request silently (requester sees "pending" status, no notification sent)
  - Decline and block user (prevents future requests from that person)
- Chat request shows "pending" status to requester until accepted or timeout occurs
- Timeout mechanism for pending requests (duration to be determined)
- No confrontational notifications - declined requests appear pending to protect user comfort

**Priority:** High (MVP Core Feature)

**Business Rationale:** Reinforces "safer and structured" positioning versus traditional dating apps by requiring mutual consent before any communication.

#### 3.1.4 Real-Time Chat Window
**Description:** One-on-one messaging between participants who have mutually accepted connection.

**Requirements:**
- Real-time text messaging between two users
- Chat accessible only after both parties approve connection
- Message history persistence (to be determined - session-based or permanent)
- **Note:** Specific chat features to be defined in continued discovery:
  - Photo/media sharing capability?
  - Read receipts?
  - Typing indicators?
  - Message editing/deletion?
  - Notification preferences?

**Priority:** High (MVP Core Feature)

#### 3.1.5 User Profile
**Description:** Participant profile with photo and personal information.

**Requirements:**
- User must upload at least one profile photo
- User can add personal information (specific fields to be determined in next session)
- **Open Questions for Next Session:**
  - Required vs. optional profile fields?
  - What information level: minimal (photo, name, age), moderate (+ bio, interests), or comprehensive?
  - Can users edit profile after creation?
  - Privacy controls for profile visibility?
  - Is profile visible to all app users or only people from same events?

**Priority:** High (MVP Core Feature)

**Status:** Requirements incomplete - needs continued discovery

#### 3.1.6 Blocking Functionality
**Description:** User safety feature to prevent unwanted contact.

**Requirements:**
- User can block another participant at any time
- Blocking prevents blocked user from:
  - Sending future chat requests
  - Seeing blocker in participant lists (to be determined)
  - Viewing blocker's profile (to be determined)
- Blocked user receives no notification they've been blocked
- User can view list of blocked users
- User can unblock previously blocked users (optional - to be determined)

**Priority:** High (MVP Core Feature)

**Open Questions for Next Session:**
- What specific actions does blocking prevent?
- Can users unblock someone later?
- How is blocked user's view affected (do they still see blocker in lists)?

### 3.2 Admin/Organizer Features

#### 3.2.1 Admin Dashboard
**Description:** Administrative interface for organizers to manage content and events.

**Requirements:**
- Secure login for authorized Singles of Sofia staff
- Content publishing interface for creating posts
- Ability to publish multiple content types:
  - Text posts with optional images
  - Event announcements with event details
  - Video content (reels) if technically feasible
- **Open Questions for Next Session:**
  - Content scheduling/publishing workflow?
  - Draft saving capability?
  - Content editing/deletion after publishing?
  - Analytics/engagement metrics visibility?
  - User management capabilities?
  - Event creation and management tools?
  - Participant data access and management?

**Priority:** High (MVP Core Feature)

**Status:** Requirements incomplete - significant admin workflow discovery needed

---

## 4. User Journeys

### 4.1 Journey 1: Participant Browses Content and Discovers Upcoming Event

**User Goal:** Stay engaged with Singles of Sofia community and learn about next event

**Steps:**
1. User opens Singles of Sofia app
2. Lands on home screen showing social media-style content feed
3. Scrolls through recent posts from organizers
4. Sees mix of community content (success story from recent event, dating tip)
5. Sees event announcement post for upcoming Friday event at [Venue Name]
6. Clicks on event announcement for more details
7. **[Action to be defined: How does user register/RSVP - external link, in-app registration, or just informational?]**
8. Feels connected to community and informed about opportunities

**Success Criteria:**
- User sees fresh, engaging content when opening app
- Event information is clear and actionable
- User feels part of ongoing community, not just event attendee

### 4.2 Journey 2: Participant Reconnects with Someone from Past Event

**User Goal:** Continue conversation with someone they connected with at a Singles of Sofia event

**Steps:**
1. User opens app and navigates to participant list section
2. Views list of all participants from events they've attended
3. Recognizes person they had good conversation with at last event
4. Reviews their profile information [specific fields to be determined]
5. Clicks "Request to Chat" button
6. Request shows "Pending" status
7. **Scenario A - Request Accepted:**
   - Other person accepts request
   - User receives notification
   - Chat window becomes available
   - User sends first message
   - Real-time conversation begins
8. **Scenario B - Request Declined:**
   - Other person declines request
   - User continues to see "Pending" status (no rejection notification)
   - After timeout period, request expires or remains pending indefinitely
   - User can focus on other connections without uncomfortable rejection

**Success Criteria:**
- User can easily find and identify people from past events
- Request process feels safe and low-pressure
- Rejection doesn't create uncomfortable confrontation
- Accepted connections lead to meaningful conversations

### 4.3 Journey 3: Organizer Publishes Event Announcement

**User Goal:** Inform community about upcoming Singles of Sofia event and drive registrations

**Steps:**
1. Organizer logs into admin dashboard
2. Navigates to content creation interface
3. Selects "Event Announcement" post type
4. Enters event details:
   - Event title/theme
   - Date and time
   - Venue name and location
   - Registration link or details
   - Event description/what to expect
   - Optional: featured image
5. **[To be defined: Preview post before publishing?]**
6. Clicks "Publish" button
7. Post immediately appears in all users' content feeds
8. **[To be defined: Receives confirmation or analytics?]**

**Success Criteria:**
- Quick, efficient publishing process
- Event details clearly communicated to all participants
- Reduces need for manual email/social media posting

**Status:** Journey incomplete - admin workflow details needed in continued discovery

### 4.4 Journey 4: Participant Blocks Unwanted Contact

**User Goal:** Protect themselves from persistent or uncomfortable chat requests

**Steps:**
1. User receives chat request from participant they're not interested in connecting with
2. User declines request (shows as pending to requester)
3. Same person sends another chat request later
4. User decides to block them
5. Navigates to chat request or user's profile
6. Selects "Block User" option
7. Confirms blocking action
8. Blocked user can no longer send requests or contact them
9. User feels safe and in control of their connections

**Success Criteria:**
- Blocking is easy to find and execute
- User feels protected from unwanted contact
- No confrontational notifications to blocked user

---

## 5. Non-Functional Requirements

### 5.1 Platform Requirements
- Hybrid Flutter application (iOS and Android support)
- **Note:** Specific platform versions, device support to be defined

### 5.2 User Experience Requirements
- **Critical:** Interface must be intuitive and simple enough for users with varying tech comfort levels (age range 21-45, diverse technical backgrounds)
- Design should feel familiar and easy to navigate for users who may not be tech-savvy
- Social media-style interaction patterns for content consumption (familiar UX)

### 5.3 Performance Requirements
**Note:** To be defined in continued discovery - real-time chat latency, feed loading times, etc.

### 5.4 Security & Privacy Requirements
- Permission-based connections (mutual consent required for chat)
- Silent decline functionality (no confrontational rejection notifications)
- User blocking capability
- **Note:** Data privacy, authentication, secure messaging requirements to be explored in continued discovery

### 5.5 Regulatory & Compliance Requirements
**Note:** To be explored in continued discovery:
- GDPR compliance (if applicable for EU users)
- Data protection regulations
- Age verification requirements
- Content moderation policies

---

## 6. Success Metrics and KPIs

**Status:** To be defined in continued discovery session

**Questions to Address:**
- How will you measure community engagement (DAU, MAU, session frequency)?
- What defines successful post-event reconnection (chat acceptance rate, message volume)?
- How will you track reduction in marketing costs?
- What indicates increased brand loyalty (repeat event attendance rate)?
- Content engagement metrics (views, interaction rates)?
- Event registration conversion from app announcements?

---

## 7. Stakeholder Analysis

### 7.1 Primary Stakeholders

**Singles of Sofia Event Participants**
- **Interest:** Meaningful connections, community belonging, event information, safe environment
- **Influence:** High - app success depends on their adoption and engagement
- **Requirements:** Intuitive UX, privacy/safety features, engaging content, valuable connections

**Singles of Sofia Organizers/Staff**
- **Interest:** Participant engagement, efficient communication, repeat attendance, brand growth
- **Influence:** High - content creators and app administrators
- **Requirements:** Efficient admin tools, content publishing capabilities, engagement visibility

### 7.2 Secondary Stakeholders
**Note:** To be identified in continued discovery - investors, sponsors, venue partners, etc.

---

## 8. Assumptions and Dependencies

### 8.1 Current Assumptions

1. **Event Registration Process:** Assuming event registration/ticketing happens externally (existing system) and app primarily informs about events rather than handling full registration workflow - **TO BE VALIDATED**

2. **Participant Data:** Assuming organizers have access to participant lists from past events (names, contact info) to populate participant lists in app - **TO BE VALIDATED**

3. **Content Moderation:** Assuming organizers will manually moderate published content, no automated content filtering required for MVP - **TO BE VALIDATED**

4. **Language:** Assuming app will be in English initially, Bulgarian language support to be addressed later - **TO BE VALIDATED**

5. **User Authentication:** Assuming participants create app accounts linked to event attendance, but authentication method not yet defined - **TO BE VALIDATED**

### 8.2 External Dependencies

1. **Event Data Integration:** Dependency on existing event management system to provide participant lists
2. **Real-Time Chat Infrastructure:** Requires real-time messaging backend/service
3. **Content Storage:** Requires media storage for photos, videos, user uploads
4. **Push Notifications:** Likely requires notification service for chat requests, new content alerts

**Note:** Technical implementation dependencies are outside scope of BRD but noted for awareness

---

## 9. Constraints

### 9.1 Known Constraints
- MVP scope - building foundational features first, advanced features later
- Hybrid Flutter platform requirement

### 9.2 Potential Constraints (To Be Validated)
- Budget constraints
- Timeline constraints
- Resource availability (development team, content creation capacity)
- Regulatory compliance requirements

**Note:** Constraint exploration needed in continued discovery

---

## 10. Out of Scope for MVP

**To be defined in continued discovery session**

**Potential candidates for future phases:**
- In-app event registration/ticketing
- Group chat or community forums
- Advanced matching algorithm integration
- Gamification features
- Premium/paid features
- User-generated content (participants posting content, not just consuming)

---

## 11. Open Questions for Continued Discovery

### High Priority - Critical for MVP Definition

1. **User Profile Requirements:**
   - What profile information is essential vs. optional (photo, name, age, bio, interests, preferences)?
   - Privacy level: minimal, moderate, or comprehensive profiles?
   - Can users edit profiles after creation?
   - Who can view profiles (everyone vs. only people from same events)?

2. **Success Metrics:**
   - How will you measure community engagement and loyalty?
   - What KPIs define MVP success?
   - How will marketing cost reduction be measured?

3. **Admin Dashboard Workflows:**
   - What content management capabilities do organizers need (scheduling, drafts, editing, deletion)?
   - What participant/user management tools are required?
   - Event creation and management in-app or external system?
   - Analytics and engagement reporting needs?

4. **Event Registration Flow:**
   - Does app handle event registration or just link to external system?
   - How do users RSVP or express interest in events?

5. **Authentication & Account Creation:**
   - How do participants create accounts (email, phone, social login)?
   - How are accounts linked to event attendance?
   - Password reset and account recovery process?

6. **Chat Functionality Details:**
   - Permanent message history or session-based?
   - Photo/media sharing in chat?
   - Read receipts, typing indicators?
   - Notification preferences?

### Medium Priority - Important for Complete Requirements

7. **Participant List Organization:**
   - How should participant lists be organized (by event, chronological, alphabetical, searchable)?
   - Can users search/filter participant lists?

8. **Blocking Details:**
   - What exactly does blocking prevent (requests, visibility, profile viewing)?
   - Can users unblock someone later?
   - How does blocked user's view change?

9. **Content Types:**
   - Video/reel support technically feasible and desired for MVP?
   - Other content formats needed (polls, links, galleries)?

10. **Regulatory Compliance:**
    - GDPR or data protection requirements?
    - Age verification needed?
    - Content moderation policies?

11. **Notifications:**
    - What events trigger push notifications (new content, chat requests, messages)?
    - User control over notification preferences?

12. **Language Support:**
    - English only or Bulgarian required for MVP?
    - Future multi-language plans?

---

## 12. Next Steps

### For Continued Discovery Session:

1. **Complete Profile Requirements** - Determine essential vs. optional profile fields and privacy level
2. **Define Success Metrics** - Establish measurable KPIs for MVP evaluation
3. **Detail Admin Workflows** - Explore organizer needs for content management, user management, event management
4. **Clarify Event Registration Integration** - Define how app connects to event ticketing/registration
5. **Specify Chat Features** - Determine message history, media sharing, notifications
6. **Address Compliance** - Identify regulatory requirements (GDPR, age verification, etc.)
7. **Finalize Out-of-Scope Items** - Clearly define what features are explicitly excluded from MVP

### After Discovery Completion:

- Validate all assumptions with stakeholders
- Prioritize feature backlog (MVP must-haves vs. nice-to-haves)
- Prepare BRD for technical team handoff
- Define project timeline and milestones (not in BRD scope)

---

## Document Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-17 | Business Analyst | Initial discovery - captured primary objectives, user personas, core feature requirements. Multiple areas require continued discovery (noted throughout document). |

---

**Document Status:** IN PROGRESS - Continued discovery session required to complete requirements definition

**Primary Contact:** [To be added]

**Review and Approval:** [To be added after completion]