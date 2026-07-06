# FENS 2026 Program Website — Specification

## 1. Source Data

`program.txt` contains the full FENS 2026 conference program (49,269 lines).

### Structure

**Monday, July 6** — Pre-conference day
- Special Interest Events (SiE)
- Technical Workshops (W)
- Special Lecture (SL)
- Brain Debate
- Opening Ceremony
- Plenary Lecture (PL)
- Networking Events (NE)

**Tuesday–Friday (July 7–10)** — Main conference days
Each day is structured as:
1. **Poster Sessions** (09:30–13:00 and 14:00–17:30)
   - Multiple concurrent sessions with different themes
   - Each session contains individual posters with ID, title, presenter, location
2. **Plenary Lectures** (morning/evening)
3. **Scientific Symposia** (S) — morning and afternoon blocks
4. **Special Interest Events** (SiE)
5. **Special Lectures** (SL)
6. **Networking Events** (NE)

### Poster Session Layout
```
Poster Sessions
09:30 - 13:00
POSTER AREA
Poster Session 01 - Theme Name
PS01-07AM-001
POSTER TITLE (may span multiple lines)
09:30 - 09:30
Poster Presenter: Name (Location)
```

### Non-Poster Event Layout
```
Event Type (e.g. Scientific Symposia (S))
Time Range
LOCATION HALL
Event Title
Chair: Name (Location)
Introduction
Time
Talk Title (may span multiple lines)
Time
Speaker: Name (Location)
...
```

## 2. JSON Schema

```json
{
  "conference": "FENS 2026",
  "days": [
    {
      "day": "Monday",
      "date": "July 6, 2026",
      "events": [
        {
          "type": "ScientificSymposia|PosterSession|PlenaryLecture|SpecialInterestEvents|TechnicalWorkshop|SpecialLecture|BrainDebate|OpeningCeremony|NetworkingEvents",
          "title": "S01 - Full Session Title",
          "time": "10:00 - 12:00",
          "location": "HALL A",
          "chairs": ["Name (Location)"],
          "talks": [
            {
              "time": "10:00 - 10:06",
              "title": "Talk Title",
              "speaker": "Speaker Name",
              "location": "Speaker Location"
            }
          ],
          "session_name": "Poster Session 01 - Theme Name",
          "posters": [
            {
              "id": "PS01-07AM-001",
              "title": "POSTER TITLE",
              "presenter": "Name",
              "location": "Location",
              "time": "09:30 - 09:30"
            }
          ]
        }
      ]
    }
  ]
}
```

## 3. Website Features

### Layout
- **Day tabs** (Mon–Fri) to switch between days
- Each day shows events chronologically

### Interactive Features
1. **Starring / highlighting**
   - Star icons on: talks, poster sessions, individual posters
   - Toggle star by clicking
   - Stars persist in `localStorage`
   - Starred items highlighted with a distinctive color

2. **Search**
   - Search box searches through:
     - Poster titles
     - Talk titles
     - Author/presenter names
   - Real-time filtering as user types

3. **Filter by starred**
   - Toggle to show only starred/highlighted items
   - Works together with search

4. **Checkboxes**
   - Checkbox per poster for marking as "visited" or "attended"
   - Checkboxes persist in `localStorage`

### Visual Design
- Clean, minimal, mobile-friendly
- Dark mode support (prefers-color-scheme)
- Monospace font for code-like elements
- Expandable/collapsible sections
- Color-coded event types

## 4. Implementation

- **Parser**: Python script → `program.json`
- **Frontend**: Single `index.html` with embedded CSS + JS
- **No dependencies**: Vanilla JS, no frameworks, no external CSS
- **localStorage keys**: `fens2026_stars` and `fens2026_checks` (JSON maps)
