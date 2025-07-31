import os
from flask import Flask, request, jsonify, make_response
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from google_sync import (
    log_entry,
    get_leaderboard_from_sheet,
    get_charity_summary,
    get_stats_summary,
    get_keeper_summary  # NEW
)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
if not SLACK_BOT_TOKEN:
    raise EnvironmentError("Missing SLACK_BOT_TOKEN environment variable")

client = WebClient(token=SLACK_BOT_TOKEN)
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "DogLog is awake!", 200

@app.route("/doglog", methods=["POST"])
def doglog():
    try:
        data = request.form
        text = data.get("text", "").strip()
        user_name = data.get("user_name", "Unknown User")

        if text.startswith("add"):
            parts = text.split()
            if len(parts) < 2:
                raise ValueError("Missing count for add command")
            count = float(parts[1])
            target_user = parts[2] if len(parts) > 2 else user_name
            log_entry(target_user, count)
            message = f"{target_user} logged {count} dog(s). 🌭"

        elif text == "leaderboard":
            message = get_leaderboard_from_sheet()

        elif text == "charity":
            message = get_charity_summary()

        elif text == "stats":
            message = get_stats_summary()

        elif text == "keeper":
            message = get_keeper_summary()

        else:
            message = (
                "Try `/doglog add [count] [optional user]`, "
                "`/doglog leaderboard`, `/doglog charity`, `/doglog stats`, or `/doglog keeper`"
            )

        return make_response(jsonify({
            "response_type": "in_channel",
            "text": message
        }), 200)

    except Exception as e:
        return make_response(jsonify({
            "response_type": "ephemeral",
            "text": f"Error: {e}"
        }), 500)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
