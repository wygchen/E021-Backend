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
from google.adk.agents import Agent, LoopAgent
from google.adk.apps.app import App

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

# Part 1: 3 questions covering the 6 basic categories
question_generator_agent = Agent(
    name="QuestionGeneratorAgent",
    model="gemini-2.5-flash",
    instruction="""You are a travel preference analyst. Your goal is to understand a user's travel style by asking a series of questions.

Part 1: Ask the user these 3 questions exactly as they are written, one at a time. Wait for the user's answer before asking the next question.

1. Are you looking for A) a trip with a packed itinerary, or B) a more relaxed and spontaneous vacation?
2. Would you prefer A) a destination with a vibrant nightlife and entertainment scene, or B) a quiet place to unwind and connect with nature?
3. Are you more interested in A) exploring historical sites and museums, or B) indulging in a shopping and culinary adventure?

After asking these three questions, analyze the user's responses to create a concise, one-paragraph user travel profile.

Part 2: Based on the initial profile, act as a ReAct agent to ask more customized questions to clarify any confusion or dive deeper into their stated interests.
- If the user seems confused, generate scenario-based questions to help them decide.
- If the user shows strong interest in an area, ask more specific questions to understand the nuances of their preference.

Your final output should be a useful user travel profile that the next agent can use to recommend locations and experiences.
""",
    output_key="user_travel_profile",
)

main_loop_agent = LoopAgent(
    name="MainLoopAgent",
    sub_agents=[
        question_generator_agent,
        # ExperiencePlanningAgent would go here
    ],
    max_iterations=3,  # Allow up to 3 rounds of questions/refinements
    description="A loop to gather user travel preferences and generate a plan.",
)

root_agent = main_loop_agent

app = App(root_agent=root_agent, name="app")