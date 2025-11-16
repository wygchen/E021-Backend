# RAG Engine Demo Output - Visual Example

## 🎨 New Improved Output

### Before vs After Comparison

#### ❌ **OLD OUTPUT** (Messy and Hard to Read)
```
🔍 Destination Search Results for: 'User travel profile based on answers: Relaxing beach vacation? / Exploring historical cities? -> A (1.2s); Boutique hotels with character? / Modern, all-inclusive resorts? -> B (1.8s); Beachfront restaurants and seafood / Exploring local culture and history -> B (7.6s); Immersive local experiences and activities / Superficial sightseeing and shopping -> A (5.9s); Learn the language, traditions and customs / Just see the main historical landmarks -> all good (1.5s); Active tours: hiking, biking, exploring ruins / Leisurely museums, workshops, local performances -> A (134.3s); Budget-friendly: Hostels and local eateries / Luxury: Upscale hotels and fine dining -> A (0.8s); Challenging multi-day treks or hikes / Easy-paced walks exploring local markets -> A (1.0s); Detailed daily itinerary, pre-booked activities? / Go with the flow, decide as you go? -> B (1.1s)'
  1. Hualien (ID: HUN) - Score: 0.447
  2. Ishigaki (ID: ISG) - Score: 0.427
  3. Changzhou (ID: CZX) - Score: 0.424
```

#### ✅ **NEW OUTPUT** (Clean and Professional)
```
🔍 RAG: Destination Search                                    <- Cyan
   Preferences: A, B, B...                                     <- Yellow (smart extraction)
   → Top 3 Destinations:                                       <- Green arrow
      1. Hualien (HUN) - Score: 0.447                         <- Green score (>0.4)
      2. Ishigaki (ISG) - Score: 0.427                        <- Green score
      3. Changzhou (CZX) - Score: 0.424                       <- Green score

🎯 RAG: Experience Search for HUN                              <- Magenta
   Preferences: A, B, B...                                     <- Yellow
   → Top 7 Experiences:                                        <- Green arrow
      1. Mugua River "River Tracing" Adventure (HUN-RIVER-005) - Score: 0.402  <- Yellow (0.35-0.45)
      2. Taroko "Zhuilu Old Trail" Hiking Permit Package (HUN-HIKE-002) - Score: 0.397
      3. Qixingtan Beach & "Dongdamen" Night Market Tour (HUN-NIGHT-007) - Score: 0.397
      4. Qingshui Cliff "Sunrise Kayak" Tour (HUN-KAYAK-003) - Score: 0.393
      5. Whale & Dolphin Watching Boat Tour (HUN-WHALE-004) - Score: 0.381
      6. "Amis" (Indigenous) Cultural Village & Performance (HUN-AMIS-006) - Score: 0.375
      7. Hualien "Stone-Art" Carving Workshop (HUN-ART-009) - Score: 0.369
```

---

## 🎨 Color Coding

| Element | Color | Purpose |
|---------|-------|---------|
| **🔍 RAG: Destination Search** | Cyan | Destination retrieval header |
| **🎯 RAG: Experience Search** | Magenta | Experience retrieval header |
| **Preferences/Query** | Yellow | User query/preferences |
| **→ Top N Results** | Green | Results section header |
| **Score > 0.45 (Experiences)** | Green | High relevance match |
| **Score > 0.40 (Destinations)** | Green | High relevance match |
| **Score > 0.35** | Yellow | Medium relevance match |
| **Score < 0.35** | White | Lower relevance match |

---

## 🧠 Smart Query Extraction

The system now intelligently extracts key preferences from verbose user profiles:

### Input Query:
```
User travel profile based on answers: Relaxing beach vacation? / Exploring historical cities? -> A (1.2s); Boutique hotels with character? / Modern, all-inclusive resorts? -> B (1.8s); Beachfront restaurants and seafood / Exploring local culture and history -> B (7.6s)...
```

### Displayed As:
```
Preferences: A, B, B...
```

This makes it immediately clear what preferences are being searched without cluttering the terminal.

---

## 📊 Full Demo Flow Example

When the Experience Planner runs, you'll see:

```
🔍 RAG: Destination Search
   Preferences: Relaxing beach vacation, Modern resorts, Exploring local culture...
   → Top 3 Destinations:
      1. Hualien (HUN) - Score: 0.447
      2. Ishigaki (ISG) - Score: 0.427
      3. Changzhou (CZX) - Score: 0.424

🎯 RAG: Experience Search for HUN
   Preferences: Relaxing beach vacation, Modern resorts, Exploring local culture...
   → Top 7 Experiences:
      1. Mugua River "River Tracing" Adventure (HUN-RIVER-005) - Score: 0.402
      2. Taroko "Zhuilu Old Trail" Hiking Permit Package (HUN-HIKE-002) - Score: 0.397
      3. Qixingtan Beach & "Dongdamen" Night Market Tour (HUN-NIGHT-007) - Score: 0.397
      4. Qingshui Cliff "Sunrise Kayak" Tour (HUN-KAYAK-003) - Score: 0.393
      5. Whale & Dolphin Watching Boat Tour (HUN-WHALE-004) - Score: 0.381
      6. "Amis" (Indigenous) Cultural Village & Performance (HUN-AMIS-006) - Score: 0.375
      7. Hualien "Stone-Art" Carving Workshop (HUN-ART-009) - Score: 0.369

🎯 RAG: Experience Search for ISG
   Preferences: Relaxing beach vacation, Modern resorts, Exploring local culture...
   → Top 7 Experiences:
      1. Sunrise "Mangrove" Kayaking/SUP Tour (ISG-KAYAK-009) - Score: 0.425
      2. "Dark Sky" Preserve Stargazing & Photo Tour (ISG-STAR-006) - Score: 0.401
      3. Yaeyama Islands "Island-Hopper" Passport (ISG-ISLAND-002) - Score: 0.392
      4. Taketomi Island "Ryukyu Heritage" Package (ISG-HERITAGE-003) - Score: 0.392
      5. Kabira Bay "Black Pearl" Glass-Bottom Boat Tour (ISG-PEARL-005) - Score: 0.381
      6. "Gourmet" Ishigaki Salt & Spice Tour (ISG-GOURMET-010) - Score: 0.372
      7. Manta Ray "Guaranteed" Scuba/Snorkel Expedition (ISG-MANTA-001) - Score: 0.369

🎯 RAG: Experience Search for CZX
   Preferences: Relaxing beach vacation, Modern resorts, Exploring local culture...
   → Top 7 Experiences:
      1. Oriental Salt Lake City "Zen Retreat" Package (CZX-ZEN-003) - Score: 0.414
      2. Grand Canal "Night Cruise" Package (CZX-CRUISE-007) - Score: 0.389
      3. Hongmei Park & Museum Day (CZX-PARK-008) - Score: 0.369
      4. Taihu Lake Liyang "Bamboo Sea" Day Trip (CZX-BAMBOO-010) - Score: 0.365
      5. CC-JOYLAND Anime Kingdom (CZX-ANIME-006) - Score: 0.363
      6. Chunqiu Yancheng "Ancient Kingdom" Tour (CZX-KINGDOM-005) - Score: 0.361
      7. Jing'an 18-Block "Foodie" Tour (CZX-FOOD-009) - Score: 0.358
```

---

## 🚀 Benefits

1. **Readability**: Clear visual hierarchy with icons and colors
2. **Conciseness**: Smart query extraction shows only key info
3. **Score Visibility**: Color-coded scores show match quality at a glance
4. **Professional**: Looks polished for demos and presentations
5. **Scannable**: Easy to quickly identify top matches

---

## 🔧 Technical Implementation

### Files Modified:
- `RAG/rag_retriever.py`

### Key Changes:
1. Added `Colors` class for ANSI color codes
2. Added `_format_query_for_display()` helper function
3. Updated destination search output formatting
4. Updated experience search output formatting
5. Added color-coded relevance scores
6. Smart query truncation/extraction

### Color Thresholds:
- **Destinations**: Green if score > 0.40, Yellow if > 0.35
- **Experiences**: Green if score > 0.45, Yellow if > 0.35
- Shows top relevance matches clearly
