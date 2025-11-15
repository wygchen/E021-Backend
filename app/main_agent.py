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
from google.genai import types as genai_types

# Use the QuestionGeneratorAgent implementation from the separate module.
from app.question_generator import QuestionGeneratorAgent
# Use the RAG-powered ExperiencePlanningAgent
from app.experience_planner import ExperiencePlanningAgent

# Prefer an explicit Gemini (Generative Language) endpoint + API key when provided.
# If `GEMINI_API_KEY` is present in the environment, configure
# the process to use that external Generative Language endpoint. Otherwise fall back
# to initializing Vertex AI (the previous default).
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_ENDPOINT = os.environ.get("GEMINI_ENDPOINT")

if GEMINI_API_KEY:
    # Export the provided values into the environment for downstream libraries.
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
    if GEMINI_ENDPOINT:
        os.environ["GEMINI_ENDPOINT"] = GEMINI_ENDPOINT
    # Tell ADK to prefer the Generative Language endpoint instead of Vertex.
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")
else:
    # Fallback to Vertex AI initialization for existing setups.
    try:
        from google.cloud import aiplatform
        aiplatform.init(project='triumph-in-the-skies', location='us-central1')
        _, project_id = google.auth.default()
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "triumph-in-the-skies")
        os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
        os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
    except Exception as e:
        print(f"Warning: Could not initialize Vertex AI: {e}")
        print("Please set GEMINI_API_KEY environment variable or configure Google Cloud credentials.")

# Instantiate the agents
question_generator_agent = QuestionGeneratorAgent()
experience_planning_agent = ExperiencePlanningAgent()


class TravelPlanningOrchestrator(BaseAgent):
    """
    Main orchestrator agent that coordinates the question generation and planning flow.
    
    This agent handles the conversation flow:
    1. Calls QuestionGeneratorAgent to manage Q&A
    2. When profile is ready, calls ExperiencePlanningAgent to generate plan
    3. Returns appropriate responses to the user
    """
    
    def __init__(self, name: str = "TravelPlanningOrchestrator"):
        super().__init__(name=name)
    
    def _get_question_agent(self) -> QuestionGeneratorAgent:
        """Get or create QuestionGeneratorAgent instance."""
        return QuestionGeneratorAgent()
    
    def _get_planner_agent(self) -> ExperiencePlanningAgent:
        """Get or create ExperiencePlanningAgent instance."""
        return ExperiencePlanningAgent()
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        state = ctx.session.state
        
        # Extract user's latest message from user_content
        # The user might be answering a question (A or B)
        # Format can be "A" or "A|2.5" (answer|hesitation_seconds)
        user_text = None
        if hasattr(ctx, 'user_content') and ctx.user_content:
            # user_content is a Content object with parts
            if hasattr(ctx.user_content, 'parts'):
                for part in ctx.user_content.parts:
                    if hasattr(part, 'text') and part.text:
                        user_text = part.text.strip()
                        break
        
        # Parse answer and hesitation from user input
        # Format: "A|2.0" or just "A"
        if user_text:
            parts = user_text.split('|')
            answer = parts[0].strip().upper()
            hesitation = float(parts[1]) if len(parts) > 1 else 2.0
            
            if answer in ['A', 'B']:
                state['submitted_answer'] = {
                    'answer': answer,
                    'hesitation_seconds': hesitation
                }
        
        # Get agent instances
        question_agent = self._get_question_agent()
        planner_agent = self._get_planner_agent()
        
        # Step 1: Let QuestionGeneratorAgent process and yield its events
        # This will show questions to the user
        async for event in question_agent.run_async(ctx):
            # Important: Don't swallow events - yield them so user sees the questions!
            yield event
        
        # Step 2: Check if we have a profile ready for planning
        if state.get("user_travel_profile") and state.get("part") == "profile_generated":
            # Profile is ready, run the experience planner
            async for event in planner_agent.run_async(ctx):
                # Yield planner events too
                yield event
            
            # Check planning result
            planning_result = state.get("experience_planning_result")
            if planning_result:
                status = planning_result.get("status")
                
                if status == "SUCCESS":
                    # Format and return the plan
                    destinations = planning_result.get("data", [])
                    
                    # Create response message
                    response_parts = [
                        "🎉 I've created a personalized travel plan for you!\n"
                    ]
                    
                    for i, dest in enumerate(destinations, 1):
                        response_parts.append(f"\n📍 Destination {i}: {dest.get('name')}")
                        response_parts.append(f"   {dest.get('summary')}")
                        response_parts.append(f"   Cost Level: {dest.get('cost_index')}/5")
                        
                        experiences = dest.get("experiences", [])
                        if experiences:
                            response_parts.append(f"\n   ✨ Recommended Experiences:")
                            for j, exp in enumerate(experiences[:3], 1):  # Show top 3
                                response_parts.append(f"   {j}. {exp.get('title')} ({exp.get('role')})")
                    
                    response_text = "\n".join(response_parts)
                    
                    yield Event(
                        author=self.name,
                        content=genai_types.Content(
                            role="model",
                            parts=[genai_types.Part.from_text(text=response_text)]
                        )
                    )
                    return
                
                elif status == "CONFLICT":
                    # Return conflict question
                    conflict_data = planning_result.get("data", {})
                    conflict_q = conflict_data.get("conflict_question", "")
                    
                    yield Event(
                        author=self.name,
                        content=genai_types.Content(
                            role="model",
                            parts=[genai_types.Part.from_text(text=conflict_q)]
                        )
                    )
                    return
        
        # The QuestionGeneratorAgent already yielded the question or profile message
        # No need to duplicate it here


# Use the orchestrator as the root agent
root_agent = TravelPlanningOrchestrator(name="TravelPlanningOrchestrator")

app = App(root_agent=root_agent, name="app")