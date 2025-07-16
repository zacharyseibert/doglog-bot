import os
from datetime import datetime, timedelta
from collections import defaultdict
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from google_sync import get_all_logs_from_sheet

SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL = "#doglog"  # Make sure your bot is a member of this channel
client = WebClient(token=SLACK_TOKEN)


def calculate_stats(logs):
    user_totals = defaultdict(int)
    user_weekly = defaultdict(int)
    user_previous_week = defaultdict(int)
    weekly_totals = defaultdict(int)
    first_log_date = {}
    most_recent_log_date = {}
    largest_log = {}

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

        if user not in first_log_date or date < first_log_date[user]:
            first_log_date[user] = date
        if user not in most_recent_log_date or date > most_recent_log_date[user]:
            most_recent_log_date[user] = date
        if user not in largest_log or count > largest_log[user][0]:
            largest_log[user] = (count, date)

    return (
        user_totals,
        user_weekly,
        user_previous_week,
        weekly_totals,
        first_log_date,
        most_recent_log_date,
        largest_log,
    )


def project_group_total(weekly_totals):
    now = datetime.now()
    next_july_4 = datetime(year=now.year + 1, month=7, day=4)
    if now.month == 7 and now.day > 4:
        next_july_4 = datetime(year=now.year + 1, month=7, day=4)

    weeks_remaining = (next_july_4 - now).days // 7
    current_avg = sum(weekly_totals.values()) / len(weekly_totals) if weekly_totals else 0
    projected = int(sum(weekly_totals.values()) + (weeks_remaining * current_avg))
    return projected


def format_digest(user_totals, user_weekly, user_previous_week, weekly_totals,
                  first_log_date, most_recent_log_date, largest_log):
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

    message += f"\n📈 *% Change from Last Week:* {percent_change:.1f}%"
    message += f"\n📅 *Projected Group Dogs by Next July 4th:* {projected_total}\n"

    message += "\n*Fun Stats:*\n"
    for user in sorted(user_totals):
        first = first_log_date.get(user)
        recent = most_recent_log_date.get(user)
        largest = largest_log.get(user)
        entries = sum(1 for row in leaderboard if row[0] == user)
        avg = round(user_totals[user] / entries, 2) if entries else 0
        if not (first and recent and largest):
            continue
        message += (
            f"\n🌭 Stats for {user}:\n"
            f"• Total hot dogs: {user_totals[user]}\n"
            f"• Entries: {entries}\n"
            f"• Average per log: {avg}\n"
            f"• First log: {first.strftime('%b %d')}\n"
            f"• Most recent log: {recent.strftime('%b %d')}\n"
            f"• Largest log: {largest[0]} dogs on {largest[1].strftime('%b %d')}\n"
        )

    return message


def post_digest():
    try:
        logs = get_all_logs_from_sheet()
        if not logs:
            raise ValueError("No logs found.")

        (
            user_totals,
            user_weekly,
            user_previous_week,
            weekly_totals,
            first_log_date,
            most_recent_log_date,
            largest_log,
        ) = calculate_stats(logs)

        message = format_digest(
            user_totals,
            user_weekly,
            user_previous_week,
            weekly_totals,
            first_log_date,
            most_recent_log_date,
            largest_log,
        )

        response = client.chat_postMessage(channel=SLACK_CHANNEL, text=message)
        print("Message posted:", response)
        return {"status": "success", "message": "Digest posted successfully."}
    except SlackApiError as e:
        print("Slack error:", e.response["error"])
        return {"status": "error", "message": f"Slack error: {e.response['error']}"}
    except Exception as e:
        print("Error posting digest:", str(e))
        return {"status": "error", "message": f"Error posting digest: {str(e)}"}
