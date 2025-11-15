import asyncio
import json

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from app.main_agent import root_agent
from google.genai import types as genai_types


async def main():
    """
    Runs the agent with a sample query to test the full flow.
    
    This demonstrates:
    1. Dynamic question generation based on user preferences
    2. RAG-powered experience planning with real destination data
    3. Complete end-to-end travel planning flow
    """
    session_service = InMemorySessionService()
    
    # Create session
    session = session_service.create_session_sync(user_id="test_user", app_name="app")
    
    runner = Runner(
        agent=root_agent, app_name="app", session_service=session_service
    )
    
    print("\n" + "="*70)
    print("🌍 HK Express - Agentic Travel Planning Demo")
    print("="*70)
    print("\nThis demo showcases:")
    print("  • Dynamic question generation based on user behavior")
    print("  • RAG-powered destination and experience matching")
    print("  • Personalized itinerary planning")
    print("="*70)
    
    # Start the conversation
    query = "I want to plan a trip"
    print(f"\n👤 User: {query}")
    print("-"*70)
    
    # Initial message - this will display the first question
    events = []
    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=query)]
        ),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"\n🤖 Agent:\n{part.text}")
        events.append(event)
    
    # Simulate answering questions
    # Each answer includes hesitation time which the agent analyzes
    answers = [
        ("A", 2.0),  # Quick decision - clear preference
        ("B", 1.5),  # Quick decision
        ("A", 3.0),  # Moderate hesitation
    ]
    
    for i, (answer, hesitation) in enumerate(answers, 1):
        print(f"\n👤 User: {answer} (hesitation: {hesitation}s)")
        print("-"*70)
        
        # Encode hesitation in the message itself since session state doesn't persist
        # Format: "A|2.0" means answer A with 2.0 seconds hesitation
        answer_with_hesitation = f"{answer}|{hesitation}"
        
        # Run agent with the answer
        events = []
        async for event in runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=genai_types.Content(
                role="user",
                parts=[genai_types.Part.from_text(text=answer_with_hesitation)]
            ),
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"\n🤖 Agent:\n{part.text}")
            events.append(event)
        
        # Check if we have a final plan
        planning_result = session.state.get("experience_planning_result")
        if planning_result and planning_result.get("status") == "SUCCESS":
            print("\n" + "="*70)
            print("🎉 Complete Travel Plan Generated!")
            print("="*70)
            break
        
        # Check if profile was generated
        if session.state.get("user_travel_profile"):
            print(f"\n� Agent is analyzing your preferences...")
    
    # Display final details
    planning_result = session.state.get("experience_planning_result")
    if planning_result and planning_result.get("status") == "SUCCESS":
        print("\n📊 Detailed Plan:")
        print("="*70)
        
        destinations = planning_result.get("data", [])
        for j, dest in enumerate(destinations, 1):
            print(f"\n🏙️  Destination {j}: {dest.get('name', 'Unknown')}")
            print(f"   📍 ID: {dest.get('destination_id', 'N/A')}")
            print(f"   ✨ {dest.get('summary', 'N/A')}")
            print(f"   💰 Cost Index: {dest.get('cost_index', 'N/A')}/5")
            print(f"   🎭 Archetype: {dest.get('archetype', 'N/A')}")
            
            experiences = dest.get("experiences", [])
            if experiences:
                print(f"\n   📋 Curated Experiences ({len(experiences)}):")
                for k, exp in enumerate(experiences, 1):
                    role_emoji = {"Anchor-Event": "⭐", "Secondary-Highlight": "🌟", "Add-On": "✨"}.get(exp.get('role'), "📌")
                    print(f"\n   {role_emoji} {k}. {exp.get('title', 'Unknown')}")
                    print(f"      Role: {exp.get('role', 'N/A')}")
                    print(f"      Duration: {exp.get('duration', 'N/A')}")
                    print(f"      Cost: {exp.get('cost_tier', 'N/A')}")
                    desc = exp.get('short_description', '')
                    if desc:
                        print(f"      {desc[:100]}...")
    
    # Show session stats
    print("\n" + "="*70)
    print("📈 Session Statistics:")
    print("="*70)
    qa_history = session.state.get("qa_history", [])
    print(f"  Questions answered: {len(qa_history)}")
    print(f"  Average hesitation: {sum(q.get('hesitation_seconds', 0) for q in qa_history) / len(qa_history):.1f}s" if qa_history else "  N/A")
    print(f"  Profile generated: {'✅ Yes' if session.state.get('user_travel_profile') else '❌ No'}")
    print(f"  Plan status: {planning_result.get('status') if planning_result else 'Not generated'}")
    
    print("\n" + "="*70)
    print("✅ Demo Complete!")
    print("="*70)
    print("\n💡 This demonstrates the complete integration of:")
    print("   • Dynamic question generation with behavioral analysis")
    print("   • RAG-powered semantic search over destination database")
    print("   • Intelligent itinerary planning with experience prioritization")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
