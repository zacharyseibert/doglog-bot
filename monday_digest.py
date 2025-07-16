import os
import pytz
import datetime
from collections import defaultdict
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from google_sync import get_all_logs  # We’ll define this in a second

# Set these explicitly or use .env
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = "#doglog"

client = WebClient(token=SLACK_TOKEN)
eastern = pytz.timezone("US/Eastern")


def get_last_week_range():
    today = datetime.datetime.now(eastern).date()
    last_sunday = today - datetime.timedelta(days=today.weekday() + 1)  # Sunday
    last_saturday = last_sunday + datetime.timedelta(days=6)
    return last_sunday, last_saturday


def format_digest(logs, start_date, end_date):
    user_totals = defaultdict(float)
    user_counts = defaultdict(int)
    largest_log = (0, None, None)  # (amount, user, date)
    unique_users = set()

    for timestamp, user, amount in logs:
        date = timestamp.date()
        if start_date <= date <= end_date:
            user_totals[user] += amount
            user_counts[user] += 1
            unique_users.add(user)
            if amount > largest_log[0]:
                largest_log = (amount, user, date)

    if not logs:
        return "🌭 No logs recorded last week. Step up your dog game."

    top_eater = max(user_totals.items(), key=lambda x: x[1], default=(None, 0))[0]
    most_logs = max(user_counts.items(), key=lambda x: x[1], default=(None, 0))[0]

    lines = [
        f"🌭 *Weekly DogLog Digest* ({start_date.strftime('%b %d')}–{end_date.strftime('%b %d')}):\n",
        f"• Top Eater: {top_eater} — {user_totals[top_eater]:.1f} dogs",
        f"• Most Logs: {most_logs} — {user_counts[most_logs]} entries",
        f"• Largest Log: {largest_log[0]:.1f} by {largest_log[1]} on {largest_log[2].strftime('%b %d')}",
        f"• Total Hot Dogs Logged: {sum(user_totals.values()):.1f}",
        f"• Entries: {sum(user_counts.values())}",
        f"• Unique Eaters: {len(unique_users)}",
        "\nKeep up the glizzological excellence."
    ]
    return "\n".join(lines)


def post_digest():
    start, end = get_last_week_range()
    logs = get_all_logs()  # Defined in google_sync.py
    message = format_digest(logs, start, end)

    try:
        client.chat_postMessage(channel=SLACK_CHANNEL, text=message)
        print("Digest posted successfully.")
    except SlackApiError as e:
        print(f"Slack error: {e.response['error']}")


if __name__ == "__main__":
    post_digest()
