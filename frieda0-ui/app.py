import os
import shlex
import subprocess

from flask import Flask, request, render_template_string

AGENT_PATH = os.path.expanduser("~/.nearai/registry/normalfrog4679.near/frieda0/0.0.1")

TEMPLATE = """
<!doctype html>
<title>Frieda Chat</title>
<form method=post>
  <input name=q placeholder="Ask Frieda…" size=60 autofocus>
  <input type=submit value=Send>
</form>
{% if reply %}
  <h3>Frieda:</h3>
  <pre>{{ reply }}</pre>
{% endif %}
"""

app = Flask(__name__)

def query_agent(prompt: str) -> str:
    """
    Calls the NEAR AI CLI to run a single task against your local agent
    and returns the assistant’s reply.
    """
    cmd = (
        f"nearai agent task "
        f"--agent {AGENT_PATH} "
        f"--task {shlex.quote(prompt)} "
        f"--local"
    )
    # run the CLI, capture stdout
    output = subprocess.check_output(shlex.split(cmd), text=True)
    # The CLI prints something like “Assistant: <the answer>\nTask completed…”
    # We’ll grab everything after the first “Assistant:”
    if "Assistant:" in output:
        return output.split("Assistant:", 1)[1].strip()
    return output.strip()

@app.route("/", methods=("GET","POST"))
def home():
    reply = None
    if request.method == "POST":
        user_q = request.form["q"]
        reply = query_agent(user_q)
    return render_template_string(TEMPLATE, reply=reply)

if __name__ == "__main__":
    # install Flask in your .venv: pip install flask
    app.run(port=5000, debug=True)
