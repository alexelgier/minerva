"""
Quick test script for the journal submission endpoint
"""
import requests
import json
import os

# Configuration
API_BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/journal/submit"

# --- Journal Content Configuration ---
# Set the name of the .md file from the 'notes' directory to use for testing
TEST_FILE_NAME = "2025-09-09.md"  # <-- MODIFY THIS to select a different file
NOTES_DIR = os.path.join(os.path.dirname(__file__), "notes")
# ------------------------------------

# Construct the full path to the test file
file_path = os.path.join(NOTES_DIR, TEST_FILE_NAME)

# Prepare journal data
TEST_JOURNAL = None

try:
    # Extract date from filename (e.g., "2025-09-10.md" -> "2025-09-10")
    journal_date = os.path.splitext(TEST_FILE_NAME)[0]

    with open(file_path, 'r', encoding='utf-8') as f:
        journal_text = f.read()

    TEST_JOURNAL = {
        "date": journal_date,
        "text": journal_text
    }
except FileNotFoundError:
    print(f"❌ ERROR: Test file not found at '{file_path}'")
    print("Please make sure the 'notes' directory exists and contains the specified file.")
except Exception as e:
    print(f"❌ ERROR: Failed to load journal from file: {e}")


def test_submit_journal():
    """Test the journal submission endpoint"""
    if not TEST_JOURNAL:
        print("Aborting submission due to an error during journal loading.")
        return

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
