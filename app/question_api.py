import uuid
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.question_generator import QuestionGeneratorAgent
from app.experience_planner import ExperiencePlanningAgent

# Output directory for session logs
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


class AnswerPayload(BaseModel):
    answer: str
    hesitation_seconds: float


app = FastAPI(title="Question Generator API")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory session store. Keys are session ids.
SESSIONS: Dict[str, Dict[str, Any]] = {}

# Instantiate the agents (kept in-process so langchain/LLM objects can be reused per server run)
question_agent = QuestionGeneratorAgent()
planner_agent = ExperiencePlanningAgent()


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    # Check for API key
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("\n" + "="*70)
        print("⚠️  WARNING: No Gemini API key found!")
        print("   Set GEMINI_API_KEY environment variable to enable LLM features.")
        print("   The API will use fallback default questions.")
        print("="*70 + "\n")


@app.get("/")
def root():
    return {"message": "Question Generator API", "status": "running", "docs": "/docs"}


@app.post("/session", status_code=201)
def create_session() -> Dict[str, str]:
    sid = str(uuid.uuid4())
    start_time = datetime.now()
    
    # Create session state
    SESSIONS[sid] = {
        "qa_history": [], 
        "part": None,
        "session_id": sid,
        "start_time": start_time.isoformat(),
        "start_timestamp": time.time()
    }
    
    # Initialize by stepping once so a pending question is set
    question_agent.step_state(SESSIONS[sid])
    
    # Log session creation to file
    log_file = OUTPUT_DIR / f"session_{sid}.txt"
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("HK EXPRESS - TRAVEL PREFERENCE QUIZ SESSION\n")
        f.write("="*70 + "\n")
        f.write(f"Session ID: {sid}\n")
        f.write(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"ISO Time: {start_time.isoformat()}\n")
        f.write("="*70 + "\n\n")
        f.write("Session initialized. Waiting for user responses...\n\n")
    
    print(f"[SESSION] Created new session: {sid}")
    print(f"[SESSION] Log file: {log_file}")
    
    return {"session_id": sid}


@app.get("/session/{session_id}/question")
def get_question(session_id: str):
    state = SESSIONS.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="session not found")
    # Ensure agent processes current state and sets pending_question
    question_agent.step_state(state)
    pending = state.get("pending_question")
    if not pending:
        # nothing pending: return profile or summary
        return {"pending_question": None, "user_travel_profile": state.get("user_travel_profile")}
    return {"pending_question": pending}


@app.post("/session/{session_id}/answer")
def post_answer(session_id: str, payload: AnswerPayload):
    state = SESSIONS.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="session not found")
    
    # Record submitted answer and time
    state["submitted_answer"] = {
        "answer": payload.answer, 
        "hesitation_seconds": payload.hesitation_seconds
    }
    
    # Log the answer to file
    log_file = OUTPUT_DIR / f"session_{session_id}.txt"
    qa_count = len(state.get("qa_history", [])) + 1
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"Question #{qa_count}\n")
        f.write(f"  Answer: {payload.answer}\n")
        f.write(f"  Hesitation: {payload.hesitation_seconds:.2f} seconds\n")
        f.write(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n")
    
    # Advance agent
    question_agent.step_state(state)
    
    # After stepping, return the new pending question (if any)
    pending = state.get("pending_question")
    profile = state.get("user_travel_profile")
    
    # If profile was generated, log it
    if profile and state.get("part") == "profile_generated":
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("QUIZ COMPLETED - TRAVEL PROFILE GENERATED\n")
            f.write("="*70 + "\n")
            f.write(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Questions: {len(state.get('qa_history', []))}\n")
            
            # Calculate total session time
            start_ts = state.get("start_timestamp", time.time())
            duration = time.time() - start_ts
            f.write(f"Session Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)\n")
            
            # Calculate average hesitation
            qa_history = state.get("qa_history", [])
            if qa_history:
                avg_hesitation = sum(q.get('hesitation_seconds', 0) for q in qa_history) / len(qa_history)
                f.write(f"Average Hesitation: {avg_hesitation:.2f} seconds\n")
            
            f.write("\n" + "-"*70 + "\n")
            f.write("USER TRAVEL PROFILE:\n")
            f.write("-"*70 + "\n")
            f.write(f"{profile}\n")
            f.write("\n" + "="*70 + "\n")
            f.write("QUESTION & ANSWER HISTORY:\n")
            f.write("="*70 + "\n\n")
            
            for i, qa in enumerate(qa_history, 1):
                f.write(f"{i}. Question: {qa.get('question', 'N/A')}\n")
                f.write(f"   Answer: {qa.get('answer', 'N/A')}\n")
                f.write(f"   Hesitation: {qa.get('hesitation_seconds', 0):.2f}s\n\n")
            
            f.write("="*70 + "\n")
            f.write("END OF SESSION\n")
            f.write("="*70 + "\n")
        
        print(f"[SESSION] Quiz completed for session: {session_id}")
        print(f"[SESSION] Profile saved to: {log_file}")
    
    return {"pending_question": pending, "user_travel_profile": profile}


@app.get("/session/{session_id}/state")
def get_state(session_id: str):
    state = SESSIONS.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="session not found")
    return state


@app.post("/session/{session_id}/plan")
async def generate_plan(session_id: str):
    """Generate travel plan using Experience Planner agent."""
    state = SESSIONS.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="session not found")
    
    # Check if profile exists
    profile = state.get("user_travel_profile")
    if not profile:
        raise HTTPException(status_code=400, detail="No travel profile found. Complete the quiz first.")
    
    # Check if plan already exists
    if state.get("experience_planning_result"):
        return state.get("experience_planning_result")
    
    # Create mock context for the planner
    from unittest.mock import Mock
    mock_session = Mock()
    mock_session.state = state
    mock_ctx = Mock()
    mock_ctx.session = mock_session
    
    # Run the planner
    async for event in planner_agent._run_async_impl(mock_ctx):
        pass  # Let it update state
    
    # Get the planning result
    planning_result = state.get("experience_planning_result", {})
    
    # Log planning results to session file
    log_file = OUTPUT_DIR / f"session_{session_id}.txt"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("\n" + "="*70 + "\n")
        f.write("EXPERIENCE PLANNING RESULTS\n")
        f.write("="*70 + "\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Status: {planning_result.get('status', 'UNKNOWN')}\n\n")
        
        if planning_result.get("status") == "SUCCESS":
            destinations = planning_result.get("data", [])
            f.write(f"Destinations Found: {len(destinations)}\n\n")
            
            for i, dest in enumerate(destinations, 1):
                f.write(f"-"*70 + "\n")
                f.write(f"DESTINATION {i}: {dest.get('name', 'Unknown')}\n")
                f.write(f"-"*70 + "\n")
                f.write(f"  Summary: {dest.get('summary', 'N/A')}\n")
                f.write(f"  Cost Index: {dest.get('cost_index', 'N/A')}/5\n")
                f.write(f"  Archetype: {dest.get('archetype', 'N/A')}\n\n")
                
                experiences = dest.get("experiences", [])
                if experiences:
                    f.write(f"  Experiences ({len(experiences)}):\n")
                    for j, exp in enumerate(experiences, 1):
                        f.write(f"    {j}. {exp.get('title', 'Unknown')}\n")
                        f.write(f"       Role: {exp.get('role', 'N/A')}\n")
                        f.write(f"       Duration: {exp.get('duration', 'N/A')}\n")
                        f.write(f"       Cost: {exp.get('cost_tier', 'N/A')}\n")
                        if exp.get('short_description'):
                            f.write(f"       Description: {exp.get('short_description')[:100]}...\n")
                        f.write("\n")
                f.write("\n")
        else:
            f.write(f"Reason: {planning_result.get('message', 'No message provided')}\n")
        
        f.write("="*70 + "\n\n")
    
    print(f"[SESSION] Planning completed for session: {session_id}")
    print(f"[SESSION] Results saved to: {log_file}")
    
    return planning_result
