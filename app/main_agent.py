# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import google.auth
from typing import AsyncGenerator, ClassVar, List

from google.adk.agents import LlmAgent, Agent, LoopAgent, BaseAgent
from google.adk.events import Event, EventActions
from google.adk.agents.invocation_context import InvocationContext
from google.adk.apps.app import App

# Use the QuestionGeneratorAgent implementation from the separate module.
from app.question_generator import QuestionGeneratorAgent

# Prefer an explicit Gemini (Generative Language) endpoint + API key when provided.
# If `GEMINI_API_KEY` and `GEMINI_ENDPOINT` are present in the environment, configure
# the process to use that external Generative Language endpoint. Otherwise fall back
# to initializing Vertex AI (the previous default).
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_ENDPOINT = os.environ.get("GEMINI_ENDPOINT")

if GEMINI_API_KEY and GEMINI_ENDPOINT:
    # Export the provided values into the environment for downstream libraries.
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
    os.environ["GEMINI_ENDPOINT"] = GEMINI_ENDPOINT
    # Tell ADK to prefer the Generative Language endpoint instead of Vertex.
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")
else:
    # Fallback to Vertex AI initialization for existing setups.
    from google.cloud import aiplatform
    aiplatform.init(project='triumph-in-the-skies', location='us-central1')
    _, project_id = google.auth.default()
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "triumph-in-the-skies")
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

class QuestionGeneratorAgent(BaseAgent):
    """Loop-based Question Generator.

    Behavior:
    - On each run, present exactly one question (either Part1 or a follow-up) by setting
      `ctx.session.state['pending_question']` to a dict with the question text and metadata.
    - Expect frontend to submit answers by writing `ctx.session.state['submitted_answer']` as
      a dict: {'answer': 'A'|'B'|'all good'|'all bad', 'hesitation_seconds': float}.
    - When a submitted answer is present, validate and append to `qa_history` in session state.
    - After Part1 (3 questions) completes, the agent will set `ctx.session.state['part'] = 'part2'`
      and (for now) synthesize a simple profile string from the answers and store it as
      `ctx.session.state['user_travel_profile']`.
    """

    QUESTIONS: ClassVar[List[str]] = [
        "Are you looking for A) a trip with a packed itinerary, or B) a more relaxed and spontaneous vacation?",
        "Would you prefer A) a destination with a vibrant nightlife and entertainment scene, or B) a quiet place to unwind and connect with nature?",
        "Are you more interested in A) exploring historical sites and museums, or B) indulging in a shopping and culinary adventure?",
    ]

    def __init__(self, name: str = "QuestionGeneratorAgent") -> None:
        super().__init__(name=name)

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        state = ctx.session.state

        qa_history = state.get("qa_history", [])
        # If a submitted answer is present, process it first.
        submitted = state.pop("submitted_answer", None)
        if submitted:
            # validate answer
            answer = str(submitted.get("answer", "")).strip()
            hesitation = submitted.get("hesitation_seconds")
            normalized = answer.lower()
            allowed = {"a", "b", "all good", "all bad"}
            if normalized not in allowed:
                # Keep the same pending question and set an error flag for the frontend to show.
                state["last_error"] = "Invalid answer. Acceptable answers: A, B, all good, all bad."
                yield Event(author=self.name)
                return

            # Determine which question this answer corresponds to. If pending_question exists, use it.
            pending = state.get("pending_question")
            question_text = None
            if pending and isinstance(pending, dict):
                question_text = pending.get("question")
            else:
                # Fallback: infer by length of qa_history
                idx = len(qa_history)
                if idx < len(self.QUESTIONS):
                    question_text = self.QUESTIONS[idx]

            qa_entry = {
                "question": question_text or "",
                "answer": answer,
                "hesitation_seconds": hesitation,
            }
            qa_history.append(qa_entry)
            state["qa_history"] = qa_history
            # clear pending question after processing
            state.pop("pending_question", None)

        # If still in Part1 (less than 3 answers), present the next question.
        if len(qa_history) < len(self.QUESTIONS):
            next_q = self.QUESTIONS[len(qa_history)]
            state["pending_question"] = {
                "question": next_q,
                "part": "part1",
                "question_index": len(qa_history) + 1,
            }
            # clear any previous error
            state.pop("last_error", None)
            yield Event(author=self.name)
            return

        # Part1 complete. If profile not yet synthesized, create a simple profile summary.
        if not state.get("user_travel_profile"):
            # Synthesize a short profile from the QA history. This is a lightweight placeholder
            #; downstream ExperiencePlanningAgent can refine or request clarifications.
            parts = []
            for entry in qa_history:
                q = entry.get("question", "")
                a = entry.get("answer", "")
                parts.append(f"{q} -> {a}")
            profile = "; ".join(parts)
            state["user_travel_profile"] = f"User travel profile based on answers: {profile}"
            # mark that part2 has been initialized
            state["part"] = "profile_generated"

        # No further questions from this agent in the default flow. Let the loop continue.
        yield Event(author=self.name)


# Instantiate the loop-based question generator
question_generator_agent = QuestionGeneratorAgent()

# ExperiencePlanningAgent: evaluates whether sufficient preferences exist and (if so) generates
# 3 destination recommendations with 4 experiences each that align with the user's profile.
experience_planning_agent = LlmAgent(
    name="ExperiencePlanningAgent",
    model="gemini-2.5-flash",
    instruction="""You are an experience planner. Read the 'user_travel_profile' and 'qa_history' from the session state.

1) Decide whether the provided profile contains sufficient detail to make informed recommendations. Output a JSON object with a boolean field 'sufficient'.
2) If 'sufficient' is true, produce a 'destinations' list containing exactly 3 destinations. Each destination must include: 'name' (string), 'summary' (1-2 sentences explaining why it matches), and 'experiences' (a list of 4 unique experience offers). Each experience must have 'title', 'short_description', and a reason why it matches the user's preferences.
3) If 'sufficient' is false, produce a 'clarifying_questions' list of up to 3 single A/B style follow-up questions (no locations or offers) to gather missing preferences.

Return the result as JSON under the key 'experience_planning_result'.
""",
    output_key="experience_planning_result",
)


class EscalationChecker(BaseAgent):
    """Reads the ExperiencePlanningAgent output and yields an Event to escalate (stop loop)
    when recommendations are ready (sufficient == True)."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        result = ctx.session.state.get("experience_planning_result")
        if result and isinstance(result, dict) and result.get("sufficient"):
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            yield Event(author=self.name)


main_loop_agent = LoopAgent(
    name="MainLoopAgent",
    sub_agents=[
        question_generator_agent,
        experience_planning_agent,
        EscalationChecker(name="EscalationChecker"),
    ],
    max_iterations=3,  # Allow up to 3 rounds of questions/refinements
    description="A loop to gather user travel preferences and generate a plan.",
)

root_agent = main_loop_agent

app = App(root_agent=root_agent, name="app")