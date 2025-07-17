import os
from flask import Flask, request, jsonify, make_response
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from google_sync import log_entry, get_leaderboard_from_sheet

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
client = WebClient(token=SLACK_BOT_TOKEN)

app = Flask(__name__)

@app.route("/doglog", methods=["POST"])
def doglog():
    try:
        data = request.form
        print(f"[DEBUG] Incoming Slack data: {data}")

        text = data.get("text", "").strip()
        user_name = data.get("user_name", "Unknown User")

        if text.startswith("add"):
            parts = text.split()
            print(f"[DEBUG] add parts: {parts}")
            try:
                count = float(parts[1])
                target_user = parts[2] if len(parts) > 2 else user_name
                log_entry(target_user, count)
                message = f"{target_user} logged {count} dog(s). 🌭"
            except (IndexError, ValueError) as e:
                print(f"[ERROR] Failed to parse add command: {e}")
                message = "Usage: `/doglog add [count] [optional user]`"
        elif text == "leaderboard":
            print("[DEBUG] Fetching leaderboard")
            leaderboard = get_leaderboard_from_sheet()
            message = leaderboard
        else:
            print("[DEBUG] Unknown command")
            message = "Try `/doglog add [count] [optional user]` or `/doglog leaderboard`"

        return make_response(jsonify({
            "response_type": "in_channel",
            "text": message
        }), 200)

    except Exception as e:
        print(f"[FATAL ERROR] Unexpected exception: {e}")
        return make_response(jsonify({
            "response_type": "ephemeral",
            "text": f"An error occurred: {e}"
        }), 500)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
