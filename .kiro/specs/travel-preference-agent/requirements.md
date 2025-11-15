# Requirements Document

## Introduction

This feature implements an intelligent travel preference discovery system using Google Cloud's Agent Development Kit (ADK). The system uses a LoopAgent architecture to iteratively gather user travel preferences through A/B questions, generate personalized travel recommendations, and refine results based on user feedback. The agent orchestrates a conversation flow that starts with generic preference questions, builds a user profile, and ultimately produces concrete destination and experience recommendations.

## Requirements

### Requirement 1: Main Loop Agent Orchestration

**User Story:** As a travel planning system, I want to orchestrate a continuous preference discovery loop, so that I can iteratively gather preferences until sufficient data exists to make travel recommendations.

#### Acceptance Criteria

1. WHEN the system starts THEN the MainLoopAgent SHALL initialize and begin executing its sub-agent sequence
2. WHEN a loop iteration completes THEN the MainLoopAgent SHALL evaluate whether to continue or terminate based on the ExperiencePlanningAgent's judgment
3. IF the ExperiencePlanningAgent determines insufficient travel preferences exist THEN the MainLoopAgent SHALL initiate another loop iteration
4. IF the ExperiencePlanningAgent determines sufficient preferences exist and escalates THEN the MainLoopAgent SHALL terminate the loop
5. WHEN executing sub-agents THEN the MainLoopAgent SHALL maintain state across iterations including accumulated Q&A history and user profile

### Requirement 2: Question Generator Agent - Part 1 (Basic Categories)

**User Story:** As a user, I want to answer broad A/B preference questions covering fundamental travel categories, so that the system can understand my basic travel interests.

#### Acceptance Criteria

1. WHEN the QuestionGeneratorAgent starts Part 1 THEN it SHALL present exactly 3 questions covering the 6 basic travel categories (wellness and relaxation, shopping, culture and history, food exploration, nightlife and entertainment, nature and outdoor adventures)
2. WHEN presenting a question THEN the agent SHALL format it as an A/B choice without mentioning specific locations or offers
3. WHEN the user responds THEN the agent SHALL accept one of the following answer types: "A", "B", "all good", or "all bad"
4. WHEN the user responds THEN the agent SHALL capture the hesitation time for the response
5. WHEN all 3 basic questions are answered THEN the agent SHALL proceed to Part 2
6. WHEN communicating with the FastAPI frontend THEN the agent SHALL present only one question at a time per API interaction

### Requirement 3: Question Generator Agent - Part 2 (Customized Discovery)

**User Story:** As a user, I want to answer customized follow-up questions based on my initial responses, so that the system can deeply understand my specific travel preferences.

#### Acceptance Criteria

1. WHEN Part 2 begins THEN the QuestionGeneratorAgent SHALL analyze Part 1 responses to identify areas of confusion and strong interest
2. IF an area shows user confusion THEN the agent SHALL generate scenario-based questions to clarify understanding
3. IF an area shows strong user interest THEN the agent SHALL generate specific questions to deepen understanding
4. WHEN generating customized questions THEN the agent SHALL use a ReAct agent approach to dynamically determine the next question
5. WHEN sufficient preference data is gathered THEN the agent SHALL generate a user travel profile as a coherent paragraph
6. WHEN the user profile is complete THEN the agent SHALL update the state with accumulated Q&A history and the profile
7. WHEN communicating with the FastAPI frontend THEN the agent SHALL present only one question at a time per API interaction

### Requirement 4: Experience Planning Agent Integration Point

**User Story:** As a system architect, I want to define the interface and behavior for the ExperiencePlanningAgent, so that it can be implemented to generate concrete travel recommendations.

#### Acceptance Criteria

1. WHEN the QuestionGeneratorAgent completes THEN the system SHALL pass the accumulated user preferences to the ExperiencePlanningAgent
2. WHEN the ExperiencePlanningAgent executes THEN it SHALL evaluate whether sufficient travel preferences have been gathered to make informed recommendations
3. IF sufficient preferences exist THEN the agent SHALL use retrieval tools to find 3 distinct travel destinations
4. WHEN destinations are identified THEN the agent SHALL find 4 unique experience offers per destination that align with user preferences
5. WHEN recommendations are generated THEN the agent SHALL update the state with destination-experience matching results
6. IF sufficient preferences exist to make recommendations THEN the agent SHALL yield an Event with escalate=True to terminate the parent LoopAgent
7. IF insufficient preferences exist THEN the agent SHALL yield an Event without escalation to continue the loop and gather more preference data
8. WHEN presenting results THEN the agent SHALL clearly format the 3 destinations with their 4 associated experiences

### Requirement 5: State Management and Data Flow

**User Story:** As a system, I want to maintain consistent state across loop iterations, so that each iteration can build upon previous user interactions.

#### Acceptance Criteria

1. WHEN a loop iteration begins THEN the system SHALL provide access to all previously accumulated Q&A history
2. WHEN the QuestionGeneratorAgent completes THEN it SHALL update the state with new Q&A pairs and the current user profile
3. WHEN the ExperiencePlanningAgent completes THEN it SHALL update the state with destination-experience matching results
4. WHEN state is updated THEN all subsequent agents in the loop SHALL have access to the updated state
5. WHEN the loop terminates THEN the final state SHALL contain the complete Q&A history, user profile, and final recommendations

### Requirement 6: Google Cloud ADK Integration

**User Story:** As a developer, I want the agent system to be built using Google Cloud ADK components, so that it can be deployed and scaled on Google Cloud Platform.

#### Acceptance Criteria

1. WHEN implementing the MainLoopAgent THEN it SHALL use the ADK LoopAgent class
2. WHEN implementing the QuestionGeneratorAgent THEN it SHALL use the ADK LlmAgent class
3. WHEN implementing the ExperiencePlanningAgent interface THEN it SHALL use the ADK LlmAgent class
4. WHEN agents need to communicate state THEN they SHALL use ADK's state management mechanisms
5. WHEN the loop needs to terminate THEN agents SHALL use Event(actions=EventActions(escalate=True))
6. WHEN the loop needs to continue THEN agents SHALL use Event() without escalation
7. WHEN deploying the system THEN it SHALL be compatible with Google Cloud deployment infrastructure

### Requirement 7: FastAPI Frontend Integration

**User Story:** As a frontend application, I want to interact with the agent system through a FastAPI interface, so that I can present questions to users and collect responses.

#### Acceptance Criteria

1. WHEN the frontend requests a question THEN the API SHALL return exactly one question at a time
2. WHEN the frontend submits an answer THEN the API SHALL accept the answer type (A, B, all good, all bad) and hesitation time
3. WHEN the frontend submits an answer THEN the API SHALL process the response and return the next question or final results
4. WHEN recommendations are ready THEN the API SHALL return the structured destination and experience data
5. WHEN the user provides feedback THEN the API SHALL accept the feedback and trigger a new loop iteration if needed
