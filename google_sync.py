import gspread
import os
import json
import base64
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Decode credentials from environment variable
creds_b64 = os.environ["GOOGLE_CREDENTIALS_B64"]
creds_json = json.loads(base64.b64decode(creds_b64).decode("utf-8"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, SCOPE)

client = gspread.authorize(creds)
sheet = client.open("DogLog").sheet1

def log_entry(user: str, count: int):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, user, count])

def get_total_from_sheet():
    data = sheet.get_all_records()
    return sum(int(row["Count"]) for row in data if str(row["Count"]).isdigit())

def update_leaderboard():
    return get_leaderboard_from_sheet()

def get_leaderboard_from_sheet():
    data = sheet.get_all_records()
    leaderboard = {}
    for row in data:
        user = row["User"]
        count = int(row["Count"]) if str(row["Count"]).isdigit() else 0
        leaderboard[user] = leaderboard.get(user, 0) + count
    return sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)

def get_all_logs_from_sheet():
    return sheet.get_all_records()

def get_user_stats():
    data = sheet.get_all_records()
    user_stats = {}

    for row in data:
        user = row["User"]
        count = int(row["Count"]) if str(row["Count"]).isdigit() else 0
        timestamp = row["Timestamp"]
        date = timestamp.split(" ")[0]

        if user not in user_stats:
            user_stats[user] = {
                "total": 0,
                "days": set(),
            }

        user_stats[user]["total"] += count
        user_stats[user]["days"].add(date)

    for user in user_stats:
        total = user_stats[user]["total"]
        days = len(user_stats[user]["days"])
        avg_per_day = total / days if days > 0 else 0
        user_stats[user]["avg_per_day"] = round(avg_per_day, 2)

    return user_stats
