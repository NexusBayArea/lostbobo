import os
import requests
import json
import sys

def test_mercury():
    api_key = os.getenv("MERCURY_API_KEY")
    if not api_key:
        print("Error: MERCURY_API_KEY not found in environment variables.")
        return False

    url = "https://api.inceptionlabs.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mercury",
        "messages": [
            {"role": "user", "content": "reply SIMHPC_OK"}
        ]
    }

    print(f"Testing Mercury API at {url}...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        content = data['choices'][0]['message']['content'].strip()
        print(f"Response content: {content}")
        
        if "SIMHPC_OK" in content:
            print("SUCCESS: Mercury API is working correctly.")
            return True
        else:
            print(f"FAILURE: Unexpected response content: {content}")
            return False
            
    except Exception as e:
        print(f"ERROR: Mercury API test failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response Body: {e.response.text}")
        return False

if __name__ == "__main__":
    success = test_mercury()
    sys.exit(0 if success else 1)
