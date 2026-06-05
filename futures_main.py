import os
import time
import logging
import requests
import pandas as pd
import data_bridge
import strategy_futures
import futures_engine 
from datetime import datetime
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OnyxApexMain")
onyx_tz = timezone('US/Eastern')

FUTURES_GRID = ["/NQ", "/ES", "/ZN", "/6E", "/CL", "/BTC"]

def run_apex_scan():
    logger.info(f"📡 ONYX APEX: Initiating Global Macro Scan...")
    
    for ticker in FUTURES_GRID:
        try:
            data = data_bridge.get_futures_ohlcv(ticker)
            if data is None or data.empty: continue
            
            audit = strategy_futures.run_strat_audit_futures(ticker, data)
            
            # Unified Gatekeeper (Filters out NEUTRAL/Incomplete setups)
            if audit['score'] >= 5.0 and audit['direction'] != "NEUTRAL":
                current_price = data['Close'].iloc[-1]
                atr = (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
                
                # Pass direction dynamically to resolve Long vs Short math
                exec_params = futures_engine.calculate_execution_levels(
                    ticker, current_price, atr, direction=audit['direction']
                )
                audit.update(exec_params) 
                
                try:
                    macro_intel = strategy_futures.get_gemini_macro_advisory(ticker, audit['score'])
                except AttributeError:
                    macro_intel = "Macro confluence data pending Gemini initialization."
                
                audit['ai_advisory'] = macro_intel
                dispatch_to_discord(audit)
        except Exception as e:
            logger.error(f"❌ Error scanning {ticker}: {e}")

def dispatch_to_discord(audit):
    webhook_url = os.getenv("DISCORD_APEX_WEBHOOK_URL")
    if not webhook_url: 
        logger.warning("❌ DISCORD_APEX_WEBHOOK_URL environment variable missing.")
        return

    timestamp = datetime.now(onyx_tz).strftime("%H:%M")
    spec = futures_engine.FUTURES_SPECS.get(audit['ticker'])
    if not spec: return
    
    display_name = data_bridge.SYMBOL_MAP.get(audit['ticker'], {}).get('alias', audit['ticker'])  
    full_risk = futures_engine.calculate_risk_params(audit['ticker'], audit['E'], audit['SL'])
    
    if not full_risk: return
    
    micro_val = spec['tick_value'] / 10 
    micro_risk = full_risk['ticks'] * micro_val
    
    content = (
        f"🏛️ **ONYX APEX | MACRO SNIPER SIGNAL**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"**PLATFORM TICKER:** `{display_name}` | **TIME:** `{timestamp} EST`\n"
        f"┣ **Directional Bias:** `{audit['direction']} ({audit['bias']})`\n"
        f"┣ **Strategic Score:** `{audit['score']}/10` (High Conviction)\n"
        f"┣ **Technical Thesis:** {audit['thesis']}\n"
        f"┣ ━━━━━━━━━━━━━━━━━━━━━━\n"
        f"┣ 🎯 **EXECUTION PARAMETERS**\n"
        f"┣ **Entry (E):** `{audit['E']}`\n"
        f"┣ **Stop Loss (SL):** `{audit['SL']}`\n"
        f"┣ **Take Profit (TP):** `{audit['TP']}`\n"
        f"┣ ━━━━━━━━━━━━━━━━━━━━━━\n"
        f"┣ ⚖️ **RISK ALLOCATION (PER 1.0 LOT)**\n"
        f"┣ **Standard ({display_name}):** `${full_risk['risk_per_con']}` Risk\n"
        f"┣ **Micro (0.10 Lot Proxy):** `${round(micro_risk, 2)}` Risk\n"
        f"┗ ━━━━━━━━━━━━━━━━━━━━━━\n"
        f"**AI Advisory:** *{audit['ai_advisory']}*"
    )
    
    try:
        res = requests.post(webhook_url, json={"content": content}, timeout=10)
        if res.status_code == 204:
            logger.info(f"✅ Multi-Contract Dispatch successful for {display_name}")
        else:
            logger.error(f"❌ Discord API returned error status: {res.status_code}")
    except Exception as e:
        logger.error(f"❌ Dispatch failed: {e}")

# --- THE LIVE ON-DEMAND WORKFLOW PIPELINE ---
def execute_system_heartbeat():
    """Run this diagnostic from the command line to verify end-to-end telemetry."""
    logger.info("🧪 [HEARTBEAT] Initiating active endpoint validation...")
    mock_audit = {
        "ticker": "/NQ",
        "score": 7.50,
        "direction": "SHORT",
        "bias": "DISTRIBUTION",
        "thesis": "TEST WORKFLOW DIAGNOSTIC: 15m 2-Down Breakdown verified with volume expansion.",
        "E": 18450.00,
        "SL": 18510.00,
        "TP": 18330.00,
        "ai_advisory": "Test pipeline diagnostic successful. Webhook execution valid."
    }
    dispatch_to_discord(mock_audit)

if __name__ == "__main__":
    # Runs a connection check to your Discord channel immediately upon script initialization
    execute_system_heartbeat()
    
    scheduler = BackgroundScheduler(timezone=onyx_tz)
    scheduler.add_job(run_apex_scan, 'interval', minutes=15, id='apex_scanner')
    scheduler.start()
    
    logger.info("🚀 ONYX APEX: Global Futures Engine Active | 15m Advisory Mode")
    try:
        while True:
            time.sleep(10) 
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("🛑 Onyx Apex shutting down...")
