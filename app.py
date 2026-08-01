import os
import time
import requests
import webbrowser
from threading import Timer
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Groq API Key
API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

chat_history = [
    {
        "role": "system",
        "content": (
            "Sən 'Atabəylər.Aİ' adlı ağıllı köməkçisisən. "
            "Səni Atabəy İmanzadə yaradıb. Əgər istifadəçi 'Səni kim yaradıb?' və ya bənzər sual verərsə, "
            "mütləq 'Məni Atabəy İmanzadə yaradıb!' deyə cavab ver. "
            "Azərbaycan dilində səlis, oxunaqlı, qrammatik baxımdan dəqiq və aydın cavablar ver."
        )
    }
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Atabəylər.Aİ</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, sans-serif; }
        html, body { height: 100%; width: 100%; background-color: #050505; color: #e3e3e3; overflow: hidden; position: fixed; top: 0; bottom: 0; left: 0; right: 0; }

        :root {
            --neon-green: #00ff66;
            --neon-glow: 0 0 12px rgba(0, 255, 102, 0.4);
            --border-green: rgba(0, 255, 102, 0.3);
        }

        .main-wrapper { display: flex; flex-direction: column; width: 100%; height: 100%; }

        .header { display: flex; align-items: center; justify-content: center; padding: 12px; background: #0a0a0a; border-bottom: 1px solid var(--border-green); box-shadow: var(--neon-glow); height: 65px; flex-shrink: 0; }
        .header-title { font-size: 22px; font-weight: bold; color: var(--neon-green); text-shadow: 0 0 10px rgba(0,255,102,0.7); letter-spacing: 1.5px; }

        .chat-container { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 16px; padding-bottom: 30px; }
        .message { display: flex; flex-direction: column; max-width: 88%; animation: fadeIn 0.3s ease; }
        .user-msg { align-self: flex-end; background-color: #0d1e12; border: 1px solid var(--border-green); padding: 10px 16px; border-radius: 18px 18px 4px 18px; color: #fff; box-shadow: 0 0 8px rgba(0, 255, 102, 0.15); font-size: 15px; word-break: break-word; }
        .bot-msg { align-self: flex-start; background-color: transparent; padding: 4px; color: #f0f0f0; line-height: 1.5; font-size: 15px; word-break: break-word; }
        
        .bot-avatar { font-weight: bold; color: var(--neon-green); margin-bottom: 6px; font-size: 15px; display: flex; align-items: center; gap: 6px; }

        .bottom-panel { background: #080808; border-top: 1px solid var(--border-green); padding: 10px 12px 15px 12px; flex-shrink: 0; width: 100%; position: relative; z-index: 10; }

        .input-card { background: #0c100d; border: 1px solid var(--border-green); border-radius: 28px; padding: 4px 8px 4px 16px; display: flex; align-items: center; gap: 8px; box-shadow: var(--neon-glow); }
        .input-card input { flex: 1; background: transparent; border: none; outline: none; color: white; font-size: 16px; padding: 10px 0; }
        .input-card input::placeholder { color: #50705a; }
        
        .action-btn { background: transparent; border: none; color: var(--neon-green); font-size: 18px; width: 38px; height: 38px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; }
        .action-btn:hover { background: rgba(0, 255, 102, 0.15); }
        .send-btn { background: var(--neon-green); color: #000; font-weight: bold; box-shadow: var(--neon-glow); }
        .listening { animation: pulse 1s infinite; color: #ff3333 !important; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.2); } 100% { transform: scale(1); } }
    </style>
</head>
<body>

    <div class="main-wrapper">
        <div class="header">
            <div class="header-title">Atabəylər.Aİ</div>
        </div>

        <div class="chat-container" id="chat">
            <div class="message bot-msg">
                <div class="bot-avatar">Atabəylər.Aİ</div>
                Salam! Süni intellekt köməkçiniz hazırdır. Sizə necə kömək edə bilərəm?
            </div>
        </div>

        <div class="bottom-panel">
            <div class="input-card">
                <input type="text" id="userInput" placeholder="Mesajınızı yazın və ya mikrofona toxunun..." onkeydown="if(event.key==='Enter') sendMessage()">
                <button class="action-btn" id="micBtn" onclick="toggleSpeech()"><i class="fa-solid fa-microphone"></i></button>
                <button class="action-btn send-btn" onclick="sendMessage()"><i class="fa-solid fa-arrow-up"></i></button>
            </div>
        </div>
    </div>

    <script>
        const chat = document.getElementById('chat');
        const userInput = document.getElementById('userInput');
        const micBtn = document.getElementById('micBtn');
        let recognition = null;
        let isListening = false;

        function appendUserMsg(msg) {
            chat.innerHTML += `<div class="message user-msg">${msg}</div>`;
            chat.scrollTop = chat.scrollHeight;
        }

        function appendBotMsg(msg) {
            chat.innerHTML += `
                <div class="message bot-msg">
                    <div class="bot-avatar">Atabəylər.Aİ</div>
                    ${msg}
                </div>`;
            chat.scrollTop = chat.scrollHeight;
        }

        async function sendMessage() {
            if (isListening) stopSpeech();

            const text = userInput.value.trim();
            if (!text) return;

            appendUserMsg(text);
            userInput.value = '';

            const lowerText = text.toLowerCase();
            if (lowerText.includes("şəkil yarat") || lowerText.includes("şəklini çək") || lowerText.includes("şəkil çek") || lowerText.includes("şəkil çək")) {
                appendBotMsg("Mən şəkil yaratmaq funksiyasına malik deyiləm, yalnız mətn əsaslı suallarınıza cavab verə bilərəm.");
                return;
            }

            const tempId = "loading_" + Date.now();
            chat.innerHTML += `<div class="message bot-msg" id="${tempId}"><div class="bot-avatar">Atabəylər.Aİ</div>Cavab hazırlanır...</div>`;
            chat.scrollTop = chat.scrollHeight;

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text})
                });
                const data = await res.json();
                const tempElem = document.getElementById(tempId);
                if (tempElem) tempElem.remove();
                appendBotMsg(data.reply);
            } catch (err) {
                const tempElem = document.getElementById(tempId);
                if (tempElem) tempElem.remove();
                appendBotMsg("⚠️ İnternet və ya server bağlantısında xəta baş verdi.");
            }
        }

        /* Səs Tanıma (Danışıq bitdikdə avtomatik dayanır) */
        function toggleSpeech() {
            if (isListening) {
                stopSpeech();
            } else {
                startSpeech();
            }
        }

        function startSpeech() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) return alert("Səs tanıma funksiyası brauzeriniz tərəfindən dəstəklənmir.");

            recognition = new SpeechRecognition();
            recognition.lang = 'az-AZ';
            recognition.continuous = false; // Danışıq bitdikdə avtomatik dayansın
            recognition.interimResults = false;

            recognition.onstart = () => {
                isListening = true;
                micBtn.classList.add('listening');
            };

            recognition.onresult = (e) => {
                const transcript = e.results[0][0].transcript;
                if (userInput.value) {
                    userInput.value += ' ' + transcript;
                } else {
                    userInput.value = transcript;
                }
            };

            recognition.onerror = () => stopSpeech();
            recognition.onend = () => stopSpeech();

            recognition.start();
        }

        function stopSpeech() {
            if (recognition) {
                try { recognition.stop(); } catch(e) {}
            }
            isListening = false;
            micBtn.classList.remove('listening');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    user_msg = data.get('message', '')

    if not user_msg:
        return jsonify({"reply": "Xahiş olunur bir mesaj daxil edin."})

    chat_history.append({"role": "user", "content": user_msg})
    model_name = "llama-3.3-70b-versatile"

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model_name, "messages": chat_history, "temperature": 0.3}

    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers)
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            reply = result["choices"][0]["message"]["content"]
            chat_history.append({"role": "assistant", "content": reply})
            return jsonify({"reply": reply})
        elif "error" in result:
            error_msg = result["error"].get("message", "Bilinməyən API xətası")
            return jsonify({"reply": f"⚠️ Groq API Xətası: {error_msg}"})
        else:
            return jsonify({"reply": "⚠️ Cavab alına bilmədi. Zəhmət olmasa bir daha cəhd edin."})

    except Exception as e:
        return jsonify({"reply": f"Xəta baş verdi: {str(e)}"})

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(port=5000)
