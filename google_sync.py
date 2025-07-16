import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Google Sheet config
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = "credentials.json"
SHEET_NAME = "DogLog"

# Initialize client and sheet
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

def log_entry(username, count):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([username, count, timestamp])

def update_leaderboard(username):
    leaderboard = get_leaderboard_from_sheet()
    total = leaderboard.get(username, 0)
    total += 0  # No increment here; logic should live outside if needed
    return total

def get_total_from_sheet(username):
    data = sheet.get_all_values()
    total = 0
    for row in data[1:]:  # skip header
        if row[0] == username:
            try:
                total += float(row[1])
            except ValueError:
                continue
    return total

def get_leaderboard_from_sheet():
    data = sheet.get_all_values()
    leaderboard = {}
    for row in data[1:]:  # skip header
        username = row[0]
        try:
            count = float(row[1])
        except ValueError:
            continue
        leaderboard[username] = leaderboard.get(username, 0) + count
    return leaderboard

def get_user_stats(username):
    data = sheet.get_all_values()
    entries = []
    for row in data[1:]:  # skip header
        if row[0] == username:
            try:
                amount = float(row[1])
                timestamp = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")
                entries.append((amount, timestamp))
            except (ValueError, IndexError):
                continue

    if not entries:
        return None

    total = sum(x[0] for x in entries)
    count = len(entries)
    avg = total / count
    first_log = min(entries, key=lambda x: x[1])[1]
    last_log = max(entries, key=lambda x: x[1])[1]
    largest_entry = max(entries, key=lambda x: x[0])

    return {
        "total": round(total, 2),
        "count": count,
        "average": round(avg, 2),
        "first_log": first_log,
        "last_log": last_log,
        "largest_entry": largest_entry
    }

def get_all_logs_from_sheet():
    data = sheet.get_all_values()
    logs = []

    for row in data[1:]:  # skip header
        if len(row) >= 3 and row[0] and row[1] and row[2]:
            username = row[0]
            try:
                amount = float(row[1])
                timestamp = row[2]
                logs.append((username, amount, timestamp))
            except ValueError:
                continue

    return logs
