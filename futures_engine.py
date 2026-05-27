import os
import logging
import requests
from datetime import datetime
from pytz import timezone

# Setup Institutional Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OnyxApex")

# 🟢 CONTRACT SPECIFICATIONS (Treasury Grade)
FUTURES_SPECS = {
    "/NQ": {"name": "Nasdaq 100", "tick_size": 0.25, "tick_value": 5.00, "micro": "/MNQ"},
    "/ES": {"name": "S&P 500", "tick_size": 0.25, "tick_value": 12.50, "micro": "/MES"},
    "/ZN": {"name": "10Y Note", "tick_size": 0.015625, "tick_value": 15.625, "micro": "/MYM"},
    "/6E": {"name": "Euro FX", "tick_size": 0.00005, "tick_value": 6.25, "micro": "/M6E"},
    "/CL": {"name": "Crude Oil", "tick_size": 0.01, "tick_value": 10.00, "micro": "/MCL"},
    "/BTC": {"name": "Bitcoin", "tick_size": 5.00, "tick_value": 25.00, "micro": "/MBT"}
}

def get_tick_rounded_price(price, tick_size):
    """Surgically rounds price to the nearest valid exchange tick."""
    return round(price / tick_size) * tick_size

def calculate_execution_levels(symbol, current_price, atr):
    """
    Calculates E, SL, and TP for the Apex Build.
    Uses a 1.5x ATR for SL and a 1:2 Risk/Reward for TP.
    """
    spec = FUTURES_SPECS.get(symbol)
    if not spec:
        return {"E": current_price, "SL": 0, "TP": 0}

    tick_size = spec['tick_size']
    
    # Entry is set at current market breakout price
    entry = get_tick_rounded_price(current_price, tick_size)
    
    # SL Calculation (1.5x ATR Volatility)
    sl_distance = atr * 1.5
    stop_loss = get_tick_rounded_price(entry - sl_distance, tick_size)
    
    # TP Calculation (1:2.0 Reward Ratio)
    tp_distance = (entry - stop_loss) * 2.0
    take_profit = get_tick_rounded_price(entry + tp_distance, tick_size)
    
    return {
        "E": entry,
        "SL": stop_loss,
        "TP": take_profit
    }

def calculate_risk_params(symbol, entry, stop):
    """Calculates tick distance and dollar risk per contract."""
    spec = FUTURES_SPECS.get(symbol)
    if not spec: return None
    
    tick_distance = abs(entry - stop) / spec['tick_size']
    dollar_risk = tick_distance * spec['tick_value']
    
    return {
        "ticks": int(tick_distance),
        "risk_per_con": round(dollar_risk, 2)
    }

# --- REMAINING UTILITIES PRESERVED ---

if __name__ == "__main__":
    scheduler = BackgroundScheduler(timezone=onyx_tz)
    scheduler.add_job(run_apex_scan, 'interval', minutes=15, id='apex_scanner')
    
    scheduler.start()
    logger.info("🚀 ONYX APEX: Global Futures Engine Active | 15m Advisory Mode")

    # 🟢 CRITICAL: This loop keeps the Render instance alive!
    try:
        while True:
            time.sleep(10) # Reduced from 60 to 10 for better responsiveness
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
