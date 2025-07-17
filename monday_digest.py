import os
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from google_sync import get_all_logs_from_sheet

SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL = "#doglog"
client = WebClient(token=SLACK_TOKEN)

def calculate_stats(logs):
    user_totals = defaultdict(int)
    user_weekly = defaultdict(int)
    user_previous_week = defaultdict(int)
    weekly_totals = defaultdict(int)
    highest_log = ("", 0)
    log_day_counts = Counter()

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
            timestamp = datetime.fromisoformat(timestamp_str)
            count = float(count_str)
        except (ValueError, TypeError):
            continue

        user_totals[user] += count
        week = timestamp.isocalendar().week
        year = timestamp.isocalendar().year

        if week == current_week and year == current_year:
            user_weekly[user] += count
            weekly_totals[current_week] += count
        elif week == last_week and year == last_week_year:
            user_previous_week[user] += count
            weekly_totals[last_week] += count

        log_day_counts[timestamp.strftime('%A')] += 1
        if count > highest_log[1]:
            highest_log = (user, count)

    return user_weekly, user_totals, user_previous_week, weekly_totals, highest_log, log_day_counts

def project_group_total(weekly_totals):
    now = datetime.now()
    next_july_4 = datetime(year=now.year + (1 if now.month > 7 or (now.month == 7 and now.day > 4) else 0), month=7, day=4)
    weeks_remaining = (next_july_4 - now).days // 7
    current_avg = sum(weekly_totals.values()) / len(weekly_totals) if weekly_totals else 0
    projected = int(sum(weekly_totals.values()) + (weeks_remaining * current_avg))
    return projected

def format_digest(user_weekly, user_totals, user_previous_week, weekly_totals, highest_log, log_day_counts):
    leaderboard = sorted(user_weekly.items(), key=lambda x: x[1], reverse=True)
    total_this_week = weekly_totals.get(datetime.now().isocalendar().week, 0)
    total_last_week = weekly_totals.get(datetime.now().isocalendar().week - 1, 0)
    percent_change = ((total_this_week - total_last_week) / total_last_week * 100) if total_last_week else 0
    projected_total = project_group_total(weekly_totals)

    top_dogger = leaderboard[0] if leaderboard else ("None", 0)
    all_time_hero = max(user_totals.items(), key=lambda x: x[1], default=("None", 0))
    most_active_day = log_day_counts.most_common(1)[0] if log_day_counts else ("None", 0)

    message = "*🌭 DogLog Monday Digest 🌭*\n\n"
    message += f"🐶 *Top Dogger This Week:* {top_dogger[0]} ({top_dogger[1]} dogs)\n"
    message += f"🌭 *All-Time Hot Dog Hero:* {all_time_hero[0]} ({all_time_hero[1]} dogs)\n"
    message += f"📈 *% Change from Last Week:* {percent_change:.1f}%\n"
    message += f"📅 *Projected Group Dogs by Next July 4th:* {projected_total}\n"
    message += f"😤 *Highest Single Log:* {highest_log[0]} ({highest_log[1]} dogs)\n"
    message += f"📆 *Most Active Logging Day:* {most_active_day[0]} ({most_active_day[1]} logs)\n"
    return message

def post_digest():
    try:
        logs = get_all_logs_from_sheet()
        if not logs:
            raise ValueError("No logs found.")

        stats = calculate_stats(logs)
        message = format_digest(*stats)
        response = client.chat_postMessage(channel=SLACK_CHANNEL, text=message)
        print("Message posted:", response)
        return {"status": "success", "message": "Digest posted successfully."}
    except SlackApiError as e:
        print("Slack error:", e.response["error"])
        return {"status": "error", "message": f"Slack error: {e.response['error']}"}
    except Exception as e:
        print("Error posting digest:", str(e))
        return {"status": "error", "message": f"Error posting digest: {str(e)}"}
def get_digest_message():
    logs = get_all_logs_from_sheet()
    if not logs:
        raise ValueError("No logs found.")
    stats = calculate_stats(logs)
    return format_digest(*stats)
