import gspread
import os
import json
import base64
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

# Setup Google Sheets credentials
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_b64 = os.environ["GOOGLE_CREDENTIALS_B64"]
creds_json = json.loads(base64.b64decode(creds_b64).decode("utf-8"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, SCOPE)
client = gspread.authorize(creds)

# Open the DogLog sheet
sheet = client.open("DogLog").sheet1

def log_entry(user: str, count: float):
    timestamp = datetime.now().isoformat()
    sheet.append_row([timestamp, user, count])

def get_total_from_sheet():
    data = sheet.get_all_records()
    return sum(float(row["Count"]) for row in data if str(row["Count"]).replace('.', '', 1).isdigit())

def get_leaderboard_from_sheet():
    data = sheet.get_all_records()
    leaderboard = {}
    for row in data:
        user = row["User"]
        count = float(row["Count"]) if str(row["Count"]).replace('.', '', 1).isdigit() else 0
        leaderboard[user] = leaderboard.get(user, 0) + count

    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)

    # Format as string for Slack
    if not sorted_leaderboard:
        return "No logs yet!"

    lines = [f"{i+1}. {user}: {count:.1f} dog(s)" for i, (user, count) in enumerate(sorted_leaderboard)]
    return "\n".join(lines)

def get_all_logs_from_sheet():
    """Returns all rows as list of dicts with headers."""
    rows = sheet.get_all_values()
    if not rows or len(rows) < 2:
        return []

    headers = rows[0]
    return [dict(zip(headers, row)) for row in rows[1:]]

def get_charity_summary():
    """Summarizes the total dogs logged by moonhammad since July 17 and calculates total owed."""
    try:
        print("[DEBUG] Entered get_charity_summary()")
        data = get_all_logs_from_sheet()
        print(f"[DEBUG] Retrieved {len(data)} rows")

        start_date = datetime(2025, 7, 17)
        total_dogs = 0

        for row in data:
            try:
                user = row.get("User", "").lower()
                timestamp = row.get("Timestamp", "")
                count = row.get("Count", "")

                if user == "moonhammad":
                    dt = datetime.fromisoformat(timestamp)
                    if dt >= start_date:
                        if str(count).replace('.', '', 1).isdigit():
                            total_dogs += float(count)
                        else:
                            print(f"[DEBUG] Skipping row with invalid count: {count}")
            except Exception as inner:
                print(f"[DEBUG] Error processing row {row}: {inner}")

        total_dollars = total_dogs * 5 * 3  # Two contributors at $5 each
        print(f"[DEBUG] Total dogs: {total_dogs}, Total dollars: {total_dollars}")

        return f"moonhammad has eaten {int(total_dogs)} dogs since July 17. That's ${total_dollars:.2f} total for his charity. 💸"

    except Exception as e:
        print(f"[ERROR] Exception in get_charity_summary(): {e}")
        raise
