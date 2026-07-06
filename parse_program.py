#!/usr/bin/env python3
import json
import re

with open("program.txt", "r", encoding="utf-8") as f:
    lines = f.read().splitlines()

# Strip trailing whitespace, keep blank lines as empty strings
# but we need the original line numbers for debugging

# Step 1: identify day boundaries
day_pattern = re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday), (July \d+, 2026)$")
days = []  # list of (day_name, date, start_line_index)
for i, line in enumerate(lines):
    m = day_pattern.match(line)
    if m:
        days.append((m.group(1), m.group(2), i))

# Append a sentinel
days.append(("END", "", len(lines)))

print(f"Found {len(days)-1} days")

EVENT_TYPES = [
    "Poster Sessions",
    "Plenary Lecture (PL)",
    "Scientific Symposia (S)",
    "Special Interest Events (SiE)",
    "Technical Workshop (W)",
    "Special Lecture (SL)",
    "Brain Debate",
    "Opening Ceremony",
    "Networking Events (NE)",
    "Thematic Poster Session",
    "FENS Forum Debate",
    "Industry Session",
    "Career Session",
    "Meet the Expert",
]

def is_event_header(line):
    """Check if a line is a section header."""
    stripped = line.strip()
    if not stripped:
        return False
    # Poster Sessions
    if stripped == "Poster Sessions":
        return True
    if stripped.startswith("Poster Session ") and " - " in stripped:
        return True
    # Other event types
    for et in EVENT_TYPES:
        if et in ["Poster Sessions"]:
            continue
        if stripped.startswith(et):
            return True
    return False

def is_time_range(s):
    """Check if a string looks like HH:MM - HH:MM"""
    return bool(re.match(r'^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}$', s.strip()))

def is_poster_id(s):
    return bool(re.match(r'^PS\d{2}-\d{2}(AM|PM)-\d{3}$', s.strip()))

def is_presenter_line(s):
    return s.strip().startswith("Poster Presenter:")

def is_speaker_line(s):
    return s.strip().startswith("Speaker:")

def is_chair_line(s):
    return s.strip().startswith("Chair:")

def is_hall_line(s):
    s = s.strip()
    return s in ["HALL A", "HALL B", "HALL C", "HALL D", "HALL E", "HALL F", "HALL G", "HALL H",
                  "HALL I", "HALL J", "HALL K", "HALL L", "POSTER AREA",
                  "ROUNDTABLE HALL", "POSTER AREA"]

def parse_program():
    output = {
        "conference": "FENS 2026",
        "days": []
    }

    for di in range(len(days) - 1):
        day_name, day_date, start = days[di]
        end = days[di + 1][2]

        day_lines = lines[start:end]
        print(f"\n--- {day_name} ({day_date}) --- lines {start}-{end} ({len(day_lines)} lines)")

        events = []
        i = 0
        while i < len(day_lines):
            line = day_lines[i].strip()

            # Skip empty lines and the day header
            if not line or line == f"{day_name}, {day_date}":
                i += 1
                continue

            # Detect event sections
            # First, try to detect the main section headers

            # Check for Poster Sessions header
            if line == "Poster Sessions":
                i += 1
                # Next non-empty line should be time range
                while i < len(day_lines) and not day_lines[i].strip():
                    i += 1
                time_range = ""
                if i < len(day_lines) and is_time_range(day_lines[i]):
                    time_range = day_lines[i].strip()
                    i += 1

                # Skip empty lines until POSTER AREA or session name
                while i < len(day_lines) and not day_lines[i].strip():
                    i += 1

                location = ""
                if i < len(day_lines) and day_lines[i].strip() == "POSTER AREA":
                    location = "POSTER AREA"
                    i += 1

                # Now parse all poster sessions under this "Poster Sessions" header
                # There can be multiple sessions (e.g., "Poster Session 01 - ...")
                # until we hit a non-poster section header or a different main section

                current_session = None

                while i < len(day_lines):
                    l_raw = day_lines[i]
                    l = l_raw.strip()

                    # Skip empty lines
                    if not l:
                        i += 1
                        continue

                    # Check if we hit a new Poster Sessions block (should not happen nested, but safety)
                    if l == "Poster Sessions":
                        break

                    if l.startswith("Thematic Poster Session"):
                        current_session = {
                            "type": "PosterSession",
                            "time": time_range,
                            "location": "POSTER AREA",
                            "session_name": l,
                            "posters": []
                        }
                        events.append(current_session)
                        i += 1
                        continue

                    # Check for Poster Session 0X - Theme
                    m = re.match(r'^(Poster Session \d+ - .+)', l)
                    if m and not is_poster_id(l):
                        current_session = {
                            "type": "PosterSession",
                            "time": time_range,
                            "location": location,
                            "session_name": l,
                            "posters": []
                        }
                        events.append(current_session)
                        i += 1
                        continue

                    # Check if this is a new non-poster section header
                    if is_event_header(l) and l != "Poster Sessions" and not l.startswith("Poster Session "):
                        break

                    # Try to parse a poster entry (by poster ID)
                    if is_poster_id(l):
                        # Create session on demand if needed
                        if current_session is None:
                            current_session = {
                                "type": "PosterSession",
                                "time": time_range,
                                "location": location,
                                "session_name": f"Poster Session at {time_range}",
                                "posters": []
                            }
                            events.append(current_session)
                        poster = parse_poster(day_lines, i)
                        if poster:
                            current_session["posters"].append(poster)
                            i = poster["_end_line"] + 1
                            continue

                    # Skip everything else
                    i += 1

                continue  # outer loop continues

            # Non-poster events
            # Detect by matching event type headers
            matched_type = None
            for et in EVENT_TYPES:
                if et == "Poster Sessions":
                    continue
                if line.startswith(et):
                    matched_type = et
                    break

            if matched_type:
                event = parse_non_poster_event(day_lines, i, matched_type)
                if event:
                    events.append(event)
                    i = event["_end_line"] + 1
                    continue
                else:
                    i += 1
                    continue

            # Special cases: Brain Debate and Opening Ceremony
            if line.startswith("Brain Debate") or line.startswith("Brain Debate:"):
                event = parse_non_poster_event(day_lines, i, "Brain Debate")
                if event:
                    events.append(event)
                    i = event["_end_line"] + 1
                    continue
                i += 1
                continue

            if line.startswith("Opening Ceremony"):
                event = parse_non_poster_event(day_lines, i, "Opening Ceremony")
                if event:
                    events.append(event)
                    i = event["_end_line"] + 1
                    continue
                i += 1
                continue

            i += 1

        output["days"].append({
            "day": day_name,
            "date": day_date,
            "events": events
        })

    return output

def parse_poster(day_lines, start_idx):
    """Parse a single poster entry starting at start_idx (which is the poster ID line)."""
    result = {
        "_end_line": start_idx
    }

    i = start_idx
    poster_id = day_lines[i].strip()
    result["id"] = poster_id
    i += 1

    # Collect title lines (all caps or mixed case, before the time line)
    title_lines = []
    while i < len(day_lines):
        l = day_lines[i]
        if is_time_range(l):
            result["time"] = l.strip()
            i += 1
            break
        if is_presenter_line(l):
            # No time found, but we hit presenter
            break
        if l.strip():
            title_lines.append(l.strip())
        i += 1

    result["title"] = " ".join(title_lines).strip()

    # Skip empty lines until presenter
    while i < len(day_lines):
        l = day_lines[i].strip()
        if is_presenter_line(l):
            # Parse "Poster Presenter: Name (Location)"
            rest = l[len("Poster Presenter:"):].strip()
            # Try to extract name and location
            m = re.match(r'^(.+?)\s+\((.+)\)$', rest)
            if m:
                result["presenter"] = m.group(1).strip()
                result["location"] = m.group(2).strip()
            else:
                result["presenter"] = rest
                result["location"] = ""
            result["_end_line"] = i
            return result
        if l:
            # Something unexpected - maybe more title lines
            title_lines.append(l)
            result["title"] = " ".join(title_lines).strip()
        i += 1

    result["_end_line"] = i - 1
    return result

def parse_non_poster_event(day_lines, start_idx, event_type):
    """Parse a non-poster event (symposia, plenary, etc.)."""
    result = {
        "type": event_type,
        "_end_line": start_idx
    }

    i = start_idx
    # First line is already the event type header
    header_line = day_lines[i].strip()
    result["_header"] = header_line
    i += 1

    # Next non-empty should be time range
    while i < len(day_lines) and not day_lines[i].strip():
        i += 1
    if i < len(day_lines) and is_time_range(day_lines[i]):
        result["time"] = day_lines[i].strip()
        i += 1
    else:
        result["time"] = ""

    # Skip empty
    while i < len(day_lines) and not day_lines[i].strip():
        i += 1

    # Get location (hall name)
    location = ""
    if i < len(day_lines) and is_hall_line(day_lines[i]):
        location = day_lines[i].strip()
        result["location"] = location
        i += 1
    else:
        result["location"] = ""

    # Skip empties
    while i < len(day_lines) and not day_lines[i].strip():
        i += 1

    # Collect title (may span multiple lines until we hit "Chair:" or "Introduction" or time)
    title_parts = []
    chairs = []
    while i < len(day_lines):
        l = day_lines[i].strip()
        if not l:
            i += 1
            continue
        if is_chair_line(l):
            chairs.append(l[len("Chair:"):].strip())
            i += 1
            continue
        if l.startswith("Moderator:"):
            chairs.append(l[len("Moderator:"):].strip())
            i += 1
            continue
        if l.startswith("Panelists"):
            # Skip panelist header
            i += 1
            continue
        if l == "Introduction" or l == "Introduction to the session" or l == "Brief introduction" or l == "Workshop presentation":
            result["introduction"] = l
            i += 1
            break
        if l == "Programme" or l.startswith("Speakers"):
            i += 1
            break
        if l == "Q&A":
            i += 1
            continue
        if is_time_range(l):
            break
        # If we've already collected at least one chair, this is likely a talk title, not part of the event title
        if chairs:
            break
        title_parts.append(l)
        i += 1

    result["title"] = " ".join(title_parts).strip() if title_parts else header_line
    if chairs:
        result["chairs"] = chairs

    # Now parse talks
    talks = []
    # current_talk being built
    current_talk = None

    while i < len(day_lines):
        l = day_lines[i].strip()
        if not l:
            i += 1
            continue

        # Check for event type repetition FIRST (same type repeating)
        if l == event_type:
            if current_talk:
                talks.append(current_talk)
                current_talk = None
            break

        # Check if we hit a different new event section
        if is_event_header(l) and l != event_type:
            if current_talk:
                talks.append(current_talk)
                current_talk = None
            break

        # Check for special endings
        if l == "Q&A":
            if current_talk:
                talks.append(current_talk)
                current_talk = None
            i += 1
            continue

        # Is it a time range?
        if is_time_range(l):
            if current_talk:
                talks.append(current_talk)
            current_talk = {"time": l}
            i += 1
            continue

        # Is it a speaker line?
        if is_speaker_line(l):
            if current_talk is None:
                current_talk = {}
            rest = l[len("Speaker:"):].strip()
            m = re.match(r'^(.+?)\s+\((.+)\)$', rest)
            if m:
                current_talk["speaker"] = m.group(1).strip()
                current_talk["location"] = m.group(2).strip()
            else:
                current_talk["speaker"] = rest
                current_talk["location"] = ""
            i += 1
            continue

        # If we have a current talk, it's the title
        if current_talk is not None:
            if "title" not in current_talk:
                current_talk["title"] = l
            else:
                current_talk["title"] += " " + l
            i += 1
            continue

        # If no current talk, this line might be a talk title without preceding time/speaker
        if current_talk is None:
            current_talk = {"title": l}
            i += 1
            continue

        # Check if we're in a networking event with just speaker names
        if event_type in ["Networking Events (NE)"]:
            m = re.match(r'^(.+?)\s+\((.+)\)$', l)
            if m:
                result.setdefault("talks", []).append({
                    "speaker": m.group(1).strip(),
                    "location": m.group(2).strip()
                })
                i += 1
                continue

        i += 1

    if current_talk:
        talks.append(current_talk)

    if talks:
        result["talks"] = talks

    result["_end_line"] = i - 1
    return result


# Run
import sys

data = parse_program()

# Clean up internal fields
def clean(obj):
    if isinstance(obj, dict):
        to_delete = [k for k in obj if k.startswith("_")]
        for k in to_delete:
            del obj[k]
        for v in obj.values():
            clean(v)
    elif isinstance(obj, list):
        for v in obj:
            clean(v)
    return obj

data = clean(data)

with open("program.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\nDone! Wrote program.json")
print(f"Total days: {len(data['days'])}")
for d in data['days']:
    print(f"  {d['day']} ({d['date']}): {len(d['events'])} events")
