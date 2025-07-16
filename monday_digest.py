import os
import datetime
from collections import defaultdict
from slack_sdk import WebClient
from google_sync import get_leaderboard_from_sheet, get_all_logs_from_sheet

client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
CHANNEL = "#doglog"

def post_digest():
    now = datetime.datetime.now()
    tz = datetime.timezone(datetime.timedelta(hours=-5))  # EST
    today = now.astimezone(tz).date()
    start_of_week = today - datetime.timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + datetime.timedelta(days=6)

    logs = get_all_logs_from_sheet()
    leaderboard = get_leaderboard_from_sheet()

    # Filter logs for this week and last week
    this_week_logs = []
    last_week_logs = []
    for log in logs:
        username, amount, timestamp = log
        log_date = datetime.datetime.strptime(timestamp, "%Y-%m-%d").date()
        if start_of_week <= log_date <= end_of_week:
            this_week_logs.append((username, float(amount), log_date))
        elif (start_of_week - datetime.timedelta(days=7)) <= log_date < start_of_week:
            last_week_logs.append((username, float(amount), log_date))

    # Build user stats
    user_totals = defaultdict(float)
    user_counts = defaultdict(int)
    user_days = defaultdict(set)

    for username, amount, log_date in this_week_logs:
        user_totals[username] += amount
        user_counts[username] += 1
        user_days[username].add(log_date)

    # Largest log
    largest_log = max(this_week_logs, key=lambda x: x[1], default=None)

    # Most consistent logger
    most_days = max(user_days.items(), key=lambda x: len(x[1]), default=(None, set()))

    # Group totals
    this_week_total = sum(amount for _, amount, _ in this_week_logs)
    last_week_total = sum(amount for _, amount, _ in last_week_logs)
    percent_change = ((this_week_total - last_week_total) / last_week_total * 100) if last_week_total else 0

    # Projection
    days_until_july_4 = (datetime.date(today.year + 1, 7, 4) - today).days
    projected_total = int(this_week_total * (days_until_july_4 / 7))

    # Format message
    lines = ["🌭 *Weekly Hot Dog Digest* 🌭", ""]

    if largest_log:
        lines.append(f"• Largest log: {largest_log[1]} dogs by {largest_log[0]} on {largest_log[2].strftime('%b %d')}")
    if most_days[0]:
        lines.append(f"• Most consistent: {most_days[0]} with logs on {len(most_days[1])} days")
    if user_counts:
        avg_log = this_week_total / sum(user_counts.values())
        lines.append(f"• Average log size: {avg_log:.2f} dogs")

    lines.append(f"• Total dogs this week: {this_week_total:.1f}")
    lines.append(f"• Change from last week: {percent_change:+.1f}%")
    lines.append(f"• Projected Group Dogs by Next July 4th: {projected_total}")

    lines.append("\n🏆 *All-Time Leaderboard* 🏆")
    for i, (user, total) in enumerate(leaderboard, 1):
        lines.append(f"{i}. {user} — {total:.1f} 🌭")

    message = "\n".join(lines)

    try:
        client.chat_postMessage(channel=CHANNEL, text=message)
    except Exception as e:
        return {"status": "error", "message": f"Slack error: {e.response['error']}"}

    return {"status": "success", "message": "Digest posted to Slack"}
