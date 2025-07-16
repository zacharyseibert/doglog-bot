# monday_digest.py

import os
import pytz
from datetime import datetime
from flask import request, jsonify
from google_sync import get_leaderboard_from_sheet
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = "#doglog"
TIMEZONE = pytz.timezone("America/New_York")

def format_digest(leaderboard):
    if not leaderboard:
        return "No hot dogs were logged this week. Sad!"
    lines = ["🌭 *Weekly DogLog Digest* 🌭\n"]
    for i, row in enumerate(leaderboard):
        name, count = row[0], float(row[1])
        lines.append(f"{i + 1}. {name} — {count:.1f} dogs")
    return "\n".join(lines)

def post_digest():
    now = datetime.now(TIMEZONE)
    print(f"[{now}] Starting digest post...")
    
    if not SLACK_BOT_TOKEN:
        print("SLACK_BOT_TOKEN is missing!")
        return jsonify({"error": "Missing Slack token"}), 500

    client = WebClient(token=SLACK_BOT_TOKEN)

    try:
        leaderboard = get_leaderboard_from_sheet()
        print(f"Leaderboard: {leaderboard}")

        message = format_digest(leaderboard)
        print(f"Formatted Message:\n{message}")

        response = client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text=message
        )
        print(f"Slack API response: {response.data}")
        return jsonify({"status": "success", "message": "Digest sent."})
    except SlackApiError as e:
        print(f"Slack API error: {e.response['error']}")
        return jsonify({"status": "error", "message": f"Slack error: {e.response['error']}"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
