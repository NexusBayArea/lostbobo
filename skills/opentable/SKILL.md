---
name: opentable
description: Search for restaurant availability and manage dinner reservations.
license: MIT
compatibility: opencode
---

# OpenTable Skill for OpenCode

This skill gives OpenCode the ability to check restaurant availability via the terminal.

## Instructions
1. When a user asks about dining or reservations, use this skill.
2. Run the command: `python skills/opentable/opentable.py "<user_request>"`
3. Parse the JSON output and present the options to the user.

## Examples
- "Find a table for 4 at 7 PM in San Francisco."
- "Are there any Italian spots open tonight?"
- "Book a dinner reservation for 2 in New York."
- "What Japanese restaurants are available this evening?"

## Output Format
The script returns JSON with the following structure:
```json
{
  "status": "success",
  "query": "original query",
  "parsed_params": {
    "cuisine": "italian",
    "party_size": 4,
    "time": "19:00",
    "location": "San Francisco",
    "date": "2026-04-04"
  },
  "results_count": 2,
  "restaurants": [
    {
      "name": "Restaurant Name",
      "cuisine": "Cuisine Type",
      "rating": 4.5,
      "location": "City",
      "available_slots": ["18:00", "19:00", "20:00"]
    }
  ]
}
```
