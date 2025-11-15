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