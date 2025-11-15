# RAG Integration with Deep Agent - Implementation Summary

## Overview

I've successfully integrated the RAG (Retrieval-Augmented Generation) engine with the Deep Agent system. The system now uses semantic vector search to find real destinations and experiences from your database, instead of generating fictional recommendations.

## What Was Done

### 1. Created RAG Tools Module (`app/rag_tools.py`)

This module provides ADK-compatible wrapper functions for the RAG retrieval system:

- **`RAGToolkit`**: Main class that initializes the RAG retriever with vector indexes
- **`destination_retriever_tool()`**: Searches for destinations based on user preferences
- **`experience_retriever_tool()`**: Searches for experiences within destinations

The toolkit:
- Loads pre-built vector indexes from `RAG/vector_indexes/`
- Uses the Gemini embedding API for semantic search
- Supports both "top-down" (destination-first) and "bottom-up" (experience-first) search strategies

### 2. Created Experience Planning Agent (`app/experience_planner.py`)

This is the **PlannerAgent** from your design document. It implements the core planning logic:

**Key Features:**
- **Smart Search Strategy**: Automatically chooses between top-down and bottom-up approaches based on user profile
- **Conflict Detection**: Identifies when multiple "Anchor-Event" experiences compete and generates conflict questions
- **Role-Based Selection**: Prioritizes experiences by their `itinerary_role` (Anchor-Event > Secondary-Highlight > Add-On)
- **Success/Conflict Output**: Returns structured output with `status: SUCCESS` or `status: CONFLICT`

**The Agent Workflow:**
1. Reads `user_travel_profile` from session state
2. Determines search strategy (top-down vs bottom-up)
3. Searches destinations and experiences using RAG
4. Checks for conflicts between competing experiences
5. Selects 4 best experiences per destination
6. Formats and returns the complete plan

### 3. Updated Main Agent (`app/main_agent.py`)

Replaced the simple LLM-based experience planner with the RAG-powered version:

```python
# OLD: Simple LLM agent without real data
experience_planning_agent = LlmAgent(...)

# NEW: RAG-powered agent with vector search
from app.experience_planner import ExperiencePlanningAgent
experience_planning_agent = ExperiencePlanningAgent()
```

Also updated the `EscalationChecker` to properly handle the new output format (`status: SUCCESS/CONFLICT` instead of `sufficient: true/false`).

### 4. Fixed Run Agent Script (`run_agent.py`)

Enhanced the test script to:
- Display questions properly with A/B choices
- Show the user profile when generated
- Display the complete travel plan with all destinations and experiences
- Handle conflict scenarios
- Provide better console output formatting

## How It Works

### The Complete Flow

1. **Question Phase** (QuestionGeneratorAgent):
   - Asks 3 baseline A/B preference questions
   - Uses LLM to analyze answers and decide if more questions are needed
   - Generates dynamic follow-up questions based on hesitation and uncertainty
   - Creates a `user_travel_profile` paragraph for RAG search

2. **Planning Phase** (ExperiencePlanningAgent):
   - Receives the `user_travel_profile`
   - Determines search strategy:
     - **Top-Down**: If profile is general (e.g., "relaxed, cultural, nature-focused")
       - Search destinations first → then search experiences within each
     - **Bottom-Up**: If profile mentions specific experiences (e.g., "K-Pop concert", "elephant sanctuary")
       - Search experiences first → then get their parent destinations
   
3. **RAG Search**:
   - Converts user profile to embedding vector using Gemini API
   - Performs cosine similarity search against pre-built vector indexes
   - Returns top 3 destinations and top 4-7 experiences per destination

4. **Conflict Resolution** (if needed):
   - Detects if multiple "Anchor-Event" experiences compete
   - Extracts the `conflict_question` from experience dossier
   - Returns `status: CONFLICT` to trigger user clarification
   - User answer updates profile → re-runs planning

5. **Final Output**:
   - 3 destinations with full metadata (name, ID, summary, cost_index)
   - 4 experiences per destination with role, duration, description
   - Ready for UI display and booking flow

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Supervisor (MainLoopAgent)                │
│                                                               │
│  ┌──────────────────┐    ┌─────────────────────────────┐   │
│  │ Question         │ →  │ Experience Planning Agent    │   │
│  │ Generator Agent  │    │ (RAG-Powered)                │   │
│  └──────────────────┘    └─────────────────────────────┘   │
│         │                            │                       │
│         ▼                            ▼                       │
│  user_travel_profile    ┌────────────────────┐              │
│                         │   RAG Toolkit      │              │
│                         └────────────────────┘              │
│                                  │                           │
│                    ┌─────────────┴──────────────┐           │
│                    ▼                            ▼            │
│          ┌──────────────────┐        ┌──────────────────┐  │
│          │ Destination      │        │ Experience       │  │
│          │ Vector Index     │        │ Vector Index     │  │
│          │ (destination_    │        │ (experience_     │  │
│          │  index.pkl)      │        │  index.pkl)      │  │
│          └──────────────────┘        └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Files Modified/Created

### Created:
- ✅ `app/rag_tools.py` - RAG toolkit wrapper for ADK
- ✅ `app/experience_planner.py` - RAG-powered planning agent

### Modified:
- ✅ `app/main_agent.py` - Updated to use new RAG-powered agent
- ✅ `run_agent.py` - Enhanced test script with better output

## Testing the System

### Prerequisites:
1. Vector indexes must exist in `RAG/vector_indexes/`:
   - `destination_index.pkl`
   - `experience_index.pkl`
   
2. Environment variable must be set:
   ```bash
   export GEMINI_API_KEY="your-api-key"
   ```

### Run the Test:
```bash
# Activate your conda environment
conda activate /Users/ivanl/Desktop/Development/my-awesome-agent-real/.conda

# Run the agent
python run_agent.py
```

### Expected Output:
```
🌍 HK Express Travel Preference Discovery & Planning Agent
======================================================================

👤 User: I want to plan a trip
----------------------------------------------------------------------

🤖 Agent [part1]: Which do you prefer?
   A) Spa days, yoga retreats, and wellness activities
   B) Exploring local markets, boutiques, and artisan shops

👤 User: A
----------------------------------------------------------------------

... (more questions) ...

📝 User Profile Generated:
   User prefers wellness activities, cultural sites, and nature experiences...

✅ TRAVEL PLAN GENERATED!
======================================================================

🏙️  Destination 1: Chiang Mai
   ID: THA-CNX
   Summary: The Ethical Adventurer's Hub
   Cost Index: 3/5

   Experiences (4):
   1. Ethical Elephant Sanctuary Full-Day Experience
      Role: Anchor-Event
      Duration: Full-Day
      This is a life-changing day for animal lovers...
   ...
```

## Key Design Patterns Implemented

1. **Supervisor Pattern**: MainLoopAgent orchestrates the two sub-agents
2. **RAG Pattern**: Semantic search over structured data using embeddings
3. **Conflict Resolution**: Loopback mechanism when choices are ambiguous
4. **Top-Down vs Bottom-Up**: Intelligent search strategy selection
5. **Role-Based Prioritization**: Experience selection based on itinerary importance

## Next Steps for Production

1. **Add Conflict Resolution Loop**: Currently, the system detects conflicts but doesn't loop back to ask the user. You'll need to:
   - Add a conflict handler agent
   - Loop back to QuestionGeneratorAgent with the specific conflict question
   - Update the profile and re-run planning

2. **Enhance Search Strategy**: Add more sophisticated logic to determine top-down vs bottom-up:
   - Use LLM to analyze profile and classify intent
   - Support hybrid searches (some destinations specified, others open)

3. **Add Filtering**: Implement filters for:
   - Budget constraints (cost_index)
   - Date ranges (for events)
   - Physical intensity levels
   - Duration preferences

4. **Improve Experience Selection**: 
   - Consider `planner_memo` instructions from dossiers
   - Respect time constraints (don't schedule multiple full-day activities)
   - Balance cost_tier across the 4 experiences

5. **Add Session Persistence**: Store sessions in a database for multi-session conversations

6. **Add Analytics**: Log user behaviors for feedback loop (hesitation times, preference patterns)

## Troubleshooting

### "Import rag_retriever could not be resolved"
This is expected - the import happens dynamically at runtime via `sys.path.insert()`.

### "Vector indexes not found"
Run the RAG index builder first:
```bash
cd RAG
python build_vector_index.py
```

### "GEMINI_API_KEY not found"
Set your API key:
```bash
export GEMINI_API_KEY="your-key-here"
```

## Questions?

The integration follows the architecture from `full_idea.md`. The system now uses real destination and experience data from your JSON databases, searched via semantic embeddings.
