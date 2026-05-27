import os
import time
import logging
import data_bridge
import strategy_futures
from datetime import datetime
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler
import requests

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OnyxApexMain")
onyx_tz = timezone('US/Eastern')

# 🎯 THE APEX MACRO GRID
FUTURES_GRID = ["/NQ", "/ES", "/ZN", "/6E", "/CL", "/BTC"]

def run_apex_scan():
    logger.info(f"📡 ONYX APEX: Initiating Global Macro Scan...")
    
    for ticker in FUTURES_GRID:
        # 1. Fetch Real-Time OHLCV
        data = data_bridge.get_futures_ohlcv(ticker)
        if data is None: continue
        
        # 2. Run High-Conviction Audit
        audit = strategy_futures.run_strat_audit_futures(ticker, data)
        
        # 3. Gatekeeper: Only dispatch if Score >= 5.0
        if audit['score'] >= 5.0:
            dispatch_to_discord(audit)
            # Future: add_to_db(audit) once setup_db is run

def dispatch_to_discord(audit):
    webhook_url = os.getenv("DISCORD_APEX_WEBHOOK_URL")
    if not webhook_url: return

    timestamp = datetime.now(onyx_tz).strftime("%H:%M")
    
    # Executive Briefing Format
    content = (
        f"🏛️ **ONYX APEX | MACRO SNIPER SIGNAL**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"**ASSET:** `{audit['ticker']}` | **TIME:** `{timestamp} EST`\n"
        f"┣ **Institutional Bias:** `{audit['bias']}`\n"
        f"┣ **Strategic Score:** `{audit['score']}/10` (High Conviction)\n"
        f"┣ **Technical Thesis:** {audit['thesis']}\n"
        f"┗ **Velocity (RVOL):** `{audit['rvol']}x` | **Status:** `{'🔥 FTFC ACTIVE' if audit['is_ftfc'] else '✅ STABLE'}`"
    )
    
    try:
        requests.post(webhook_url, json={"content": content}, timeout=10)
        logger.info(f"✅ Apex Dispatch successful for {audit['ticker']}")
    except Exception as e:
        logger.error(f"❌ Dispatch failed: {e}")

if __name__ == "__main__":
    # Initialize Scheduler for 15-minute high-velocity scans
    scheduler = BackgroundScheduler(timezone=onyx_tz)
    scheduler.add_job(run_apex_scan, 'interval', minutes=15, id='apex_scanner')
    
    scheduler.start()
    logger.info("🚀 ONYX APEX: Global Futures Engine Active | 15m Scan Interval")

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
