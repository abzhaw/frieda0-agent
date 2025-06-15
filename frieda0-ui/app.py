import os
from flask import Flask, request, jsonify, render_template
from nearai import AgentClient

app = Flask(__name__)

# 1) Instantiate the NEAR-AI client here, before your route handlers:
AGENT_PATH = os.path.expanduser("~/.nearai/registry/normalfrog4679.near/frieda0/0.0.1")
client = AgentClient(agent_path=AGENT_PATH, local=True)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")
    reply = client.chat(user_msg)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
