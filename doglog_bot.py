import os
import json
import base64
from flask import Flask, request, jsonify
from slack_sdk.webhook import WebhookClient
from google_sync import log_entry, get_leaderboard_from_sheet

app = Flask(__name__)

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]
SLACK_COMMAND_TOKEN = os.environ["SLACK_COMMAND_TOKEN"]

@app.route("/doglog", methods=["POST"])
def doglog():
    token = request.form.get("token")
    if token != SLACK_COMMAND_TOKEN:
        return "Unauthorized", 403

    user = request.form.get("user_name")
    text = request.form.get("text", "").strip().lower()

    if text == "leaderboard":
        leaderboard = get_leaderboard_from_sheet()
        message = "*Current Leaderboard:*\n"
        for i, (name, count) in enumerate(leaderboard, start=1):
            message += f"{i}. {name} – {count} 🌭\n"
        return jsonify({"response_type": "in_channel", "text": message})

    try:
        count = float(text)
    except ValueError:
        return "Please enter a valid number of hot dogs."

    log_entry(user, count)

    webhook = WebhookClient(SLACK_WEBHOOK_URL)
    webhook.send(text=f":hotdog: {user} logged {count} hot dog(s)!")

    return jsonify({"response_type": "in_channel", "text": f"{user} logged {count} hot dog(s)! 🌭"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
