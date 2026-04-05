import sys
import json
import argparse
from datetime import datetime


def parse_query(query):
    """Parse user query into structured booking parameters."""
    params = {
        "cuisine": None,
        "party_size": 2,
        "time": "19:00",
        "location": None,
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    query_lower = query.lower()

    # Extract party size
    size_keywords = {
        "for 1": 1,
        "for 2": 2,
        "for 3": 3,
        "for 4": 4,
        "for 5": 5,
        "for 6": 6,
        "for 7": 7,
        "for 8": 8,
    }
    for keyword, size in size_keywords.items():
        if keyword in query_lower:
            params["party_size"] = size
            break

    # Extract cuisine type
    cuisines = [
        "italian",
        "chinese",
        "japanese",
        "mexican",
        "french",
        "indian",
        "thai",
        "american",
        "mediterranean",
        "korean",
    ]
    for cuisine in cuisines:
        if cuisine in query_lower:
            params["cuisine"] = cuisine
            break

    # Extract time
    time_keywords = {
        "tonight": "19:00",
        "dinner": "19:00",
        "lunch": "12:00",
        "brunch": "11:00",
        "noon": "12:00",
        "evening": "19:00",
    }
    for keyword, time in time_keywords.items():
        if keyword in query_lower:
            params["time"] = time
            break

    # Extract location (simple heuristic)
    locations = [
        "san francisco",
        "new york",
        "los angeles",
        "chicago",
        "seattle",
        "boston",
        "miami",
        "austin",
        "denver",
        "portland",
    ]
    for location in locations:
        if location in query_lower:
            params["location"] = location
            break

    return params


def search_restaurants(params):
    """Search for restaurant availability (mock implementation)."""
    mock_restaurants = [
        {
            "name": "Bella Cucina",
            "cuisine": "Italian",
            "rating": 4.5,
            "location": "San Francisco",
            "available_slots": ["18:00", "19:00", "20:30"],
        },
        {
            "name": "Dragon Palace",
            "cuisine": "Chinese",
            "rating": 4.3,
            "location": "San Francisco",
            "available_slots": ["18:30", "19:30", "21:00"],
        },
        {
            "name": "Sakura Sushi",
            "cuisine": "Japanese",
            "rating": 4.7,
            "location": "San Francisco",
            "available_slots": ["17:30", "19:00", "20:00"],
        },
        {
            "name": "El Mariachi",
            "cuisine": "Mexican",
            "rating": 4.2,
            "location": "San Francisco",
            "available_slots": ["18:00", "19:30", "21:00"],
        },
        {
            "name": "Le Petit Bistro",
            "cuisine": "French",
            "rating": 4.8,
            "location": "San Francisco",
            "available_slots": ["19:00", "20:00"],
        },
    ]

    results = []
    for restaurant in mock_restaurants:
        if (
            params.get("cuisine")
            and params["cuisine"].lower() != restaurant["cuisine"].lower()
        ):
            continue
        if (
            params.get("location")
            and params["location"].lower() not in restaurant["location"].lower()
        ):
            continue
        results.append(restaurant)

    return results if results else mock_restaurants


def handle_booking(query):
    """Main handler for booking requests."""
    try:
        params = parse_query(query)
        restaurants = search_restaurants(params)

        response = {
            "status": "success",
            "query": query,
            "parsed_params": params,
            "results_count": len(restaurants),
            "restaurants": restaurants,
        }
        return response
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


def main():
    parser = argparse.ArgumentParser(description="OpenTable restaurant search")
    parser.add_argument("query", nargs="+", help="Search query")
    args = parser.parse_args()

    user_input = " ".join(args.query)
    result = handle_booking(user_input)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
