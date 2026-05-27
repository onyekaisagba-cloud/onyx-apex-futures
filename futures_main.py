import os
import time
import logging
import requests
import data_bridge
import strategy_futures
import futures_engine 
from datetime import datetime
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OnyxApexMain")
onyx_tz = timezone('US/Eastern')

# 🎯 THE APEX MACRO GRID (Option B: Scan Truth only)
FUTURES_GRID = ["/NQ", "/ES", "/ZN", "/6E", "/CL", "/BTC"]

def run_apex_scan():
    logger.info(f"📡 ONYX APEX: Initiating Global Macro Scan...")
    
    for ticker in FUTURES_GRID:
        try:
            # 1. Fetch Real-Time OHLCV
            data = data_bridge.get_futures_ohlcv(ticker)
            if data is None or data.empty: continue
            
            # 2. Run High-Conviction Audit
            audit = strategy_futures.run_strat_audit_futures(ticker, data)
            
            # 3. Gatekeeper: Only dispatch if Score >= 5.0
            if audit['score'] >= 5.0:
                current_price = data['Close'].iloc[-1]
                # Calculate ATR for SL/TP
                atr = (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
                
                exec_params = futures_engine.calculate_execution_levels(ticker, current_price, atr)
                audit.update(exec_params) 
                
                # AI Advisory Hook (Safeguarded)
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
    if not webhook_url: return

    timestamp = datetime.now(onyx_tz).strftime("%H:%M")
    
    spec = futures_engine.FUTURES_SPECS.get(audit['ticker'])
    if not spec: return
    
    micro_ticker = spec.get('micro', 'N/A')
    full_risk = futures_engine.calculate_risk_params(audit['ticker'], audit['E'], audit['SL'])
    
    # Lot Size terminology for Star Trader / PU Prime
    micro_val = spec['tick_value'] / 10 
    micro_risk = full_risk['ticks'] * micro_val
    display_name = data_bridge.SYMBOL_MAP.get(audit['ticker'], {}).get('alias', audit['ticker'])  
    
    content = (
        f"🏛️ **ONYX APEX | MACRO SNIPER SIGNAL**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"**PLATFORM TICKER:** `{display_name}` | **TIME:** `{timestamp} EST`\n"
        f"┣ **Institutional Bias:** `{audit['bias']}`\n"
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
        requests.post(webhook_url, json={"content": content}, timeout=10)
        logger.info(f"✅ Multi-Contract Dispatch successful for {display_name}")
    except Exception as e:
        logger.error(f"❌ Dispatch failed: {e}")

if __name__ == "__main__":
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
