#!/usr/bin/env python3
"""
Simple terminal interface to test the travel planning agent.

This bypasses ADK's runner and directly uses the agent's step_state methods,
similar to how the Question API works (which we know works correctly).
"""

import time
from app.question_generator import QuestionGeneratorAgent
from app.experience_planner import ExperiencePlanningAgent


def print_header(text):
    print("\n" + "="*70)
    print(text)
    print("="*70)


def print_section(text):
    print("\n" + "-"*70)
    print(text)
    print("-"*70)


def main():
    print_header("🌍 HK Express - Travel Planning Agent (Terminal Interface)")
    print("\nThis is a simple test interface for the agent.")
    print("The agent will ask you questions to understand your preferences,")
    print("then use RAG to find perfect destinations for you.")
    
    # Create session state (like Question API does)
    state = {}
    
    # Initialize agents
    q_agent = QuestionGeneratorAgent()
    planner_agent = ExperiencePlanningAgent()
    
    # ====================================================================
    # PHASE 1: Question & Answer Loop
    # ====================================================================
    print_section("PHASE 1: Understanding Your Preferences")
    
    # Initialize first question
    q_agent.step_state(state)
    
    question_count = 0
    max_questions = 10  # Safety limit
    
    while question_count < max_questions:
        # Check if we have a pending question
        pending = state.get("pending_question")
        
        if not pending:
            # No more questions - check if profile is ready
            if state.get("user_travel_profile"):
                print("\n✅ Profile completed!")
                break
            else:
                print("\n⚠️  No pending question and no profile. Something went wrong.")
                break
        
        # Display the question
        choices = pending.get("choices", [])
        if len(choices) < 2:
            print("\n⚠️  Invalid question format")
            break
        
        print(f"\n🤖 Agent Question #{question_count + 1}:")
        print(f"   A) {choices[0]}")
        print(f"   B) {choices[1]}")
        
        # Get user input
        print("\n👤 Your answer (A/B): ", end="", flush=True)
        start_time = time.time()
        
        user_input = input().strip().upper()
        
        end_time = time.time()
        hesitation = end_time - start_time
        
        # Validate input
        if user_input not in ['A', 'B']:
            print("   ⚠️  Please answer A or B")
            continue
        
        # Submit the answer
        state['submitted_answer'] = {
            'answer': user_input,
            'hesitation_seconds': hesitation
        }
        
        # Let agent process the answer
        q_agent.step_state(state)
        
        question_count += 1
        
        # Check if profile was generated
        if state.get("part") == "profile_generated":
            print("\n✅ Got enough information! Generating your profile...")
            break
    
    # ====================================================================
    # PHASE 2: Display Profile
    # ====================================================================
    print(f"\n[DEBUG] State keys after Q&A: {list(state.keys())}")
    print(f"[DEBUG] Has profile: {state.get('user_travel_profile') is not None}")
    print(f"[DEBUG] Part value: {state.get('part')}")
    
    if state.get("user_travel_profile"):
        print_section("📝 Your Travel Profile")
        profile = state["user_travel_profile"]
        print(f"\n{profile}\n")
        
        # Show Q&A history
        qa_history = state.get("qa_history", [])
        print(f"\n📊 Questions answered: {len(qa_history)}")
        if qa_history:
            avg_hesitation = sum(q.get('hesitation_seconds', 0) for q in qa_history) / len(qa_history)
            print(f"📊 Average response time: {avg_hesitation:.1f}s")
    else:
        print("\n[DEBUG] Profile not found. Checking qa_history...")
        qa_history = state.get("qa_history", [])
        print(f"[DEBUG] Questions in history: {len(qa_history)}")
        for i, qa in enumerate(qa_history[:3], 1):
            print(f"[DEBUG]   Q{i}: {qa.get('question', 'N/A')[:50]}...")
            print(f"[DEBUG]       A: {qa.get('answer')}, H: {qa.get('hesitation_seconds'):.2f}s")
    
    # ====================================================================
    # PHASE 3: RAG-Powered Planning
    # ====================================================================
    if state.get("user_travel_profile") and state.get("part") == "profile_generated":
        print_section("PHASE 2: Finding Perfect Destinations")
        print("\n🔍 Searching destination database using RAG...")
        print("   • Loading vector indexes")
        print("   • Performing semantic search")
        print("   • Matching experiences to your profile")
        
        # Create a mock context for the planner (it needs ctx.session.state)
        from unittest.mock import Mock
        mock_session = Mock()
        mock_session.state = state
        mock_ctx = Mock()
        mock_ctx.session = mock_session
        
        # Run the planner synchronously
        import asyncio
        
        async def run_planner():
            async for event in planner_agent._run_async_impl(mock_ctx):
                pass  # Let it update state
        
        asyncio.run(run_planner())
        
        # ====================================================================
        # PHASE 4: Display Results
        # ====================================================================
        planning_result = state.get("experience_planning_result")
        
        if planning_result:
            status = planning_result.get("status")
            
            if status == "SUCCESS":
                print_header("🎉 Your Personalized Travel Plan")
                
                destinations = planning_result.get("data", [])
                print(f"\n✨ Found {len(destinations)} perfect destinations for you!\n")
                
                for i, dest in enumerate(destinations, 1):
                    print("━" * 70)
                    print(f"📍 DESTINATION {i}: {dest.get('name', 'Unknown')}")
                    print("━" * 70)
                    print(f"   Summary: {dest.get('summary', 'N/A')}")
                    print(f"   Cost Index: {dest.get('cost_index', 'N/A')}/5")
                    print(f"   Archetype: {dest.get('archetype', 'N/A')}")
                    
                    experiences = dest.get("experiences", [])
                    if experiences:
                        print(f"\n   📋 CURATED EXPERIENCES ({len(experiences)} activities):\n")
                        
                        for j, exp in enumerate(experiences, 1):
                            role_emoji = {
                                "Anchor-Event": "⭐",
                                "Secondary-Highlight": "🌟",
                                "Add-On": "✨"
                            }.get(exp.get('role'), "📌")
                            
                            print(f"   {role_emoji} {j}. {exp.get('title', 'Unknown')}")
                            print(f"      • Role: {exp.get('role', 'N/A')}")
                            print(f"      • Duration: {exp.get('duration', 'N/A')}")
                            print(f"      • Cost: {exp.get('cost_tier', 'N/A')}")
                            
                            desc = exp.get('short_description', '')
                            if desc:
                                print(f"      • {desc[:120]}{'...' if len(desc) > 120 else ''}")
                            print()
                    print()
                
                print_header("✅ Planning Complete!")
                
            elif status == "INSUFFICIENT":
                print("\n⚠️  Not enough information to create a plan.")
                print("   This usually means no profile was generated.")
                
            elif status == "CONFLICT":
                print("\n⚠️  Detected conflicting preferences.")
                conflict_data = planning_result.get("data", {})
                conflict_q = conflict_data.get("conflict_question", "")
                if conflict_q:
                    print(f"\n{conflict_q}")
                    
            else:
                print(f"\n⚠️  Planning status: {status}")
        else:
            print("\n⚠️  No planning result generated.")
    else:
        print("\n⚠️  Could not generate travel profile. Please try again.")
    
    print_header("Session Complete")
    print("\n💡 Next steps:")
    print("   • This agent can be integrated into a web frontend")
    print("   • The Question API (question_api.py) provides REST endpoints")
    print("   • Run: uvicorn app.question_api:app --reload")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Session cancelled by user.\n")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
