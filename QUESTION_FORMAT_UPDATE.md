# Question Format Update - Concise Choices

## Summary
Updated the QuestionGeneratorAgent to generate **short, scannable questions** with maximum 10 words per choice, making it easier for users to decide quickly.

## Changes Made

### 1. LLM Prompt Enhancement
**File**: `app/question_generator.py`

Added strict requirements:
- Each choice MUST be 10 words or less
- Use short, punchy language
- Easy to understand at a glance

### 2. Examples Added to Prompt
Provided concrete examples of good short choices:
```json
"choices": ["Luxury hotels with full amenities", "Budget hostels and local guesthouses"]
"choices": ["Action-packed itinerary visiting multiple sites daily", "Relaxed pace with plenty of downtime"]
"choices": ["Street food and local markets", "Fine dining and Michelin-starred restaurants"]
"choices": ["Solo travel for personal freedom", "Group tours with social interaction"]
```

### 3. Updated Default Questions
Shortened all default fallback questions to match the new format:
- ❌ Before: "Visiting museums, historical landmarks, and cultural sites"
- ✅ After: "Museums, landmarks, and cultural sites"

## Results

### Before (Verbose)
```
When you travel, do you prefer a jam-packed itinerary where you're seeing 
and doing as much as possible each day, like visiting multiple museums, 
attending several tours, and trying a new restaurant every meal (Option A)?

Or do you prefer a more relaxed pace with plenty of downtime, like lingering 
in cafes, revisiting favorite spots, and only having one or two planned 
activities per day (Option B)?
```

### After (Concise)
```
🤖 Agent Question #1:
   A) Museums, historical sites and local culture?
   B) Hiking, beaches, and outdoor adventures?

🤖 Agent Question #2:
   A) Structured itinerary with pre-booked activities?
   B) Go with the flow, decide on the spot?

🤖 Agent Question #3:
   A) Boutique hotels and unique stays?
   B) Budget-friendly hostels/guesthouses?
```

## Benefits

1. ✅ **Faster Decision Making** - Users can scan and answer in seconds
2. ✅ **Mobile Friendly** - Short text fits better on small screens
3. ✅ **Better UX** - Less cognitive load, clearer choices
4. ✅ **Maintained Depth** - Still covers all travel dimensions (7-10 questions)
5. ✅ **LLM-Driven** - Questions remain personalized based on user history

## Testing

Run the terminal interface:
```bash
python run_agent_simple.py
```

Or use the Question API:
```bash
uvicorn app.question_api:app --reload
# Then visit http://localhost:8000/docs
```

## Technical Details

- **Minimum questions**: 7
- **Maximum questions**: 10
- **Word limit per choice**: 10 words
- **Profile generation**: 4-6 sentences covering all major dimensions
- **Hesitation tracking**: Still analyzes response times to detect uncertainty
