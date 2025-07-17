import os
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from google_sync import log_entry, get_leaderboard_from_sheet

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
DEFAULT_CHANNEL = os.environ.get("SLACK_CHANNEL", "#doglog")

client = WebClient(token=SLACK_BOT_TOKEN)
app = Flask(__name__)

@app.route("/doglog", methods=["POST"])
def doglog():
    data = request.form
    user_name = data.get("user_name", "unknown")
    text = data.get("text", "").strip()
    channel_id = data.get("channel_id", DEFAULT_CHANNEL)

    if text.lower().startswith(("add", "log")):
        parts = text.split()
        if len(parts) == 2:
            # /doglog add 3
            if parts[1].replace('.', '', 1).isdigit():
                target_user = user_name
                count = float(parts[1])
            else:
                return jsonify({"text": "Please specify a valid number."}), 200
        elif len(parts) == 3:
            # /doglog add drewbie 4
            target_user = parts[1]
            if parts[2].replace('.', '', 1).isdigit():
                count = float(parts[2])
            else:
                return jsonify({"text": "Please specify a valid number."}), 200
        else:
            return jsonify({"text": "Usage: `/doglog add [user] <count>`"}), 200

        log_entry(target_user, count)
        message = f"🐶 {target_user} logged {count:.1f} dogs!"
    elif text.lower() == "leaderboard" or text == "":
        leaderboard = get_leaderboard_from_sheet()
        lines = ["🏆 DogLog Leaderboard 🐶"]
        for i, (user, count) in enumerate(leaderboard, start=1):
            lines.append(f"{i}. {user}: {count:.1f} dogs")
        message = "\n".join(lines)
    else:
        message = "Please enter a valid subcommand: `add` or `leaderboard`."

    try:
        client.chat_postMessage(channel=channel_id, text=message)
    except SlackApiError as e:
        return jsonify({"error": str(e)}), 500

    return "", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
