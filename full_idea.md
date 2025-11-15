
Cathay Hackathon:
Statement: Low-Cost Travel: Digital Travel Experience
> As the only Low-Cost Carrier in Hong Kong, HK Express connects travellers across Asia with affordable, reliable, and joyful journeys. With an increasing customer base, opportunities are growing to make every step of the travel experience - from booking to post-flight - smarter, digital, and more personalized through technology. From understanding travellers' needs using data and Al, to creating seamless and intuitive interfaces, HK Express seeks to make simplicity feel valuable as part of our commitment to great value.

How might we reimagine the digital travel experience to feel effortless, personal, and unexpectedly delightful - using smart technologies and data insights, while staying true to the low-cost travel model?

Our pain point to solve:
Currently, UO have a lot of different ⅔-tier cities destinations. This kind of destination is exclusive to UO, however different user or people may not have a full picture what would it be with this destination
The young new generation would like to have a different experience based travel. And they may betoo lazy to plan or see what they can plan for. So we would plan to create a one-step platform to aid young generation book experience and travel flight together.

The flow:
User would first log into their UO / Cathay Account, which contains their basic information (like age, past flight experience)
We will use a Deep Agent to generate user-based questions, in the format of choosing which experience they would prefer, with a Tinder-like UI, and they can choose with their preference by swiping left and right.
During the progress, we will log down user's final preference, user behaviour (how long they take to hesitate, etc), and passit  into the Deep Agent, allow the Deep Agent to dynamically decide what question to ask next.
When the Deep agent found he is confident with 2 - 3 travel preference that is most suit the user, out of 3X Destination UO provided, with some draft itinerary plan (focused only on mainly experience activity), it will stop the Tinder-type Question and output the 2 - 3 destination with highlight of itinerary experience highlight for each of the destination
After that, we will redirect them into the ticket engine and then further guide them into buying out travel experience after the buying of the flight ticket
After the travel end, we would give them some brief question ask about their interest during this trip and also this kind of data can further go back data insight and construct a more all-around user image.  

1. High-Level Architecture: The Supervisor Loop
The system is controlled by a main Python script, the Supervisor, which is not an LLM. It manages the application state (like the user_profile) and orchestrates the agents in an iterative loop.
The loop follows the "Iterative Discovery and Refinement" model:
Ask (PreferenceAgent): The Supervisor first calls the PreferenceAgent to ask generic preference questions and build an initial user_profile.
Plan (PlannerAgent): The Supervisor then passes the user_profile to the PlannerAgent, which uses RAG tools to find destinations and experiences, generating a concrete plan.
Decide (Supervisor): The Supervisor receives the PlannerAgent's output:
If status: "SUCCESS": The plan is presented to the user. The Supervisor asks for feedback. If the user is satisfied, the loop ends. If not, the feedback is added to the user_profile, and the loop repeats (returning to Step 2).
If status: "CONFLICT": The PlannerAgent couldn't decide. The Supervisor calls the PreferenceAgent (in its "conflict-solver" mode) to ask the user the specific conflict_question (e.g., "Elephants or Hiking?"). The user's answer updates the user_profile, and the loop repeats (returning to Step 2).
2. Detailed Agent Roles
🤖 Agent 1: PreferenceAgent (The "Psychologist")
This agent handles all user-facing dialogue for preference gathering.
Type: LlmAgent (likely using ReAct for advanced questioning).
Job 1: Initial Profiling (First Loop)
Asks 3-5 broad, A/B-style travel preference questions covering the 6 basic categories (Wellness, Shopping, Culture, Food, Nightlife, Nature).
Output: An initial user_profile in paragraph form.
Job 2: Deep Dive (ReAct Sub-agent)
If the user's initial answers are vague, this agent generates customized scenario questions to narrow down their preferences and build a more useful profile for the PlannerAgent.
Job 3: Conflict Resolution (Loopback)
When the PlannerAgent returns a status: "CONFLICT", the Supervisor calls this agent with the specific conflict_question. This agent's sole job is to present that question to the user and return their answer.
🗺️ Agent 2: PlannerAgent (The "Reasoning & RAG Expert")
This agent does not talk to the user. Its only job is to translate the user_profile into a concrete, bookable plan by using RAG tools.
Type: LlmAgent (Tool-use specialist).
Instruction: "You are an expert travel planner. Based on the cumulative user profile in {user_profile}, you must use your retrieval tools to find 3 distinct travel destinations and 4 unique experience offers for each. Reason over the retrieved data (especially the planner_memo and cost_index) to build the best possible plan. Output a plan or a conflict."
Tools:
destination_retriever
experience_retriever
Output (to Supervisor): A JSON object with a status and data.
On Success: { "status": "SUCCESS", "data": [ ...final plan... ] }
On Conflict: { "status": "CONFLICT", "data": { "conflict_question": "..." } }

3. Core RAG & Tooling Architecture
This is the "brain" used by the PlannerAgent. It consists of two RAG indexes and two corresponding tools.
🧠 RAG 1: The Destination Dossier (The "Context")
This RAG holds the "personality" and "logistics" of each destination.
destination_id: (string) THA-CNX
destination_name: (string) "Chiang Mai"
hk_express_destination_type: (string enum) ["Primary-Hub", "2nd-Tier-City"]
one_line_pitch: (string) The "hook" for the agent.
primary_archetype: (string) "The Ethical Adventurer's Hub"
semantic_profile: (string) (Vector Embedding) A rich paragraph describing the "soul" of the city, its ideal traveler, and its feel.
semantic_antiprofile: (string) (Negative Vector) "Do not recommend this city to travelers seeking beaches or high-energy nightlife."
dominant_vibes: (list) ["relaxed", "spiritual", "nature-centric"]
primary_experience_types: (list) ["Ethical-Wildlife", "UNESCO-History"]
cost_index: (int) 1-5
logistics_hub_score: (int) 1-5 (How good is it as a "home base"?)
planner_memo: (string) (Agent Instruction) "A plan for Chiang Mai must be anchored by a major day trip. Prioritize 'Anchor-Event' experiences."
key_dichotomies: (list of objects) Destination-level conflict questions.
📦 RAG 2: The Signature Experience Dossier (The "Product")
This RAG holds the "product" data for each specific, bookable package.
experience_id: (string) CNX-ELE-001
experience_name: (string) "Ethical Elephant Sanctuary Full-Day Experience"
parent_destination_id: (string) THA-CNX
package_type: (string enum) ["Permanent-Tour", "Event-Concert"]
one_line_pitch: (string) The "hook" for this package.
semantic_profile: (string) (Vector Embedding) "This is a life-changing day for animal lovers... you'll prepare their food, feed them, and walk with them to a river..."
semantic_antiprofile: (string) (Negative Vector) "Not for travelers seeking luxury, or who are afraid to get dirty."
primary_preference_tag: (string) "Ethical-Wildlife"
secondary_preference_tags: (list) ["Nature", "Adventure"]
cost_tier: (string enum) ["Budget", "Mid-Range", "Premium"]
duration_type: (string enum) ["Full-Day", "Half-Day (AM)"]
physical_intensity: (int) 1-5
itinerary_role: (string enum) (Critical) ["Anchor-Event", "Secondary-Highlight", "Add-On"]
itinerary_pitch_text: (string) The exact text the agent must use in its final plan.
conflict_solver: (object) (Critical Loopback Data)
competing_experience_ids: (list) ["CNX-TREK-001", "CNX-COOK-001"]
conflict_question: (string) "I've found some amazing full-day trips... are you more excited by... [spending a day connecting with elephants] or [hiking to the highest point in Thailand]?"
planner_memo: (string) (Agent Instruction) "Private note: This is an 'Anchor-Event'. Do not plan other major activities on the same day. Only suggest a relaxing 'Add-On' like a spa."

4. The Merged Workflow in Action
The PlannerAgent is instructed to be "smart" and decide its own tool-use strategy based on the user profile.
Flow A: "Top-Down" (Vibe-First) Search
User Profile: "I like quiet, art, and slow-travel."
PlannerAgent: Sees no "anchor" tag. It will search for a destination first.
Tool Call 1: destination_retriever(query_string="quiet, art, slow-travel")
RAG 1 Returns: [Takamatsu_Dossier]
PlannerAgent: "Great, I have Takamatsu. Now I need experiences."
Tool Call 2: experience_retriever(query_string="quiet, art, slow-travel", destination_id="JPN-TKM")
RAG 2 Returns: [Art_Package_Dossier, Garden_Package_Dossier]
PlannerAgent: Reads all dossiers, sees planner_memo, and builds a plan.
Output to Supervisor: { "status": "SUCCESS", "data": [Takamatsu_Plan] }
Flow B: "Bottom-Up" (Experience-First) Search
User Profile: "I want to see a K-Pop concert in a 2nd-tier city and I'm budget-conscious."
PlannerAgent: Sees an "anchor" tag ("K-Pop concert"). It will search for the experience first.
Tool Call 1: experience_retriever(query_string="K-Pop concert, 2nd-tier city, budget")
RAG 2 Returns: [Fukuoka_Concert_Dossier, Osaka_Concert_Dossier]
PlannerAgent: "I have two packages. I need their destination context." It reads their parent_destination_ids (JPN-FUK, JPN-OSA).
Tool Call 2: destination_retriever(destination_ids=["JPN-FUK", "JPN-OSA"])
RAG 1 Returns: [Fukuoka_Dossier, Osaka_Dossier]
PlannerAgent: Reasons over all data: "User is budget-conscious. Fukuoka_Dossier.cost_index is 3, Osaka_Dossier.cost_index is 4. Fukuoka is the stronger match."
Output to Supervisor: { "status": "SUCCESS", "data": [Fukuoka_Plan] }
Flow C: The "Conflict-Solver" Loopback
User Profile: "I want an amazing full-day adventure in Chiang Mai."
PlannerAgent: Calls experience_retriever and gets two strong, competing "Anchor-Event" matches: CNX-ELE-001 (Elephants) and CNX-TREK-001 (Hiking). It cannot decide which to build the plan around.
PlannerAgent: It inspects the conflict_solver field in CNX-ELE-001.
Output to Supervisor: { "status": "CONFLICT", "data": { "conflict_question": "I've found some amazing full-day trips... are you more excited by... [spending a day connecting with elephants] or [hiking to the highest point in Thailand]?" } }
Supervisor: Receives this and calls the PreferenceAgent with the conflict question.
User: "Elephants!"
Supervisor: Updates user_profile to include "prefers elephants."
Supervisor: Calls PlannerAgent again. This time, the user_profile is so specific that the PlannerAgent's RAG search returns CNX-ELE-001 as the #1 match, and it confidently builds the plan.
Output to Supervisor: { "status": "SUCCESS", "data": [Elephant_Plan] }

Data Feedback Loop:
During our process, there are a lot of different point of data received and all of them can be used into improve our user profile, destination profile, experience profile and also the Deep Agent itself
