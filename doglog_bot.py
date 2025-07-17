import os
from flask import Flask, request, jsonify, make_response
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from google_sync import log_entry, get_leaderboard_from_sheet, get_charity_summary

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
        print("[DEBUG] /doglog endpoint hit")

        data = request.form
        print(f"[DEBUG] Request data: {data}")

        text = data.get("text", "").strip()
        user_name = data.get("user_name", "Unknown User")
        print(f"[DEBUG] Parsed text: '{text}', user: '{user_name}'")

        if text.startswith("add"):
            print("[DEBUG] Handling add command")
            parts = text.split()
            print(f"[DEBUG] Split parts: {parts}")

            if len(parts) < 2:
                raise ValueError("Missing count for add command")

            count = float(parts[1])
            target_user = parts[2] if len(parts) > 2 else user_name
            print(f"[DEBUG] Logging {count} dog(s) for {target_user}")
            log_entry(target_user, count)

            message = f"{target_user} logged {count} dog(s). 🌭"

        elif text == "leaderboard":
            print("[DEBUG] Handling leaderboard command")
            leaderboard = get_leaderboard_from_sheet()
            message = leaderboard

        elif text == "charity":
            print("[DEBUG] Handling charity command")
            message = get_charity_summary()

        else:
            print("[DEBUG] Unrecognized command")
            message = "Try `/doglog add [count] [optional user]`, `/doglog leaderboard`, or `/doglog charity`"

        print(f"[DEBUG] Response message: {message}")

        return make_response(jsonify({
            "response_type": "in_channel",
            "text": message
        }), 200)

    except Exception as e:
        print(f"[ERROR] Exception in /doglog: {e}")
        return make_response(jsonify({
            "response_type": "ephemeral",
            "text": f"Error: {e}"
        }), 500)

if __name__ == "__main__":
    print("[INFO] Starting app...")
    app.run(host="0.0.0.0", port=5000)
