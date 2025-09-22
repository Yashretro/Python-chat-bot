from flask import Flask, render_template_string, request, make_response
import requests
import json
from datetime import datetime

app = Flask(__name__)

HTML = """
<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>Gemma 3B Chatbot</title>
  <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css' rel='stylesheet'>
  <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'>
  <style>
    body {
      background: linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%);
      min-height: 100vh;
      margin: 0;
      font-family: 'Segoe UI', Arial, sans-serif;
    }
    .chat-container {
      max-width: 600px;
      margin: 40px auto;
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 4px 24px rgba(0,0,0,0.08);
      padding: 0;
      display: flex;
      flex-direction: column;
      min-height: 70vh;
    }
    .chat-header {
      background: #0d6efd;
      color: #fff;
      padding: 18px 24px;
      border-top-left-radius: 16px;
      border-top-right-radius: 16px;
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .chat-header img {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #fff;
      object-fit: cover;
    }
    .chat-box {
      flex: 1;
      overflow-y: auto;
      background: #f1f3f4;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .user-msg, .bot-msg {
      display: flex;
      align-items: flex-end;
      gap: 8px;
      margin-bottom: 2px;
      animation: fadeIn 0.5s;
    }
    .user-msg {
      justify-content: flex-end;
    }
    .bot-msg {
      justify-content: flex-start;
    }
    .msg {
      padding: 10px 16px;
      border-radius: 18px;
      max-width: 70%;
      font-size: 1rem;
      box-shadow: 0 2px 8px rgba(0,0,0,0.04);
      transition: background 0.2s;
    }
    .user-msg .msg {
      background: #e7f1ff;
      color: #0d6efd;
      border-bottom-right-radius: 4px;
    }
    .bot-msg .msg {
      background: #e2e3e5;
      color: #212529;
      border-bottom-left-radius: 4px;
    }
    .timestamp {
      font-size: 0.8em;
      color: #888;
      margin: 0 4px;
      align-self: flex-end;
    }
    .chat-footer {
      background: #f8f9fa;
      padding: 12px 24px;
      border-bottom-left-radius: 16px;
      border-bottom-right-radius: 16px;
      text-align: center;
      font-size: 0.95em;
      color: #888;
    }
    .input-group {
      margin: 0;
    }
    #userInput {
      border-radius: 18px 0 0 18px;
      padding-left: 18px;
    }
    #sendBtn {
      border-radius: 0 18px 18px 0;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px);}
      to { opacity: 1; transform: translateY(0);}
    }
    @media (max-width: 700px) {
      .chat-container { max-width: 98vw; }
      .chat-box { padding: 12px; }
      .chat-header, .chat-footer { padding: 10px; }
    }
  </style>
</head>
<body>
  <div class='chat-container'>
    <div class='chat-header'>
      <img src='https://api.dicebear.com/7.x/bottts/svg?seed=Gemma' alt='Bot Avatar'>
      <span style='font-size:1.3em;font-weight:500;'>Gemma 3B Chatbot</span>
    </div>
    <div class='chat-box' id='chatBox'>
      {% if chat_history %}
        {% for entry in chat_history %}
          {% if entry.role == 'user' %}
            <div class='user-msg'>
              <span class='msg'>{{ entry.text }}</span>
              <span class='timestamp'>{{ entry.time }}</span>
              <i class='fa-solid fa-user'></i>
            </div>
          {% else %}
            <div class='bot-msg'>
              <img src='https://api.dicebear.com/7.x/bottts/svg?seed=Gemma' alt='Bot Avatar' style='width:28px;height:28px;'>
              <span class='msg'>{{ entry.text }}</span>
              <span class='timestamp'>{{ entry.time }}</span>
            </div>
          {% endif %}
        {% endfor %}
      {% endif %}
      <div id='loadingSpinner' style='display:none;' class='text-center'>
        <div class='spinner-border text-primary' role='status'>
          <span class='visually-hidden'>Loading...</span>
        </div>
      </div>
    </div>
    <form id='chatForm' method='post' autocomplete='off' style='padding:12px 24px;background:#fff;'>
      <div class='input-group'>
        <input type='text' class='form-control' name='user_input' id='userInput' placeholder='Type your message... 😊' autofocus required>
        <button class='btn btn-primary' type='submit' id='sendBtn'><i class='fa-solid fa-paper-plane'></i></button>
      </div>
    </form>
    <div class='chat-footer'>
      &copy; {{ year }} Gemma 3B Chatbot &mdash; Made by Yashretro
    </div>
  </div>
  <script src='https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js'></script>
  <script src='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/js/all.min.js'></script>
  <script>
    const chatBox = document.getElementById('chatBox');
    const chatForm = document.getElementById('chatForm');
    const loadingSpinner = document.getElementById('loadingSpinner');
    chatForm.addEventListener('submit', function(e) {
      loadingSpinner.style.display = 'block';
      setTimeout(() => {
        chatBox.scrollTop = chatBox.scrollHeight;
      }, 100);
    });
    window.onload = function() {
      chatBox.scrollTop = chatBox.scrollHeight;
    };
  </script>
</body>
</html>
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
    chat_history = []
    if request.cookies.get('chat_history'):
        try:
            chat_history = json.loads(request.cookies.get('chat_history'))
        except Exception:
            chat_history = []
    bot_reply = None
    if request.method == "POST":
        user_input = request.form.get("user_input")
        if user_input:
            chat_history.append({'role': 'user', 'text': user_input, 'time': datetime.now().strftime('%H:%M')})
            bot_reply = get_llm_response(user_input)
            chat_history.append({'role': 'bot', 'text': bot_reply, 'time': datetime.now().strftime('%H:%M')})
    resp = render_template_string(HTML, bot_reply=bot_reply, chat_history=chat_history, year=datetime.now().year)
    response = make_response(resp)
    response.set_cookie('chat_history', json.dumps(chat_history))
    return response

if __name__ == "__main__":
    app.run(debug=True)