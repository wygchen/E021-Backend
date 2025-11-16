# Frontend-Backend Integration Guide

## ✅ Integration Status: READY

The frontend (SwipeQuiz.tsx) and backend (question_api.py) are **fully compatible** and working together!

---

## 🔄 Complete Flow

### 1. Session Creation
**Frontend:**
```typescript
const apiClient = new QuestionApiClient();
await apiClient.createSession();
```

**Backend Endpoint:**
```
POST /session
Response: { "session_id": "uuid-here" }
```

**What happens:**
- Backend creates new session with empty state
- Calls `agent.step_state(state)` to generate first question
- Returns session ID to frontend

---

### 2. Get First Question
**Frontend:**
```typescript
const response = await apiClient.getQuestion();
const question = response.pending_question;
// question.choices = ["Museums and culture", "Beaches and nature"]
// question.question_index = 1
```

**Backend Endpoint:**
```
GET /session/{session_id}/question
Response: {
  "pending_question": {
    "choices": ["Choice A text", "Choice B text"],
    "part": "dynamic",
    "question_index": 1,
    "reasoning": "LLM's reasoning for this question"
  }
}
```

---

### 3. Submit Answer
**Frontend:**
```typescript
// User selects option A after 2.5 seconds
const response = await apiClient.submitAnswer('A', 2.5);

// Or selects "I like both"
const response = await apiClient.submitAnswer('all good', 3.1);

// Or selects "Not interested in either"
const response = await apiClient.submitAnswer('all bad', 1.8);
```

**Backend Endpoint:**
```
POST /session/{session_id}/answer
Body: {
  "answer": "A",  // or "B", "all good", "all bad"
  "hesitation_seconds": 2.5
}

Response: {
  "pending_question": { ... next question ... },
  "user_travel_profile": null  // null until quiz complete
}
```

**What happens:**
- Backend records answer with hesitation time in `qa_history`
- Calls LLM to analyze history and generate next question
- Returns next question OR profile if done

---

### 4. Quiz Completion
**After 7-10 questions, backend returns:**
```json
{
  "pending_question": null,
  "user_travel_profile": "This traveler seeks adventure-packed group trips on a budget. They prioritize experiencing local culture through food tours and hiking, with a preference for boutique accommodations. Quick decision-making suggests confidence in choices.",
  "part": "profile_generated"
}
```

**Frontend handles:**
```typescript
if (response.pending_question === null) {
  // Quiz complete!
  handleQuizComplete(response.user_travel_profile);
}
```

---

## 📋 Answer Types Supported

| Frontend Choice | API Value | Meaning |
|----------------|-----------|---------|
| User taps Choice A | `"A"` | Prefers option A |
| User taps Choice B | `"B"` | Prefers option B |
| "I like both" button | `"all good"` | Likes both options |
| "Not interested" button | `"all bad"` | Dislikes both options |

---

## 🎯 Key Features

### ✅ Hesitation Time Tracking
- Frontend: `(Date.now() - startTime) / 1000`
- Backend: Analyzes hesitation patterns
- Fast answers (<1s) = confident
- Slow answers (>4s) = uncertain → LLM may ask follow-up

### ✅ Dynamic Question Generation
- Every question is LLM-generated based on history
- LLM analyzes previous answers and hesitation
- Questions get more specific as quiz progresses
- Minimum 7 questions, maximum 10 questions

### ✅ Concise Questions
- Each choice is **max 10 words**
- Easy to scan and decide quickly
- Examples:
  - "Museums and cultural landmarks"
  - "Beaches and outdoor adventures"
  - "Luxury hotels with amenities"
  - "Budget hostels and guesthouses"

---

## 🧪 Testing

### Test Backend API
```bash
cd /Users/ivanl/Desktop/Development/my-awesome-agent-real
/Users/ivanl/Desktop/Development/my-awesome-agent-real/.conda/bin/python scripts/test_question_api.py
```

### Test with HTML Demo
```bash
# Backend is already running on port 8000
# Open test_frontend.html in browser
open test_frontend.html
```

### Test in Terminal
```bash
/Users/ivanl/Desktop/Development/my-awesome-agent-real/.conda/bin/python run_agent_simple.py
```

---

## 🌐 API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check |
| `/session` | POST | Create new session |
| `/session/{id}/question` | GET | Get current/next question |
| `/session/{id}/answer` | POST | Submit answer + hesitation |
| `/session/{id}/state` | GET | Get full session state (debug) |

---

## 🔧 Configuration

### Frontend Environment
```typescript
// In .env or vite config
VITE_API_URL=http://localhost:8000
```

### Backend CORS
Already configured to allow all origins in development:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # All origins allowed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🚀 Running Everything

### 1. Start Backend
```bash
cd /Users/ivanl/Desktop/Development/my-awesome-agent-real
/Users/ivanl/Desktop/Development/my-awesome-agent-real/.conda/bin/uvicorn app.question_api:app --reload --port 8000
```

### 2. Start Frontend (in separate terminal)
```bash
cd /Users/ivanl/Desktop/Development/Cathayhackathon2025
npm run dev
```

### 3. Test the Flow
1. Open frontend in browser
2. Navigate to SwipeQuiz component
3. Answer questions by tapping choices
4. Backend tracks each answer + hesitation time
5. After 7-10 questions, profile is generated
6. Frontend receives profile and completes quiz

---

## 🎨 Frontend State Management

```typescript
const [currentQuestion, setCurrentQuestion] = useState<QuestionChoice | null>(null);
const [startTime, setStartTime] = useState<number>(Date.now());

// When question changes
useEffect(() => {
  if (response.pending_question) {
    setCurrentQuestion(response.pending_question);
    setStartTime(Date.now()); // Reset timer for new question
  }
}, [response]);

// When user answers
const hesitationSeconds = (Date.now() - startTime) / 1000;
await apiClient.submitAnswer(choice, hesitationSeconds);
```

---

## 📊 Example Flow

```
1. Frontend: POST /session
   Backend: Creates session, generates Q1
   Response: { session_id: "abc-123" }

2. Frontend: GET /session/abc-123/question
   Backend: Returns Q1
   Response: {
     pending_question: {
       choices: ["Museums and culture", "Beaches and nature"],
       question_index: 1
     }
   }

3. User taps "Beaches and nature" after 2.3s
   Frontend: POST /session/abc-123/answer
   Body: { answer: "B", hesitation_seconds: 2.3 }
   Backend: LLM analyzes, generates Q2
   Response: {
     pending_question: {
       choices: ["Luxury hotels", "Budget hostels"],
       question_index: 2
     }
   }

4. ... repeat for 7-10 questions ...

5. After Q9, LLM decides profile is complete
   Frontend: POST /session/abc-123/answer
   Backend: Generates profile instead of new question
   Response: {
     pending_question: null,
     user_travel_profile: "This traveler seeks..."
   }

6. Frontend detects null pending_question
   → Quiz complete!
   → Navigate to results/destinations
```

---

## ✅ Integration Checklist

- [x] Backend accepts A/B/all good/all bad
- [x] Backend tracks hesitation time
- [x] Backend generates 7-10 questions
- [x] Backend creates rich profile (4-6 sentences)
- [x] Frontend sends correct answer format
- [x] Frontend measures hesitation time accurately
- [x] Frontend handles quiz completion
- [x] CORS configured for local development
- [x] TypeScript types match backend response
- [x] Error handling on both sides

---

## 🎉 Everything is Ready!

The integration is **complete and working**. The frontend SwipeQuiz component will:
1. ✅ Create session automatically
2. ✅ Display LLM-generated questions (max 10 words each)
3. ✅ Track hesitation time per answer
4. ✅ Submit answers with timing data
5. ✅ Handle "I like both" and "Neither" options
6. ✅ Receive personalized travel profile after 7-10 questions
7. ✅ Navigate to next screen with profile data

**No changes needed to SwipeQuiz.tsx** - it already works perfectly with the backend!
