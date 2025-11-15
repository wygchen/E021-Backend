"""Interactive script to run the QuestionGeneratorAgent with user input."""

import sys
import time
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.question_generator import QuestionGeneratorAgent


def display_question(pending_question):
    """Display the current question to the user."""
    if not pending_question:
        return
    
    choices = pending_question.get("choices", [])
    part = pending_question.get("part", "unknown")
    question_num = pending_question.get("question_index", 0)
    
    print(f"\n{'='*60}")
    print(f"Question {question_num} ({part.upper()})")
    print(f"{'='*60}")
    
    if len(choices) >= 2:
        print(f"\nA) {choices[0]}")
        print(f"B) {choices[1]}")
    else:
        print("Invalid question format")
    
    print("\nYou can answer: A, B, all good, or all bad")


def get_user_answer():
    """Get and validate user's answer."""
    valid_answers = {"a", "b", "all good", "all bad"}
    
    start_time = time.time()
    while True:
        answer = input("\nYour answer: ").strip()
        elapsed = time.time() - start_time
        
        if answer.lower() in valid_answers:
            return answer, elapsed
        else:
            print("Invalid answer. Please enter A, B, 'all good', or 'all bad'")
            start_time = time.time()  # Reset timer after invalid input


def display_profile(state):
    """Display the final travel profile."""
    profile = state.get("user_travel_profile")
    if profile:
        print(f"\n{'='*60}")
        print("YOUR TRAVEL PROFILE")
        print(f"{'='*60}")
        print(f"\n{profile}\n")
        print(f"{'='*60}")


def display_qa_history(state):
    """Display the Q&A history."""
    qa_history = state.get("qa_history", [])
    if qa_history:
        print(f"\n{'='*60}")
        print("Q&A HISTORY")
        print(f"{'='*60}")
        for i, entry in enumerate(qa_history, 1):
            q = entry.get("question", "N/A")
            a = entry.get("answer", "N/A")
            h = entry.get("hesitation_seconds", 0)
            print(f"\n{i}. Q: {q}")
            print(f"   A: {a} (hesitation: {h:.1f}s)")


def main():
    """Main interactive loop."""
    print("=" * 60)
    print("TRAVEL PREFERENCE QUESTIONNAIRE")
    print("=" * 60)
    print("\nWelcome! This questionnaire will help us understand your travel")
    print("preferences through a series of questions.")
    print("\nInstructions:")
    print("- Answer each question by typing A or B")
    print("- Type 'all good' if both options appeal to you")
    print("- Type 'all bad' if neither option appeals to you")
    
    # Initialize the agent and state
    agent = QuestionGeneratorAgent()
    state = {
        "qa_history": [],
        "part": "part1"
    }
    
    # Initialize first question
    agent.step_state(state)
    
    # Main interaction loop
    while True:
        # Check if we're done
        if state.get("part") == "profile_generated":
            print("\n\nThank you for completing the questionnaire!")
            display_profile(state)
            
            # Ask if user wants to see history
            show_history = input("\nWould you like to see your answer history? (y/n): ").strip().lower()
            if show_history == 'y':
                display_qa_history(state)
            
            break
        
        # Check for errors
        if "last_error" in state:
            print(f"\nError: {state['last_error']}")
            state.pop("last_error")
        
        # Display current question
        pending = state.get("pending_question")
        if not pending:
            print("\nNo more questions. Generating profile...")
            agent.step_state(state)
            continue
        
        display_question(pending)
        
        # Get user answer
        answer, hesitation = get_user_answer()
        
        # Submit answer and advance state
        state["submitted_answer"] = {
            "answer": answer,
            "hesitation_seconds": hesitation
        }
        agent.step_state(state)
    
    print("\nGoodbye!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nQuestionnaire interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
