import os
import pytz
from datetime import datetime, timedelta
from google_sync import get_leaderboard_from_sheet
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import request, jsonify

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = "#doglog"  # change this if needed
TIMEZONE = pytz.timezone("America/New_York")

def format_digest(leaderboard):
    if not leaderboard:
        return "No hot dogs were logged this week. Sad!"

    lines = ["🌭 *Weekly DogLog Digest* 🌭\n"]
    for i, row in enumerate(leaderboard):
        name, count = row[0], float(row[1])
        lines.append(f"{i + 1}. {name} — {count:.1f} dogs")
    return "\n".join(lines)

def get_this_week_data(leaderboard):
    """Filter leaderboard data for the past 7 days based on timestamp if available."""
    # This is just placeholder logic — assumes you only keep total counts.
    # To do real weekly stats, you'll need per-entry timestamped logs from your sheet.
    return leaderboard

def post_digest():
    now = datetime.now(TIMEZONE)
    print(f"[{now}] Running Monday Digest")

    client = WebClient(token=SLACK_BOT_TOKEN)

    try:
        full_leaderboard = get_leaderboard_from_sheet()
        weekly_leaderboard = get_this_week_data(full_leaderboard)
        message = format_digest(weekly_leaderboard)

        response = client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text=message
        )
        print(f"Slack API response: {response.data}")
        return jsonify({"status": "success", "message": "Digest sent."})
    except SlackApiError as e:
        print(f"Slack API error: {e.response['error']}")
        return jsonify({"status": "error", "message": f"Slack error: {e.response['error']}"})
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"status": "error", "message": str(e)})
