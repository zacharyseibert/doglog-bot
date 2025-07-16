from datetime import datetime
from collections import defaultdict
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from google_sync import get_all_logs_from_sheet
import os

SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL = "#doglog"
client = WebClient(token=SLACK_TOKEN)

def calculate_stats(logs):
    user_totals = defaultdict(float)
    user_weekly = defaultdict(float)
    user_previous_week = defaultdict(float)
    weekly_totals = defaultdict(float)

    now = datetime.now()
    current_week = now.isocalendar().week
    current_year = now.year
    last_week = current_week - 1 if current_week > 1 else 52
    last_week_year = current_year if current_week > 1 else current_year - 1

    for row in logs:
        if not isinstance(row, dict):
            continue
        user = row.get("User")
        timestamp_str = row.get("Timestamp")
        count_str = row.get("Count")

        if not user or not timestamp_str or not count_str:
            continue

        try:
            date = datetime.fromisoformat(timestamp_str)
            count = float(count_str)
        except (ValueError, TypeError):
            continue

        user_totals[user] += count

        week = date.isocalendar().week
        year = date.isocalendar().year

        if week == current_week and year == current_year:
            user_weekly[user] += count
            weekly_totals[current_week] += count
        elif week == last_week and year == last_week_year:
            user_previous_week[user] += count
            weekly_totals[last_week] += count

    return user_totals, user_weekly, user_previous_week, weekly_totals

def project_group_total(weekly_totals):
    now = datetime.now()
    next_july_4 = datetime(year=now.year + 1, month=7, day=4)
    if now.month == 7 and now.day > 4:
        next_july_4 = datetime(year=now.year + 1, month=7, day=4)

    weeks_remaining = (next_july_4 - now).days // 7
    current_avg = sum(weekly_totals.values()) / len(weekly_totals) if weekly_totals else 0
    projected = int(sum(weekly_totals.values()) + (weeks_remaining * current_avg))
    return projected

def format_digest(user_totals, user_weekly, user_previous_week, weekly_totals):
    leaderboard = sorted(user_weekly.items(), key=lambda x: x[1], reverse=True)
    total_this_week = weekly_totals.get(datetime.now().isocalendar().week, 0)
    total_last_week = weekly_totals.get(datetime.now().isocalendar().week - 1, 0)
    percent_change = (
        ((total_this_week - total_last_week) / total_last_week) * 100
        if total_last_week else 0
    )
    projected_total = project_group_total(weekly_totals)

    message = "*🌭 DogLog Monday Digest 🌭*\n\n"
    message += "*Top Doggers This Week:*\n"
    for i, (user, count) in enumerate(leaderboard[:10], start=1):
        message += f"{i}. {user}: {count} dog(s)\n"

    message += "\n*All-Time Totals:*\n"
    all_time = sorted(user_totals.items(), key=lambda x: x[1], reverse=True)
    for user, count in all_time[:5]:
        message += f"- {user}: {count} total dog(s)\n"

    highest_week_user = max(user_weekly.items(), key=lambda x: x[1], default=("None", 0))
    highest_all_time_user = max(user_totals.items(), key=lambda x: x[1], default=("None", 0))

    message += f"\n🏆 *Top Glizzy Gladiator This Week:* {highest_week_user[0]} ({highest_week_user[1]} dogs)\n"
    message += f"🥇 *All-Time Hot Dog Hero:* {highest_all_time_user[0]} ({highest_all_time_user[1]} dogs)\n"
    message += f"\n📈 *% Change from Last Week:* {percent_change:.1f}%"
    message += f"\n📅 *Projected Group Dogs by Next July 4th:* {projected_total}\n"

    return message

def post_digest():
    try:
        logs = get_all_logs_from_sheet()
        if not logs:
            raise ValueError("No logs found.")

        user_totals, user_weekly, user_previous_week, weekly_totals = calculate_stats(logs)
        message = format_digest(user_totals, user_weekly, user_previous_week, weekly_totals)

        response = client.chat_postMessage(channel=SLACK_CHANNEL, text=message)
        print("Message posted:", response)
        return {"status": "success", "message": "Digest posted successfully."}
    except SlackApiError as e:
        print("Slack error:", e.response["error"])
        return {"status": "error", "message": f"Slack error: {e.response['error']}"}
    except Exception as e:
        print("Error posting digest:", str(e))
        return {"status": "error", "message": f"Error posting digest: {str(e)}"}
