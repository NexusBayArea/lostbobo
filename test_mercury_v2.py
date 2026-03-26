import os
import requests
import json

def test_mercury_v2():
    # Use INCEPTION_API_KEY as requested, falling back to MERCURY_API_KEY
    api_key = os.getenv("INCEPTION_API_KEY") or os.getenv("MERCURY_API_KEY")
    if not api_key:
        print("Missing API key (INCEPTION_API_KEY or MERCURY_API_KEY)")
        return False

    print(f"Testing Mercury-2 API with key: {api_key[:8]}***")

    response = requests.post(
      "https://api.inceptionlabs.ai/v1/chat/completions",
      headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
      },
      json={
        "model": "mercury-2",
        "messages": [
          {"role": "user", "content": "What is the meaning of life?"}
        ]
      }
    )

    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
        return True
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw Response: {response.text}")
        return False

if __name__ == "__main__":
    test_mercury_v2()
