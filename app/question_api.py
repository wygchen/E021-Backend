import uuid
import time
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.question_generator import QuestionGeneratorAgent


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

# Instantiate the agent (kept in-process so langchain/LLM objects can be reused per server run)
agent = QuestionGeneratorAgent()


@app.get("/")
def root():
    return {"message": "Question Generator API", "status": "running", "docs": "/docs"}


@app.post("/session", status_code=201)
def create_session() -> Dict[str, str]:
    sid = str(uuid.uuid4())
    SESSIONS[sid] = {"qa_history": [], "part": None}
    # Initialize by stepping once so a pending question is set
    agent.step_state(SESSIONS[sid])
    return {"session_id": sid}


@app.get("/session/{session_id}/question")
def get_question(session_id: str):
    state = SESSIONS.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="session not found")
    # Ensure agent processes current state and sets pending_question
    agent.step_state(state)
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
    state["submitted_answer"] = {"answer": payload.answer, "hesitation_seconds": payload.hesitation_seconds}
    # Advance agent
    agent.step_state(state)
    # After stepping, return the new pending question (if any)
    pending = state.get("pending_question")
    return {"pending_question": pending, "user_travel_profile": state.get("user_travel_profile")}


@app.get("/session/{session_id}/state")
def get_state(session_id: str):
    state = SESSIONS.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="session not found")
    return state
