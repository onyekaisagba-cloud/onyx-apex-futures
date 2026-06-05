# test_alert.py
import os
import requests
from dotenv import load_dotenv

# Load local variables if testing on your machine
load_dotenv()

def force_test_alert():
    # Looks for both variants to guarantee compatibility
    webhook_url = os.getenv("DISCORD_APEX_WEBHOOK_URL") or os.getenv("DISCORD_APEX_WEBHOOK")
    
    if not webhook_url:
        print("❌ CRITICAL: No webhook variable found in your environment setup.")
        return

    print(f"📡 Sending bypass test payload directly to target destination...")
    
    payload = {
        "content": (
            "🏛️ **ONYX APEX | TELEMETRY WORKFLOW TEST**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "STATUS: `🟢 PIPELINE ALIVE`\n"
            "THESIS: This is an on-demand diagnostic test bypassing the core strategy "
            "engine to verify communication structures. If you see this, your webhook is functional."
        )
    }
    
    try:
        res = requests.post(webhook_url, json=payload, timeout=10)
        if res.status_code == 204:
            print("✅ PIPELINE VALID: Test alert successfully accepted by server.")
        else:
            print(f"❌ PIPELINE ERROR: Server responded with status code {res.status_code}")
    except Exception as e:
        print(f"❌ PIPELINE FAILURE: Network execution error: {e}")

if __name__ == "__main__":
    force_test_alert()
