# 🎬 Demo Setup Guide

Quick guide to run the HK Express Travel Agent demo with beautiful terminal visualization.

## 🚀 Quick Start

### 1. Start Backend (Clean Demo Mode)
```bash
cd /Users/ivanl/Desktop/Development/my-awesome-agent-real
./run_demo.sh
```

You should see:
```
🚀 Starting HK Express Travel Agent API (Demo Mode)
📍 Running on: http://localhost:8000
📄 API Docs: http://localhost:8000/docs

👀 Watch for green INFO messages showing agent reasoning...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2. Start Frontend (Separate Terminal)
```bash
cd /Users/ivanl/Desktop/Development/Cathayhackathon2025
npm run dev
```

### 3. Open Browser
Navigate to: `http://localhost:5173`

---

## 🎯 What You'll See

### In Browser (Frontend):
1. Swipe-based quiz with travel questions
2. Beautiful animations and transitions
3. WanderBox reveal with 3 destinations

### In Terminal (Backend):
```
======================================================================
INFO: User Justin Connected                            <- Green text
======================================================================
INFO: Generating First Question Based on User Background
INFO: First Question Generated: 'What kind of travel...'
======================================================================

----------------------------------------------------------------------
INFO: Justin Selected 'Urban exploration', with hesitation of 1.2s
----------------------------------------------------------------------
INFO: Generating Next Question Based on Past Results
      → Analyzing Justin's choice: 'Urban exploration'  <- Yellow arrow
      → Quick decision detected - strong preference     <- Yellow arrow
INFO: Next Question Generated: 'How do you prefer to...'
----------------------------------------------------------------------
```

**Key Features:**
- ✅ **Green INFO** labels for main agent actions
- ✅ **Yellow arrows (→)** for AI analysis and reasoning
- ✅ **No HTTP request noise** - Clean, focused output
- ✅ **Real-time hesitation analysis** - Shows AI thinking

---

## 🎨 Terminal Colors Explained

| Color | Meaning | Example |
|-------|---------|---------|
| 🟢 Green | INFO - Agent actions | `INFO: Generating Next Question` |
| 🟡 Yellow | Analysis - AI reasoning | `→ Quick decision detected` |
| 🔴 Red | ERROR - Something failed | `ERROR: Planning Failed` |
| ⚪ White | Dividers & structure | `======...` or `------...` |

---

## 📋 Demo Flow Checklist

- [ ] Backend running in one terminal (`./run_demo.sh`)
- [ ] Frontend running in another terminal (`npm run dev`)
- [ ] Browser open to `localhost:5173`
- [ ] Terminal positioned next to browser (split screen recommended)
- [ ] Terminal font size readable for audience

**Split Screen Recommendation:**
```
┌─────────────────────┬─────────────────────┐
│                     │                     │
│   Browser           │   Terminal          │
│   (Frontend UI)     │   (Agent Logs)      │
│                     │                     │
│   localhost:5173    │   ./run_demo.sh     │
│                     │                     │
└─────────────────────┴─────────────────────┘
```

---

## 🗣️ Demo Script

### Introduction (30 seconds)
"Today I'll show you an AI-powered travel recommendation system that adapts to users in real-time. On the left, you'll see the user interface. On the right, you can watch the AI's decision-making process."

### Quiz Phase (1-2 minutes)
1. Start quiz in browser
2. Point to terminal: "See how it detected I connected?"
3. Answer first question
4. Point to terminal: "Notice it's analyzing my hesitation time"
5. Continue answering questions
6. Highlight: "Each question is dynamically generated based on my previous answers"

### Profile Generation (30 seconds)
1. Answer final question
2. Point to terminal: "Now it's building my complete travel profile"
3. Show profile summary statistics in terminal

### Planning Phase (30 seconds)
1. WanderBox opens in browser
2. Point to terminal: "Watch as it matches destinations from the knowledge base"
3. Show 3 recommended destinations
4. Point out: "12 curated experiences for each destination"

### Closing (30 seconds)
"Everything you saw in the terminal is logged to a file for analytics. The AI considered my hesitation patterns, answer choices, and preferences to generate personalized recommendations."

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is already in use
lsof -ti:8000 | xargs kill -9

# Try again
./run_demo.sh
```

### No colored output in terminal
Some terminals don't support ANSI colors. Try:
- macOS Terminal (built-in) ✅
- iTerm2 ✅
- VS Code integrated terminal ✅
- Avoid: Basic SSH terminals ❌

### Still seeing HTTP request logs
Make sure you're using `./run_demo.sh` instead of running uvicorn directly.

---

## 📁 Log Files

All sessions are logged to:
```
output/session_{uuid}.txt
```

Contains:
- Full Q&A history
- Hesitation times
- Generated travel profile
- Planning results with destinations and experiences

---

## 🎓 Technical Details

### What `run_demo.sh` does:
```bash
.conda/bin/uvicorn app.question_api:app \
    --reload \                    # Auto-reload on code changes
    --port 8000 \                 # Run on port 8000
    --log-level warning \         # Hide INFO-level HTTP logs
    --no-access-log              # Disable access logs (127.0.0.1:xxx)
```

### Custom Logging Implementation:
- **File:** `app/question_api.py`
- **Functions:** `print_info()`, `print_analysis()`, `print_error()`
- **ANSI Codes:**
  - Green: `\033[92m`
  - Yellow: `\033[93m`
  - Red: `\033[91m`
  - Reset: `\033[0m`

---

## 📚 Related Files

- `TERMINAL_DEMO_OUTPUT.md` - Full terminal output examples
- `scripts/test_demo_logging.py` - Test script for logging
- `output/README.md` - Session log format documentation
