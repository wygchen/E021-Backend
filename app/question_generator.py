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
            "Museums, landmarks, and cultural sites",
            "Food tours, local cuisine, cooking classes",
        ]
    },
    # Q3: nightlife vs nature
    {
        "choices": [
            "Bars, clubs, and vibrant city nightlife",
            "Hiking, beaches, and outdoor activities",
        ]
    },
    # Q4: luxury vs budget
    {
        "choices": [
            "Luxury hotels and upscale accommodations",
            "Budget hostels, guesthouses, or Airbnb",
        ]
    },
    # Q5: structure vs spontaneity
    {
        "choices": [
            "Organized tours and structured itineraries",
            "Spontaneous adventures and independent travel",
        ]
    },
    # Q6: social vs solitary
    {
        "choices": [
            "Group activities and meeting new people",
            "Quiet time alone and personal reflection",
        ]
    },
    # Q7: adventure vs relaxation
    {
        "choices": [
            "Thrilling activities like zip-lining and rock climbing",
            "Relaxing by pool, beach, slow-paced sightseeing",
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

    def _generate_next_question(self, qa_history: List[Dict[str, Any]]) -> dict:
        """Use LLM to generate the next personalized question based on conversation history.
        
        This analyzes:
        - Previous answers to understand preferences
        - Hesitation times to detect uncertainty
        - Gaps in knowledge about the traveler
        
        Returns:
            dict with keys:
                - 'should_end': bool - whether we have enough info
                - 'profile': str or None - travel profile if should_end is True
                - 'choices': list or None - new question choices if should_end is False
                - 'reasoning': str - why this question was chosen
        """
        client = self._get_gemini_client()
        if client is None:
            # Fallback: use first default question if no LLM
            if len(qa_history) < len(DEFAULT_QUESTIONS):
                return {
                    "should_end": False,
                    "profile": None,
                    "choices": DEFAULT_QUESTIONS[len(qa_history)]["choices"],
                    "reasoning": "Default question (no LLM available)"
                }
            return {"should_end": True, "profile": None, "choices": None, "reasoning": "No LLM"}

        # Build detailed history string
        history_str = ""
        for i, entry in enumerate(qa_history, 1):
            q = entry.get('question', 'N/A')
            a = entry.get('answer', 'N/A')
            h = entry.get('hesitation_seconds', 0)
            
            # Interpret hesitation
            if h < 1:
                confidence = "very confident"
            elif h < 2:
                confidence = "confident"
            elif h < 4:
                confidence = "somewhat uncertain"
            else:
                confidence = "very uncertain"
            
            history_str += f"\n{i}. Q: {q}\n   Answer: {a} ({confidence}, {h:.1f}s hesitation)\n"

        # Determine minimum questions needed
        min_questions = 7
        max_questions = 10
        questions_asked = len(qa_history)
        
        prompt = (
            "You are an expert travel advisor conducting a preference interview. Your goal is to build a DEEP, "
            "COMPREHENSIVE understanding of this traveler's preferences through strategic questioning.\n\n"
            
            "CONVERSATION HISTORY:\n"
            f"{history_str}\n"
            f"Total questions asked so far: {questions_asked}\n\n"
            
            "ANALYSIS FRAMEWORK:\n"
            "1. PREFERENCE CLARITY: Do we clearly understand their core travel motivations?\n"
            "2. BEHAVIORAL PATTERNS: What do hesitation times reveal about their certainty?\n"
            "3. INFORMATION GAPS: What critical aspects are still unknown?\n"
            "   - Accommodation style (luxury, budget, unique stays)\n"
            "   - Activity pace (fast-paced, relaxed, balanced)\n"
            "   - Social preference (solo, group, couples)\n"
            "   - Meal importance (foodie, practical, adventurous)\n"
            "   - Cultural immersion level (deep dive, light touch, avoid)\n"
            "   - Nature vs urban preference\n"
            "   - Physical activity level\n"
            "   - Time of day preferences (early bird, night owl)\n"
            "   - Travel style (structured, spontaneous)\n"
            "   - Budget consciousness\n\n"
            
            "DECISION CRITERIA:\n"
            f"- You MUST ask at least {min_questions} questions to build a complete profile\n"
            f"- You MUST end questioning after {max_questions} questions, even if some minor details are missing\n"
            f"- CRITICAL: If questions_asked >= {max_questions}, you MUST set should_end=true and create the profile NOW\n"
            "- Between 7-10 questions: end when you have clear answers about MOST major travel dimensions\n"
            "- If the user showed high hesitation (>3s), prioritize clarifying that area\n"
            "- Each new question should explore a DIFFERENT dimension than previous ones\n"
            "- Questions should be SPECIFIC and ACTIONABLE for destination matching\n\n"
            
            "TASK:\n"
            "Based on the conversation history, decide the NEXT STEP:\n\n"
            
            f"IMPORTANT: You have asked {questions_asked} questions. "
            f"{'You MUST CREATE THE PROFILE NOW - do not ask more questions!' if questions_asked >= max_questions else f'You may ask up to {max_questions - questions_asked} more questions before you must create the profile.'}\n\n"
            
            "Option A - ASK ANOTHER QUESTION (only if questions_asked < 10 AND information is incomplete):\n"
            "Generate a NEW personalized A/B question that:\n"
            "- Explores an UNEXPLORED dimension of their travel preferences\n"
            "- Or clarifies an area where they showed uncertainty\n"
            "- Uses CONCRETE examples, not abstract concepts\n"
            "- Directly helps match them to specific destinations/experiences\n"
            "- CRITICAL: Each choice MUST be 10 words or less - keep it simple and scannable\n"
            "- Use short, punchy language that's easy to understand at a glance\n\n"
            
            "Option B - CREATE PROFILE (if questions_asked >= 7):\n"
            f"{'MANDATORY: You have reached the maximum number of questions. Create the profile NOW.' if questions_asked >= max_questions else f'Optional: If you have {min_questions}+ questions AND clear understanding of MOST dimensions:'}\n"
            "- Activity preferences (cultural, adventurous, relaxing, social)\n"
            "- Pace and structure preferences\n"
            "- Budget and accommodation style\n"
            "- Food/dining importance\n"
            "- Social dynamics preference\n\n"
            
            "OUTPUT FORMAT (valid JSON only):\n"
            "{\n"
            '  "should_end": false,  // true only if comprehensive profile is possible\n'
            '  "reasoning": "Why this decision was made",\n'
            '  "choices": ["Choice A (max 10 words)", "Choice B (max 10 words)"],  // null if should_end=true. EACH choice must be 10 words or less!\n'
            '  "profile": null  // or detailed profile string if should_end=true\n'
            "}\n\n"
            
            "EXAMPLES OF GOOD SHORT CHOICES:\n"
            '  "choices": ["Luxury hotels with full amenities", "Budget hostels and local guesthouses"]\n'
            '  "choices": ["Action-packed itinerary visiting multiple sites daily", "Relaxed pace with plenty of downtime"]\n'
            '  "choices": ["Street food and local markets", "Fine dining and Michelin-starred restaurants"]\n'
            '  "choices": ["Solo travel for personal freedom", "Group tours with social interaction"]\n\n'
            
            "PROFILE REQUIREMENTS (if should_end=true):\n"
            "- 4-6 sentences covering ALL major dimensions\n"
            "- Include specific preferences, not generalizations\n"
            "- Mention hesitation patterns and what they reveal\n"
            "- Focus on ACTIONABLE traits for destination matching\n"
            "- Use rich descriptive language\n\n"
            
            "Output ONLY the JSON, no other text."
        )

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
            )
            
            if not response or not response.text:
                # Fallback to default question
                if len(qa_history) < len(DEFAULT_QUESTIONS):
                    return {
                        "should_end": False,
                        "profile": None,
                        "choices": DEFAULT_QUESTIONS[len(qa_history)]["choices"],
                        "reasoning": "LLM response failed, using default"
                    }
                return {"should_end": True, "profile": None, "choices": None, "reasoning": "LLM failed"}
            
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
            except Exception as e:
                print(f"[Q-AGENT] JSON parse error: {e}")
                # Fallback
                if len(qa_history) < len(DEFAULT_QUESTIONS):
                    return {
                        "should_end": False,
                        "profile": None,
                        "choices": DEFAULT_QUESTIONS[len(qa_history)]["choices"],
                        "reasoning": "JSON parse failed"
                    }
                return {"should_end": True, "profile": None, "choices": None, "reasoning": "Parse failed"}
            
            # Validate structure
            if "should_end" in parsed:
                return {
                    "should_end": bool(parsed.get("should_end", False)),
                    "profile": parsed.get("profile"),
                    "choices": parsed.get("choices"),
                    "reasoning": parsed.get("reasoning", "No reasoning provided")
                }
            
            # Invalid structure, fallback
            if len(qa_history) < len(DEFAULT_QUESTIONS):
                return {
                    "should_end": False,
                    "profile": None,
                    "choices": DEFAULT_QUESTIONS[len(qa_history)]["choices"],
                    "reasoning": "Invalid structure"
                }
            return {"should_end": True, "profile": None, "choices": None, "reasoning": "Invalid"}
            
        except Exception as e:
            print(f"[Q-AGENT] LLM error: {e}")
            # Fallback to default
            if len(qa_history) < len(DEFAULT_QUESTIONS):
                return {
                    "should_end": False,
                    "profile": None,
                    "choices": DEFAULT_QUESTIONS[len(qa_history)]["choices"],
                    "reasoning": f"Exception: {e}"
                }
            return {"should_end": True, "profile": None, "choices": None, "reasoning": "Exception"}

    def step_state(self, state: Dict[str, Any]) -> None:
        """Advance the provided session state by one API interaction.

        Uses LLM to generate personalized questions based on user's history and hesitation patterns.
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

        # Use LLM to generate next question or profile
        # This happens for EVERY question, making them all personalized
        decision = self._generate_next_question(qa_history)
        
        if decision["should_end"]:
            # End questioning and create profile
            if decision["profile"]:
                state["user_travel_profile"] = decision["profile"]
            else:
                # Fallback profile generation (shouldn't happen with good LLM prompt)
                parts = []
                for entry in qa_history:
                    q = entry.get("question", "")
                    a = entry.get("answer", "")
                    h = entry.get("hesitation_seconds", 0)
                    parts.append(f"{q} -> {a} ({h:.1f}s)")
                profile = "; ".join(parts)
                state["user_travel_profile"] = f"User travel profile based on answers: {profile}"
            state["part"] = "profile_generated"
            return
        else:
            # Continue with LLM-generated question
            if decision["choices"] and isinstance(decision["choices"], list) and len(decision["choices"]) >= 2:
                state["pending_question"] = {
                    "choices": decision["choices"],
                    "part": "dynamic",
                    "question_index": len(qa_history) + 1,
                    "reasoning": decision.get("reasoning", "")
                }
                return
            else:
                # Fallback if LLM didn't provide valid choices (shouldn't happen)
                print("[Q-AGENT] Warning: LLM didn't provide valid choices, using default")
                if len(qa_history) < len(DEFAULT_QUESTIONS):
                    next_q = DEFAULT_QUESTIONS[len(qa_history)]
                    state["pending_question"] = {
                        "choices": next_q["choices"],
                        "part": "fallback",
                        "question_index": len(qa_history) + 1,
                    }
                else:
                    # Force end if we've exhausted defaults
                    state["user_travel_profile"] = "Travel profile based on limited information"
                    state["part"] = "profile_generated"
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