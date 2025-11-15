# 🚀 The Full Hackathon Plan: The "Hybrid AI Planner"

This plan outlines a sophisticated, multi-agent system that intelligently uses a "Dual-Brain" RAG to build deeply personalized travel plans, moving beyond simple tag-matching to true AI-driven reasoning.

---

## 1. 🏛️ The Core Architecture: The 3-Agent Supervisor

Your system is built on a "Supervisor" model, which is the gold standard for complex agentic workflows.

### SupervisorAgent (The "Conductor" - Your Main Code)
This is not an LLM. This is your main Python (or Node.js) script that runs the entire process.
- It holds the "master state" (like `user_profile`).
- It calls the other agents in order, gets their responses, and decides what to do next (e.g., call the Planner, or loop back to the Psychologist).

### FastPsychologistAgent (The "Social" LLM)
- **Job 1 (Initial Loop):** Asks broad, non-RAG questions (e.g., "Beach vs. Mountain?") to build the initial `user_profile` (the 8+ questions).
- **Job 2 (Loopback):** When the `PlannerAgent` gets stuck, the Supervisor calls this agent with a specific conflict question (e.g., "Elephants vs. Hiking?").

### PlannerAgent (The "Reasoning" LLM)
This is your "smartest" agent. It does not store data.
- Its only job is to use tools (`destination_retriever`, `experience_retriever`) to get data, reason over that data, and output a final plan or a conflict question.

---

## 2. 🧠 The RAG Design: The "Dual-Brain" Database

Your "database" is two comprehensive RAG indexes. One for "Context" (Destinations) and one for "Products" (Experiences).

### RAG 1: The Destination Dossier (The "Context")
This RAG holds the "personality" and "logistics" of the destination.

#### Core Identity
- `destination_id`: (string) Unique ID (e.g., `THA-CNX`).
- `destination_name`: (string) (e.g., "Chiang Mai").
- `hk_express_destination_type`: (string enum) `["Primary-Hub", "2nd-Tier-City", "Leisure-Resort"]`.

#### Pitch & Archetype
- `one_line_pitch`: (string) The "hook" for the agent.
- `primary_archetype`: (string) A "personality" label (e.g., "The Ethical Adventurer's Hub").

#### Semantic Profile (For Vector RAG Embedding)
- `semantic_profile`: (string) The core vector. A rich paragraph describing the "soul" of the city, its ideal traveler, and its feel (e.g., "Chiang Mai is for the traveler who wants a slower pace, spirituality, and a deep connection with nature...").
- `semantic_antiprofile`: (string) A negative match vector. (e.g., "Do not recommend this city to travelers seeking beaches or high-energy nightlife...").

#### Structured Tags (For Agent Logical Filtering)
- `dominant_vibes`: (list) `["relaxed", "spiritual", "nature-centric", "foodie"]`.
- `primary_experience_types`: (list) (Key link to RAG 2) `["Ethical-Wildlife", "UNESCO-History", "Nature-Trekking", "Music-Event"]`.

#### Practical & Logistic Profile (For Agent Logic)
- `cost_index`: (int) 1-5.
- `logistics_hub_score`: (int) 1-5. (e.g., Chiang Mai is 5/5, a perfect "home base" for day trips).
- `transport_profile`: (list) `["Ride-hailing (Grab)", "Extensive-Subway-System"]`.

#### Agent Control & Loopback (For Agent Logic)
- `planner_memo`: (string) A "private note" to the `PlannerAgent` (e.g., "A plan for Chiang Mai must be anchored by a major day trip...").
- `key_dichotomies`: (list of objects) The loopback questions for destination-level conflicts.

### RAG 2: The Signature Experience Dossier (The "Product")
This RAG holds the "product" data for each specific, bookable package.

#### Core Identity & Product Details
- `experience_id`: (string) Unique Product ID (e.g., `CNX-ELE-001`).
- `experience_name`: (string) (e.g., "Ethical Elephant Sanctuary Full-Day Experience").
- `parent_destination_id`: (string) Foreign key to RAG 1 (e.g., `THA-CNX`).
- `package_type`: (string enum) `["Permanent-Tour", "Event-Concert", "Seasonal-Tour"]`.

#### Pitch & Profile (For Vector RAG Embedding)
- `one_line_pitch`: (string) The "hook" for this package.
- `semantic_profile`: (string) The primary vector for this package. (e.g., "This is a life-changing day for animal lovers... you'll prepare their food, feed them, and walk with them to a river and mud pit for a bath...").
- `semantic_antiprofile`: (string) (e.g., "Not for travelers seeking luxury, or who are afraid to get dirty...").

#### Structured Tags (For Agent Logical Filtering)
- `primary_preference_tag`: (string) `["Ethical-Wildlife", "K-Pop", "UNESCO-History"]`.
- `secondary_preference_tags`: (list) `["Nature", "Adventure", "High-Energy", "Music"]`.
- `vibe_tags`: (list) `["heartwarming", "muddy", "joyful", "loud", "crowded", "tense"]`.

#### Practical & Logistic Profile (For Agent Logic)
- `cost_tier`: (string enum) `["Budget", "Mid-Range", "Premium"]`.
- `duration_type`: (string enum) `["Full-Day", "Half-Day (AM)", "Evening-Event"]`.
- `physical_intensity`: (int) 1-5.
- `logistics_model`: (string enum) `["All-Inclusive (Hotel Pickup)", "Ticket-Only"]`.
- `package_inclusions`: (list) `["Round-trip Transport", "Concert Ticket (S-Rank)"]`.
- `booking_lead_time_warning`: (string enum) `["None", "Book 3-months-adv (Events)"]`.

#### Event-Specific Data (For Agent Logic)
- `event_details`: (object, null if not an event)

#### Agent Control & Loopback (For Agent Logic)
- `itinerary_role`: (string enum) This is critical. `["Anchor-Event", "Secondary-Highlight", "Add-On"]`.
- `itinerary_pitch_text`: (string) The exact text the agent must use in its final plan.
- `hesitation_analyzer`: (object) A "cheat sheet" (e.g., `{"hesitated_on_luxury": "red_flag", "hesitated_on_adventure": "green_flag"}`).
- `conflict_solver`: (object) The data for the loopback.
- `competing_experience_ids`: (list) `["CNX-TREK-001", "CNX-COOK-001"]`.
- `conflict_question`: (string) "I've found some amazing full-day trips... are you more excited by... [spending a day connecting with elephants] or [hiking to the highest point in Thailand]?"
- `upsell_opportunity_ids`: (list) `["CNX-SPA-001"]`.
- `planner_memo`: (string) "Private note to the agent: This is an 'Anchor-Event'... Do not plan any other major activities. Only suggest a relaxing 'Add-On'..."

---

## 3. 📞 The RAG Interface: The "Retrieval-as-a-Tool" Model

Your `PlannerAgent` does not get the whole database in its prompt. It calls these tools, which are your "Simulated RAG."

### `destination_retriever` Tool
```python
def destination_retriever(query_string: str = None, destination_ids: list[str] = None) -> list[dict]:
```
- **Logic:**
    - If `query_string` is provided (for "Top-Down" search), this tool runs a semantic search on the `semantic_profile` field in RAG 1.
    - If `destination_ids` is provided (for "Bottom-Up" search), this tool does a simple lookup by ID.
- **Returns:** A list of the full JSON dossiers for the top 2-3 matches.

### `experience_retriever` Tool
```python
def experience_retriever(query_string: str, destination_id: str = None) -> list[dict]:
```
- **Logic:**
    - It always uses the `query_string` for a semantic search on the `semantic_profile` in RAG 2.
    - If `destination_id` is provided, it pre-filters the search to only that destination.
- **Returns:** A list of the full JSON dossiers for the top 5-7 matching packages.

---

## 4. ⚙️ The Full Workflow: How the Agents "Think"

Your `PlannerAgent`'s prompt instructs it to use these tools. The `SupervisorAgent` just kicks it off.

### Flow A: "Top-Down" (Vibe-First) Search
1. **User Profile:** "I like quiet, art, and slow-travel."
2. `PlannerAgent` is called. Its prompt tells it to call `destination_retriever` first.
3. **Tool Call 1:** `destination_retriever(query_string="quiet, art, slow-travel")`
4. **Tool (RAG 1):** Performs semantic search. Returns `[Takamatsu_Dossier]`.
5. **`PlannerAgent`:** "Great, I have Takamatsu. Now I need experiences."
6. **Tool Call 2:** `experience_retriever(query_string="quiet, art, slow-travel", destination_id="JPN-TKM")`
7. **Tool (RAG 2):** Performs semantic search within Takamatsu. Returns `[Art_Package_Dossier, Garden_Package_Dossier]`.
8. **`PlannerAgent`:** "I have all my context." It reads the 3 retrieved dossiers, checks the `planner_memo`, and builds a plan.
9. **Output:** `status: "SUCCESS"` with the final plan.

### Flow B: "Bottom-Up" (Experience-First) Search
1. **User Profile:** "I want to see a K-Pop concert in a 2nd-tier city and I'm budget-conscious."
2. `PlannerAgent` is called. Its prompt tells it to check for "anchor" tags first. It sees `K-Pop`.
3. **Tool Call 1:** `experience_retriever(query_string="K-Pop concert, 2nd-tier city, budget-conscious")`
4. **Tool (RAG 2):** Performs semantic search. Returns `[Fukuoka_Concert_Dossier, Osaka_Concert_Dossier]`.
5. **`PlannerAgent`:** "I have two packages. I need their destination context." It reads their `parent_destination_ids` (`JPN-FUK`, `JPN-OSA`).
6. **Tool Call 2:** `destination_retriever(destination_ids=["JPN-FUK", "JPN-OSA"])`
7. **Tool (RAG 1):** Performs a simple lookup. Returns `[Fukuoka_Dossier, Osaka_Dossier]`.
8. **`PlannerAgent`:** "I have all my context." It now reasons: "The user is budget-conscious. The `Fukuoka_Dossier` `cost_index` is 3, but the `Osaka_Dossier` is 4. Fukuoka is the stronger match."
9. **Output:** `status: "SUCCESS"` with the Fukuoka plan as the primary recommendation.

### Flow C: The "Conflict-Solver" Loopback
1. ...`PlannerAgent` is reasoning. It has 2 strong packages: `CNX-ELE-001` (Elephants) and `CNX-TREK-001` (Hiking). It can't decide.
2. `PlannerAgent` checks the `conflict_solver` field in `CNX-ELE-001`.
3. **Output:** `status: "CONFLICT"` with the `conflict_question` string: "Are you more excited by... [elephants] or [hiking]?"
4. `SupervisorAgent` (Your main code) catches this status. It does not show it to the user.
5. `SupervisorAgent` calls the `FastPsychologistAgent` with the `conflict_question`.
6. **User answers:** "Elephants!"
7. `SupervisorAgent` updates the `user_profile` (now with "Elephants").
8. `SupervisorAgent` calls the `PlannerAgent` again.
9. This time, the `PlannerAgent`'s search is so specific ("Elephants") that it finds a perfect match and outputs `status: "SUCCESS"`.

---

## 5. 🛠️ Your Hackathon "Simulated RAG" Action Plan

Here is your practical to-do list for the hackathon.

### Step 1: Create Your "Database" (The JSON Files)
- Create two files: `destination_db.json` and `experience_db.json`.
- **Hackathon Tip:** You do not need 100 entries. You need just enough to tell a story.
    - 2-3 Destinations (e.g., Chiang Mai, Fukuoka)
    - 5-7 Experiences (e.g., Elephants, Trekking, Fukuoka Concert, Tokyo Concert, DMZ Tour). Make sure you have competing packages (e.g., Elephant vs. Trekking) so you can show the loopback.
- Painstakingly fill out every single field in the schemas we designed for these 7-10 entries. The quality of this data is what makes the demo work.

### Step 2: Write Your "Retrieval Tools" (The Python Functions)
- Write the two Python functions: `destination_retriever` and `experience_retriever`.
- These functions will simply `import json` and `load()` your `_db.json` files.
- **The "Simulated Semantic Search" Hack:** For the demo, you don't need a real vector DB. Your "semantic search" can be a simple `for` loop that checks if keywords from the `query_string` are in the `semantic_profile` string. This perfectly simulates the architecture of RAG, which is all that matters.

### Step 3: Write Your LLM Prompts (The "Brains")
- Create 3 text files for your prompts:
    - `fast_psychologist_prompt.txt` (The general question-asker)
    - `planner_agent_prompt.txt` (The main "foreman" prompt that instructs the agent to call tools)
    - `loopback_prompt.txt` (The simple "ask this conflict question" prompt)

### Step 4: Build Your `SupervisorAgent` (The Main App)
This is your main script.
- **Flow:**
    1. Call `FastPsychologistAgent` (with `fast_psychologist_prompt`) 8 times in a loop, building your `user_profile`.
    2. Call `PlannerAgent` (with `planner_agent_prompt` and the `user_profile`).
    3. Provide your tools (`destination_retriever`, `experience_retriever`) to the agent (e.g., via the `tools` parameter in the Gemini API).
    4. The LLM will "think," call your tools (your Python functions will run), and then "think" again.
    5. It will finally return a JSON object: `{"status": "...", "data": "..."}`.
    6. `if output.status == "SUCCESS":` Show the plan to the user. You win.
    7. `if output.status == "CONFLICT":` Go to Step 8.
    8. Call `FastPsychologistAgent` (with `loopback_prompt` and the `conflict_question`).
    9. Get the user's final answer, add it to the `user_profile`, and go back to Step 2.