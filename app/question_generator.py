import json
from typing import Any, Dict, List

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types as genai_types

try:
    from google import genai
except Exception:
    genai = None


DEFAULT_QUESTIONS = [
    # Q1: wellness vs shopping
    {
        "choices": [
            "Spa days, yoga retreats, and wellness activities",
            "Exploring local markets, boutiques, and artisan shops",
        ]
    },
    # Q2: culture/history vs food
    {
        "choices": [
            "Visiting museums, historical landmarks, and cultural sites",
            "Trying local cuisine, food tours, and cooking classes",
        ]
    },
    # Q3: nightlife vs nature
    {
        "choices": [
            "Bars, clubs, live music, and vibrant city nightlife",
            "Hiking, beaches, national parks, and outdoor activities",
        ]
    },
]


class QuestionGeneratorAgent(BaseAgent):
    """Question generator implementing Part1 (three A/B questions) and Part2 dynamic follow-ups.

    The agent exposes a `step_state(state)` helper which advances the in-memory session
    state by processing any submitted answer and setting the next `pending_question`.
    This makes it easy for a FastAPI backend to call the agent per API interaction.
    """

    def __init__(self, name: str = "QuestionGeneratorAgent") -> None:
        super().__init__(name=name)
        # Store Gemini client info for lazy loading
        self._gemini_client = None
        if genai is not None:
            try:
                self._gemini_client = genai.Client()
            except Exception:
                self._gemini_client = None

    def _get_gemini_client(self):
        """Get the Gemini client instance."""
        return self._gemini_client

    # Small deterministic fallback to create a follow-up question when no LLM is available.
    def _analyze_history_and_decide(self, qa_history: List[Dict[str, Any]]) -> dict:
        """Use LLM to analyze entire chat history and decide whether to continue or create profile.
        
        Returns:
            dict with keys:
                - 'should_end': bool - whether we have enough info
                - 'profile': str or None - travel profile paragraph if should_end is True
                - 'choices': list or None - new question choices if should_end is False
        """
        client = self._get_gemini_client()
        if client is None:
            # Fallback: end after 10 rounds
            return {"should_end": True, "profile": None, "choices": None}

        # Build history string
        history_str = "\n".join([
            f"Q: {e.get('question', 'N/A')} | Answer: {e.get('answer', 'N/A')} | Hesitation: {e.get('hesitation_seconds', 0)}s"
            for e in qa_history
        ])

        prompt = (
            "You are a travel preference analyzer. Review the user's question-answer history below."
            " Each entry shows the question, their answer (A/B/all good/all bad), and hesitation time in seconds."
            " High hesitation (4+ seconds) or 'all good'/'all bad' answers suggest uncertainty.\n\n"
            f"Chat History:\n{history_str}\n\n"
            "Task: Determine if you have ENOUGH information to create a comprehensive travel profile."
            " Consider: clarity of preferences, consistency, coverage of travel aspects.\n\n"
            "Output a JSON object with these fields:\n"
            "- 'should_end': boolean - true if enough info to create profile, false if need more questions\n"
            "- 'profile': string or null - if should_end is true, write a 2-3 sentence travel profile paragraph "
            "describing their preferences for retrieval use. If should_end is false, set to null.\n"
            "- 'choices': array or null - if should_end is false, provide 2 new question choices (no labels/prefixes) "
            "to clarify the most uncertain aspect. If should_end is true, set to null.\n\n"
            "Output only valid JSON."
        )

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
            )
            
            if not response or not response.text:
                return {"should_end": True, "profile": None, "choices": None}
            
            result_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            # Parse JSON response
            try:
                parsed = json.loads(result_text)
            except Exception:
                return {"should_end": True, "profile": None, "choices": None}
            
            # Validate structure
            if "should_end" in parsed:
                return {
                    "should_end": bool(parsed.get("should_end", True)),
                    "profile": parsed.get("profile"),
                    "choices": parsed.get("choices"),
                }
            
            return {"should_end": True, "profile": None, "choices": None}
            
        except Exception:
            return {"should_end": True, "profile": None, "choices": None}

    def step_state(self, state: Dict[str, Any]) -> None:
        """Advance the provided session state by one API interaction.

        - Processes `submitted_answer` if present (validates and appends to `qa_history`).
        - If Part1 not complete, sets the next Part1 question in `pending_question`.
        - When Part1 completes, switches to Part2 and generates a follow-up question based
          on simple heuristics and the LLM (ReAct-like decision: clarify vs deepen).
        The function mutates `state` in-place.
        """
        qa_history = state.get("qa_history", [])

        # Process submitted answer
        submitted = state.pop("submitted_answer", None)
        if submitted:
            answer = str(submitted.get("answer", "")).strip()
            hesitation = submitted.get("hesitation_seconds")
            normalized = answer.lower()
            allowed = {"a", "b", "all good", "all bad"}
            if normalized not in allowed:
                state["last_error"] = "Invalid answer. Acceptable answers: A, B, all good, all bad."
                return

            # Attach question ownership
            pending = state.get("pending_question")
            question_text = None
            if pending and isinstance(pending, dict):
                # pending uses structured format
                choices = pending.get("choices")
                if choices and isinstance(choices, list) and len(choices) >= 2:
                    question_text = f"{choices[0]} / {choices[1]}"
                else:
                    question_text = str(choices) if choices else ""
            qa_entry = {
                "question": question_text or "",
                "answer": answer,
                "hesitation_seconds": hesitation,
            }
            qa_history.append(qa_entry)
            state["qa_history"] = qa_history
            state.pop("pending_question", None)

        # If Part1 not complete, present next Part1 question
        if state.get("part") in (None, "part1") and len(qa_history) < len(DEFAULT_QUESTIONS):
            next_q = DEFAULT_QUESTIONS[len(qa_history)]
            state["pending_question"] = {
                "choices": next_q["choices"],
                "part": "part1",
                "question_index": len(qa_history) + 1,
            }
            state.pop("last_error", None)
            state.setdefault("part", "part1")
            return

        # If finished Part1 and haven't initialized Part2, set part2
        if state.get("part") == "part1" or (len(qa_history) >= len(DEFAULT_QUESTIONS) and state.get("part") is None):
            state["part"] = "part2"
            # initialize part2 metadata
            state.setdefault("part2_rounds", 0)

        # Part2 logic: use LLM to analyze entire history and decide next steps
        # Simple heuristic: detect confusion from hesitation
        has_confusion = any(
            entry.get("hesitation_seconds", 0) >= 4
            for entry in qa_history
        )

        # Use LLM to analyze history and decide whether to continue or end
        if state.get("part2_rounds", 0) < 10:
            decision = self._analyze_history_and_decide(qa_history)
            
            if decision["should_end"]:
                # End questioning and create profile
                if decision["profile"]:
                    state["user_travel_profile"] = decision["profile"]
                else:
                    # Fallback profile generation
                    parts = []
                    for entry in qa_history:
                        q = entry.get("question", "")
                        a = entry.get("answer", "")
                        parts.append(f"{q} -> {a}")
                    profile = "; ".join(parts)
                    state["user_travel_profile"] = f"User travel profile based on answers: {profile}"
                state["part"] = "profile_generated"
                return
            else:
                # Continue with new question
                if decision["choices"] and isinstance(decision["choices"], list) and len(decision["choices"]) >= 2:
                    state["pending_question"] = {
                        "choices": decision["choices"],
                        "part": "part2",
                        "question_index": state.get("part2_rounds", 0) + 1,
                    }
                    state["part2_rounds"] = state.get("part2_rounds", 0) + 1
                    return
                else:
                    # Fallback if LLM didn't provide valid choices
                    state["pending_question"] = {
                        "choices": ["Yes, that sounds perfect", "No, I'd prefer something different"],
                        "part": "part2",
                        "question_index": state.get("part2_rounds", 0) + 1,
                    }
                    state["part2_rounds"] = state.get("part2_rounds", 0) + 1
                    return

        # If no more follow-ups or rounds exhausted -> synthesize profile
        if not state.get("user_travel_profile"):
            parts = []
            for entry in qa_history:
                q = entry.get("question", "")
                a = entry.get("answer", "")
                parts.append(f"{q} -> {a}")
            profile = "; ".join(parts)
            state["user_travel_profile"] = f"User travel profile based on answers: {profile}"
            state["part"] = "profile_generated"
            # persist final state
        return

    async def _run_async_impl(self, ctx: InvocationContext):
        """ADK-compatible async implementation that yields proper events."""
        # Use underlying step_state to advance the state machine
        self.step_state(ctx.session.state)
        
        # Now yield an event with the current question or profile
        state = ctx.session.state
        
        # If there's a pending question, yield it as content
        if state.get("pending_question"):
            question = state["pending_question"]
            choices = question.get("choices", [])
            
            if len(choices) >= 2:
                question_text = f"Which do you prefer?\n\nA) {choices[0]}\n\nB) {choices[1]}"
                
                yield Event(
                    author=self.name,
                    content=genai_types.Content(
                        role="model",
                        parts=[genai_types.Part.from_text(text=question_text)]
                    )
                )
        # If profile was just generated, yield it
        elif state.get("part") == "profile_generated" and state.get("user_travel_profile"):
            profile = state["user_travel_profile"]
            yield Event(
                author=self.name,
                content=genai_types.Content(
                    role="model",
                    parts=[genai_types.Part.from_text(
                        text=f"✅ Got it! I've analyzed your preferences. Let me find the perfect destinations for you..."
                    )]
                )
            )
        else:
            # Default: just signal completion
            yield Event(author=self.name)