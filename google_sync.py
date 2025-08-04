import gspread
import os
import json
import base64
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import pytz
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

    if not sorted_leaderboard:
        return "No logs yet!"

    lines = [f"{i+1}. {user}: {count:.1f} dog(s)" for i, (user, count) in enumerate(sorted_leaderboard)]
    return "\n".join(lines)

def get_all_logs_from_sheet():
    rows = sheet.get_all_values()
    if not rows or len(rows) < 2:
        return []
    headers = rows[0]
    return [dict(zip(headers, row)) for row in rows[1:]]

def get_charity_summary():
    try:
        data = get_all_logs_from_sheet()
        if not data:
            return "No logs found."

        start_date = datetime(2025, 7, 17, tzinfo=pytz.timezone("US/Eastern"))
        total_dogs = 0.0

        for row in data:
            user = row.get("User", "").strip().lower()
            timestamp = row.get("Timestamp", "").strip()
            count_str = row.get("Count", "").strip()

            if user != "moonhammad":
                continue

            try:
                ts = datetime.fromisoformat(timestamp).astimezone(pytz.timezone("US/Eastern"))
                count = float(count_str)
            except Exception as parse_error:
                print(f"[WARN] Skipping bad row: {row} — Error: {parse_error}")
                continue

            if ts >= start_date:
                total_dogs += count

        total_dollars = total_dogs * 5 * 3
        return (
            f"moonhammad has eaten {total_dogs:.1f} dogs since July 17. "
            f"That's ${total_dollars:.2f} total for his charity. 💸"
        )

    except Exception as e:
        print(f"[ERROR] Exception in get_charity_summary(): {e}")
        return "Error generating charity summary."

def get_stats_summary():
    data = get_all_logs_from_sheet()
    if not data:
        return "No data available."

    df = []
    for row in data:
        try:
            ts = datetime.fromisoformat(row["Timestamp"]).astimezone(pytz.timezone("US/Eastern"))
            user = row["User"]
            count = float(row["Count"])
            df.append({"Timestamp": ts, "User": user, "Count": count, "Date": ts.date()})
        except:
            continue

    if not df:
        return "No valid log entries found."

    now = datetime.now(pytz.timezone("US/Eastern"))
    seven_days_ago = now - timedelta(days=7)
    df_week = [row for row in df if row["Timestamp"] >= seven_days_ago]

    top_counts = Counter()
    day_counts = defaultdict(float)
    streaks = defaultdict(int)
    day_sets = defaultdict(set)
    all_time_total = sum(row["Count"] for row in df)

    for row in df_week:
        top_counts[row["User"]] += row["Count"]
        day_counts[(row["User"], row["Date"])] += row["Count"]
        day_sets[row["User"]].add(row["Date"])

    top_5 = top_counts.most_common(5)
    most_logged_day = max(day_counts.items(), key=lambda x: x[1], default=(("", now.date()), 0))

    # Fastest to 10
    user_progress = defaultdict(float)
    reached = {}
    for row in sorted(df_week, key=lambda x: x["Timestamp"]):
        u = row["User"]
        user_progress[u] += row["Count"]
        if user_progress[u] >= 10 and u not in reached:
            reached[u] = row["Timestamp"]
    fastest_user = min(reached.items(), key=lambda x: x[1]) if reached else (None, None)

    # Longest streaks
    longest = {}
    for user, dates in day_sets.items():
        streak = 1
        max_streak = 1
        for i in range(1, len(sorted(dates))):
            d1, d2 = sorted(dates)[i-1:i+1]
            if (d2 - d1).days == 1:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 1
        longest[user] = max_streak

    # MVP = total count + 0.5 * streak
    mvp_scores = {user: top_counts[user] + 0.5 * longest.get(user, 0) for user in top_counts}
    mvp = max(mvp_scores.items(), key=lambda x: x[1]) if mvp_scores else ("N/A", 0)

    summary = "*🌭 Weekly DogLog Stats*\n\n"
    summary += "*Top 5 of the Week:*\n" + "\n".join([f"{i+1}. {user}: {count:.1f}" for i, (user, count) in enumerate(top_5)]) + "\n\n"
    summary += f"*Most Logged in One Day:* {most_logged_day[0][0]} with {most_logged_day[1]:.1f} on {most_logged_day[0][1]}\n"
    summary += f"*Biggest Single-Day Overeater:* {most_logged_day[0][0]} with {most_logged_day[1]:.1f} on {most_logged_day[0][1]}\n"
    if fastest_user[0]:
        summary += f"*Fastest to 10 Dogs:* {fastest_user[0]} at {fastest_user[1].strftime('%Y-%m-%d %H:%M %Z')}\n"
    else:
        summary += "*Fastest to 10 Dogs:* N/A\n"
    summary += "*Longest Streak This Week:*\n" + "\n".join([f"{user}: {streak} day(s)" for user, streak in longest.items()]) + "\n\n"
    summary += f"*Total Logged Since Inception:* {all_time_total:.1f}\n"
    summary += f"*Weekly MVP:* {mvp[0]} with a score of {mvp[1]:.1f}"

    return summary

def get_keeper_summary():
    try:
        data = get_all_logs_from_sheet()
        if not data:
            return "No logs found."

        start_date = datetime(2025, 7, 30, tzinfo=pytz.timezone("US/Eastern"))
        end_date = datetime(2025, 8, 28, 23, 59, 59, tzinfo=pytz.timezone("US/Eastern"))
        now = datetime.now(pytz.timezone("US/Eastern"))
        days_elapsed = max((now - start_date).days + 1, 1)
        days_remaining = max((end_date - now).days, 0)
        total_days = (end_date - start_date).days + 1

        progress = defaultdict(float)

        for row in data:
            try:
                ts = datetime.fromisoformat(row["Timestamp"]).astimezone(pytz.timezone("US/Eastern"))
                if start_date <= ts <= end_date:
                    user = row["User"]
                    count = float(row["Count"])
                    progress[user] += count
            except:
                continue

        if not progress:
            return "No logs yet in the Keeper Challenge window."

        summary_lines = ["*🌭 Keeper Challenge Progress (7/30 – 8/28)*\n"]
        for user, total in sorted(progress.items(), key=lambda x: x[1], reverse=True):
            pct = min(100 * total / 50, 100)
            projected_total = total / days_elapsed * total_days
            will_hit = "✅" if projected_total >= 50 else "❌"
            needed_per_day = (50 - total) / days_remaining if days_remaining > 0 else 0
            summary_lines.append(
                f"{user}: {total:.1f} dogs ({pct:.0f}%) {will_hit} — "
                f"Projected: {projected_total:.1f}, Needs {needed_per_day:.2f}/day"
            )

        return "\n".join(summary_lines)

    except Exception as e:
        print(f"[ERROR] Exception in get_keeper_summary(): {e}")
        return "Error generating keeper summary."
