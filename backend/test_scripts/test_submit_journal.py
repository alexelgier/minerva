"""
Quick test script for the journal submission endpoint
"""
import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/journal/submit"

# TODO Test journal content - MODIFY THIS
TEST_JOURNAL = {
    "date": "2025-09-10",
    "text": """[[2025]] [[2025-09]] [[2025-09-10]]  Wednesday

12:30, desperté, sin alarma. 
"""
}


def test_submit_journal():
    """Test the journal submission endpoint"""
    url = f"{API_BASE_URL}{ENDPOINT}"

    print(f"Submitting journal to: {url}")
    print(f"Journal date: {TEST_JOURNAL['date']}")
    print(f"Journal length: {len(TEST_JOURNAL['text'])} characters")
    print("-" * 50)

    try:
        response = requests.post(
            url,
            json=TEST_JOURNAL,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"Workflow ID: {result.get('workflow_id')}")
            print(f"Journal ID: {result.get('journal_id')}")
            print(f"Message: {result.get('message')}")
        else:
            print("❌ FAILED!")
            print(f"Error: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Is the FastAPI server running on localhost:8000?")
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Request took too long")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")


if __name__ == "__main__":
    test_submit_journal()
