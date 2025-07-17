import os
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from monday_digest import get_digest_message
from google_sync import get_leaderboard_message, get_log_message

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "#doglog")

client = WebClient(token=SLACK_BOT_TOKEN)
app = Flask(__name__)

@app.route("/doglog", methods=["POST"])
def doglog():
    data = request.form
    text = data.get("text", "").strip().lower()
    command = text or "leaderboard"

    if command == "leaderboard":
        message = get_leaderboard_message()
    elif command == "log":
        message = get_log_message()
    elif command == "digest":
        message = get_digest_message()
    else:
        message = "Please enter a valid subcommand: leaderboard, log, or digest."

    try:
        client.chat_postMessage(channel=SLACK_CHANNEL, text=message)
    except SlackApiError as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"response_type": "in_channel", "text": "Posted!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
