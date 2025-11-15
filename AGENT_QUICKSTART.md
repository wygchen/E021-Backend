# Travel Planning Agent - Quick Start Guide

## Overview

This agent uses:
1. **Dynamic Question Generation** - Asks intelligent questions to understand preferences
2. **RAG (Retrieval Augmented Generation)** - Searches destination database semantically
3. **Experience Planning** - Matches activities to user profile

## Quick Test (Terminal Interface)

```bash
python run_agent_simple.py
```

This will:
- Ask you 3-5 questions about your travel preferences
- Generate a profile based on your answers (and hesitation time!)
- Search the destination database using semantic similarity
- Return personalized destinations with curated experiences

### Example Session

```
🤖 Agent Question #1:
   A) Spa days, yoga retreats, and wellness activities
   B) Exploring local markets, boutiques, and artisan shops

👤 Your answer (A/B): A

🤖 Agent Question #2:
   A) Visiting museums, historical landmarks, and cultural sites
   B) Trying local cuisine, food tours, and cooking classes

👤 Your answer (A/B): B

... (more questions)

✅ Profile completed!
📝 Your Travel Profile: This traveler enjoys...

🎉 Your Personalized Travel Plan
📍 DESTINATION 1: Taichung
   ✨ Recommended Experiences:
   1. Bubble Tea Making Class
   2. Night Market Food Tour
   ...
```

## How It Works

### Architecture

```
TravelPlanningOrchestrator (main_agent.py)
├── QuestionGeneratorAgent (question_generator.py)
│   ├── Asks questions (A/B choices)
│   ├── Records answers + hesitation time
│   └── Generates user profile via LLM
└── ExperiencePlanningAgent (experience_planner.py)
    ├── Uses RAG to search destinations
    ├── Matches experiences semantically  
    └── Returns structured itinerary
```

### State Management

The agent maintains session state with:
- `qa_history`: All questions & answers with hesitation times
- `user_travel_profile`: Generated profile text
- `experience_planning_result`: Final itinerary

### Why `run_agent_simple.py` Instead of ADK Runner?

The ADK runner has session state persistence issues. This simple interface:
- Uses direct state dictionary (like the Question API)
- Bypasses ADK's session service
- Works reliably for testing

For production, use the **Question API** which handles sessions properly.

## Production Usage (REST API)

```bash
# Start the API server
uvicorn app.question_api:app --reload

# The API will be available at http://localhost:8000
# Documentation at http://localhost:8000/docs
```

### API Endpoints

- `POST /session` - Create new session
- `GET /session/{id}/question` - Get current question
- `POST /session/{id}/answer` - Submit answer
- `GET /session/{id}/state` - Get full state

## Integration with TravelPlanningOrchestrator

The orchestrator coordinates both agents:

1. **Input**: User sends "A" or "B|2.5" (answer + optional hesitation)
2. **QuestionGeneratorAgent**: Processes answer, updates state
3. **Profile Check**: If enough questions answered, generates profile
4. **ExperiencePlanningAgent**: Uses RAG to find destinations
5. **Output**: Returns question or final plan

### Key State Flow

```python
# User answers "A" with 2.5s hesitation
state['submitted_answer'] = {'answer': 'A', 'hesitation_seconds': 2.5}

# QuestionGeneratorAgent processes it
q_agent.step_state(state)
# → Adds to qa_history
# → Generates next question OR profile

# When profile ready:
state['user_travel_profile'] = "This traveler enjoys..."
state['part'] = "profile_generated"

# ExperiencePlanningAgent runs
planner_agent.run_async(ctx)
# → Uses RAG to search destinations
# → Returns structured itinerary
```

## Files

- `run_agent_simple.py` - Simple terminal test interface ✅ Use this for testing
- `run_agent.py` - ADK runner version (has state issues, needs fixing)
- `app/main_agent.py` - TravelPlanningOrchestrator
- `app/question_generator.py` - Question & profile generation
- `app/experience_planner.py` - RAG-powered planning
- `app/question_api.py` - REST API (production ready) ✅ Use this for web frontend

## Next Steps

1. **For Testing**: Use `run_agent_simple.py`
2. **For Web Frontend**: Use the Question API (`uvicorn app.question_api:app --reload`)
3. **For ADK Integration**: Fix session persistence in `run_agent.py` (future work)

The agent is fully functional and ready for integration!
