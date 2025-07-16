from flask import Flask, request, jsonify
from leaderboard import init_db, add_hotdogs, get_total, get_leaderboard

app = Flask(__name__)
init_db()

@app.route("/doglog", methods=["POST"])
def doglog():
    user_name = request.form.get("user_name")
    text = request.form.get("text", "").strip().lower()

    if text.startswith("add"):
        try:
            count = int(text.split("add")[1].strip())
            add_hotdogs(user_name, count)
            total = get_total(user_name)
            return jsonify({
                "response_type": "in_channel",
                "text": f":hotdog: {user_name} has now logged {total} hot dogs!"
            })
        except (IndexError, ValueError):
            return jsonify({"text": "Usage: /doglog add [number]"})

    elif text.startswith("leaderboard"):
        rows = get_leaderboard()
        if not rows:
            return jsonify({"text": "No hot dogs logged yet!"})

        leaderboard_text = "\n".join(
            [f"{i+1}. {name} — {count} 🌭" for i, (name, count) in enumerate(rows)]
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
    import os
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
