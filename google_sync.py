import os
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Decode and write credentials.json from env var if not already present
if not os.path.exists("credentials.json"):
    encoded = os.environ.get("GOOGLE_CREDENTIALS_B64")
    if encoded:
        with open("credentials.json", "wb") as f:
            f.write(base64.b64decode(encoded))
    else:
        raise Exception("Missing GOOGLE_CREDENTIALS_B64 environment variable")

# Connect to Google Sheets
SHEET_NAME = "DogLog Leaderboard"  # Must exactly match your Sheet title

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME)

# Load specific tabs
leaderboard_tab = sheet.worksheet("Leaderboard")
log_tab = sheet.worksheet("Log")

def update_leaderboard(data):
    """
    Overwrites the 'Leaderboard' tab with updated data.
    data: list of tuples [(username, count), ...]
    """
    leaderboard_tab.clear()
    leaderboard_tab.append_row(["Username", "HotDogs"])
    for username, count in data:
        leaderboard_tab.append_row([username, round(count, 1)])

def log_entry(username, amount):
    """
    Appends a new row to the 'Log' tab with timestamp, username, and amount.
    """
    log_tab.append_row([
        datetime.utcnow().isoformat(),
        username,
        float(amount)
    ])
