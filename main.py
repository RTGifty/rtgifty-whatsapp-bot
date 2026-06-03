from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN = "rtgifty123"

user_sessions = {}

def send_message(to, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    requests.post(url, headers=headers, json=data)

@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return challenge
    return "Invalid token", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    try:
        entry = data["entry"][0]["changes"][0]["value"]
        message = entry["messages"][0]
        from_number = message["from"]
        msg_text = message["text"]["body"].strip().lower()
        
        contact_name = entry.get("contacts", [{}])[0].get("profile", {}).get("name", "Sir/Madam")
        first_name = contact_name.split()[0] if contact_name else "Sir/Madam"
        
        session = user_sessions.get(from_number, {"step": "start"})
        
        if session["step"] == "start":
            send_message(from_number, f"Sure {first_name}! 😊\n\nSingle art வேணுமா இல்ல Couple art வேணுமா?\n\n1️⃣ Single\n2️⃣ Couple")
            user_sessions[from_number] = {"step": "art_type", "name": first_name}
            
        elif session["step"] == "art_type":
            if "single" in msg_text or "1" in msg_text:
                send_message(from_number, "உங்கள் Location மற்றும் Delivery Date சொல்லுங்க 📍📅")
                user_sessions[from_number] = {**session, "step": "location", "art_type": "single"}
            elif "couple" in msg_text or "2" in msg_text:
                send_message(from_number, "உங்கள் Location மற்றும் Delivery Date சொல்லுங்க 📍📅")
                user_sessions[from_number] = {**session, "step": "location", "art_type": "couple"}
            else:
                send_message(from_number, "Single அல்லது Couple என்று சொல்லுங்க 😊")
                
        elif session["step"] == "location":
            if "price" in msg_text or "விலை" in msg_text or "cost" in msg_text:
                send_message(from_number, "நாங்கள் 2 variants வச்சிருக்கோம்:\n\n📦 18 inches - ₹2,999\n📦 24 inches - ₹3,999")
            else:
                send_message(from_number, f"நன்றி! 😊\n\nஒரு Photo, பெயர், முழு Address மற்றும் Contact Number அனுப்புங்க 📸")
                user_sessions[from_number] = {**session, "step": "details", "location": msg_text}
                
        elif session["step"] == "details":
            send_message(from_number, f"Details கிடைச்சது! ✅\n\nOrder confirm பண்ண 50% Advance Pay பண்ணுங்க 💰\n\nUPI: your-upi-id@bank")
            user_sessions[from_number] = {**session, "step": "payment"}
            
        elif session["step"] == "payment":
            send_message(from_number, "✅ Order Confirmed!\n\nஉங்கள் order process ஆகுது. Delivery date-ல் deliver பண்றோம் 🎨")
            user_sessions[from_number] = {"step": "start"}
            
    except Exception as e:
        print(f"Error: {e}")
    
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
