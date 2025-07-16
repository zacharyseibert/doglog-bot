import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import Flask, request, jsonify
from google_sync import log_entry, get_total_from_sheet, get_leaderboard_from_sheet, get_all_logs_from_sheet

app = Flask(__name__)
SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL = "#doglog"
client = WebClient(token=SLACK_TOKEN)

@app.route("/doglog", methods=["POST"])
def doglog():
    user = request.form.get("user_name")
    text = request.form.get("text")
    try:
        count = float(text)
        log_entry(user, count)
        return jsonify(response_type="in_channel", text=f"{user} logged {count} hot dog(s)! 🌭")
    except ValueError:
        return jsonify(response_type="ephemeral", text="Please enter a valid number of hot dogs.")

@app.route("/digest-trigger", methods=["GET"])
def digest_trigger():
    token = request.args.get("token")
    if token != os.environ.get("DIGEST_TRIGGER_TOKEN"):
        return jsonify(status="error", message="Unauthorized"), 403
    from monday_digest import post_digest
    return jsonify(post_digest())

if __name__ == "__main__":
app.run(host="0.0.0.0", port=5000, debug=True)
