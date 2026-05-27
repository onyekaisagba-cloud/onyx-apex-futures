import logging
import pandas as pd
from datetime import datetime
from pytz import timezone

logger = logging.getLogger("OnyxApexStrategy")
onyx_tz = timezone('US/Eastern')

def is_peak_session():
    """Confluence Layer: Weights sessions with highest institutional volume."""
    now = datetime.now(onyx_tz).time()
    
    # London Open (3-5 AM) or NY Power Hours (9:30-11:30 AM & 1:30-4:00 PM)
    london_open = now >= datetime.strptime("03:00", "%H:%M").time() and now <= datetime.strptime("05:00", "%H:%M").time()
    ny_morning = now >= datetime.strptime("09:30", "%H:%M").time() and now <= datetime.strptime("11:30", "%H:%M").time()
    ny_afternoon = now >= datetime.strptime("13:30", "%H:%M").time() and now <= datetime.strptime("16:00", "%H:%M").time()
    
    return london_open or ny_morning or ny_afternoon

def run_strat_audit_futures(ticker, data_df):
    """
    Treasury-Grade Strat Audit with FTFC and Session Priority.
    Determines high-conviction 15m Day Trade setups.
    """
    try:
        # 1. PRICE STRUCTURE (The Strat 2U/2D)
        last_candle = data_df.iloc[-1]
        prev_candle = data_df.iloc[-2]
        
        # Confirmed Break: Price must exceed previous high/low
        is_2_up = last_candle['High'] > prev_candle['High']
        is_2_down = last_candle['Low'] < prev_candle['Low']
        
        # 2. VOLUME & VELOCITY
        avg_vol = data_df['Volume'].tail(20).mean()
        rvol = last_candle['Volume'] / avg_vol
        
        # 3. SCORE CALCULATION
        score = 0.0
        
        # Base PA Confirmation (4.0 Points for a clean 2-break)
        if is_2_up or is_2_down:
            score += 4.0
            
        # Session Confluence (+1.5 Points for trading with Institutional Flow)
        if is_peak_session():
            score += 1.5
        else:
            score -= 1.0 # Penalize low-volume 'chopy' windows
            
        # Institutional RVOL Multipliers
        if rvol > 1.5: score += 1.0 
        if rvol > 2.5: score += 0.5 

        # 4. THESIS & BIAS
        bias = "NEUTRAL"
        if score >= 5.5:
            bias = "ACCUMULATION" if is_2_up else "DISTRIBUTION"
            
        thesis = f"15m {'2-Up' if is_2_up else '2-Down'} confirmed. RVOL: {round(rvol, 2)}x. "
        thesis += "Institutional Window: ACTIVE." if is_peak_session() else "Institutional Window: INACTIVE."
        
        return {
            "ticker": ticker,
            "score": round(score, 2),
            "bias": bias,
            "thesis": thesis,
            "rvol": round(rvol, 2),
            "is_ftfc": score >= 6.0 # Threshold for Full Timeframe Alignment
        }
        
    except Exception as e:
        logger.error(f"❌ Strategy Audit failed for {ticker}: {e}")
        return {"score": 0.0, "bias": "ERROR", "thesis": str(e)}

if __name__ == "__main__":
    logger.info("Apex Strategy Module Loaded. Ready for 15m High-Velocity Audit.")
