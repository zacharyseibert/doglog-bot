import os
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from collections import defaultdict

SHEET_NAME = "DogLog Leaderboard"

# Write credentials.json if not present
if not os.path.exists("credentials.json"):
    encoded = os.environ.get("GOOGLE_CREDENTIALS_B64")
    if encoded:
        with open("credentials.json", "wb") as f:
            f.write(base64.b64decode(encoded))
    else:
        raise Exception("Missing GOOGLE_CREDENTIALS_B64 environment variable")

# Set up client
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME)

# Worksheets
log_tab = sheet.worksheet("Log")
leaderboard_tab = sheet.worksheet("Leaderboard")

def log_entry(username, amount):
    log_tab.append_row([
        datetime.utcnow().isoformat(),
        username.lower(),
        float(amount)
    ])

def get_leaderboard_from_sheet():
    records = log_tab.get_all_values()[1:]  # Skip header
    totals = defaultdict(float)
    for row in records:
        if len(row) >= 3:
            user = row[1].strip().lower()
            try:
                totals[user] += float(row[2])
            except ValueError:
                continue
    sorted_totals = sorted(totals.items(), key=lambda x: -x[1])
    return sorted_totals

def update_leaderboard(data):
    leaderboard_tab.clear()
    leaderboard_tab.append_row(["Username", "HotDogs"])
    for username, count in data:
        leaderboard_tab.append_row([username, round(count, 1)])

def get_total_from_sheet(username):
    username = username.lower().strip()
    leaderboard = get_leaderboard_from_sheet()
    for user, count in leaderboard:
        if user == username:
            return count
    return 0.0
def get_user_stats(username):
    """Returns a list of (timestamp, count) tuples for a given user from the Log tab."""
    sheet = client.open(SHEET_NAME)
    log_tab = sheet.worksheet("Log")
    rows = log_tab.get_all_values()[1:]  # skip header
    stats = []
    for row in rows:
        if len(row) >= 3 and row[1].strip().lower() == username.strip().lower():
            try:
                timestamp = row[0]
                count = float(row[2])
                stats.append((timestamp, count))
            except:
                continue
    return sorted(stats, key=lambda x: x[0])
