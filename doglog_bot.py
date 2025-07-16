from flask import Flask, request, jsonify
from collections import defaultdict

app = Flask(__name__)
doglog_counts = defaultdict(int)

@app.route("/doglog", methods=["POST"])
def doglog():
    user_name = request.form.get("user_name")
    text = request.form.get("text", "").strip().lower()

    if text.startswith("add"):
        try:
            count = int(text.split("add")[1].strip())
            doglog_counts[user_name] += count
            return jsonify({
                "response_type": "in_channel",
                "text": f":hotdog: {user_name} has now logged {doglog_counts[user_name]} hot dogs!"
            })
        except (IndexError, ValueError):
            return jsonify({"text": "Usage: /doglog add [number]"})

    elif text.startswith("leaderboard"):
        if not doglog_counts:
            return jsonify({"text": "No hot dogs logged yet!"})

        sorted_board = sorted(doglog_counts.items(), key=lambda x: -x[1])
        leaderboard_text = "\n".join(
            [f"{i+1}. {name} — {count} 🌭" for i, (name, count) in enumerate(sorted_board)]
        )
        return jsonify({
            "response_type": "in_channel",
            "text": "*🌭 DogLog Leaderboard:*\n" + leaderboard_text
        })

    else:
        return jsonify({
            "text": "Try:\n• /doglog add [number]\n• /doglog leaderboard"
        })

if __name__ == "__main__":
    app.run(port=3000)
