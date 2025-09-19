from flask import Flask, render_template_string, request
import requests
import json

app = Flask(__name__)

HTML = """
<!doctype html>
<title>LLM Chatbot</title>
<h2>Chat with Gemma 3B!</h2>
<form method="post">
  <input type="text" name="user_input" autofocus>
  <input type="submit" value="Send">
</form>
{% if bot_reply %}
  <div><b>Bot:</b> {{ bot_reply }}</div>
{% endif %}
"""

def get_llm_response(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "gemma3:1b",
        "prompt": prompt,
        "stream": True
    }
    response = requests.post(url, json=payload, stream=True)
    reply = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode('utf-8'))
            if "response" in data:
                reply += data["response"]
    return reply

@app.route("/", methods=["GET", "POST"])
def chat():
    bot_reply = None
    if request.method == "POST":
        user_input = request.form.get("user_input")
        bot_reply = get_llm_response(user_input)
    return render_template_string(HTML, bot_reply=bot_reply)

if __name__ == "__main__":
    app.run(debug=True)