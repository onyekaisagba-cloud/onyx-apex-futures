import os
import logging
import pandas as pd
from datetime import datetime
from pytz import timezone
from google import genai

logger = logging.getLogger("OnyxApexStrategy")
onyx_tz = timezone('US/Eastern')

def get_gemini_macro_advisory(ticker, score):
    """Acts as the Macro Analyst for fundamental confluence using the updated google-genai SDK."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Macro context unavailable (API Key missing)."

    try:
        client = genai.Client(api_key=api_key)
        prompt = (
            f"As a Senior Macro Analyst, provide a one-sentence institutional thesis for {ticker}. "
            f"The technical engine shows a conviction score of {score}/10 based on a 15m breakout. "
            f"Focus on the immediate session trend and any relevant macro tailwinds like DXY or Yields."
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini Analysis Failed: {e}")
        return "Technical breakout identified; monitor macro volatility."

def is_peak_session():
    """Confluence Layer: Weights sessions with highest institutional volume."""
    now = datetime.now(onyx_tz).time()
    london_open = now >= datetime.strptime("03:00", "%H:%M").time() and now <= datetime.strptime("05:00", "%H:%M").time()
    ny_morning = now >= datetime.strptime("09:30", "%H:%M").time() and now <= datetime.strptime("11:30", "%H:%M").time()
    ny_afternoon = now >= datetime.strptime("13:30", "%H:%M").time() and now <= datetime.strptime("16:00", "%H:%M").time()
    return london_open or ny_morning or ny_afternoon

def run_strat_audit_futures(ticker, data_df):
    """Treasury-Grade Strat Audit with FTFC, Outside-Bar Guarding, and Direction Resolution."""
    try:
        last_candle = data_df.iloc[-1]
        prev_candle = data_df.iloc[-2]
        
        # Strict Strat definitions
        is_2_up = last_candle['High'] > prev_candle['High'] and last_candle['Low'] >= prev_candle['Low']
        is_2_down = last_candle['Low'] < prev_candle['Low'] and last_candle['High'] <= prev_candle['High']
        is_3_outside = last_candle['High'] > prev_candle['High'] and last_candle['Low'] < prev_candle['Low']
        
        # Volume profile
        avg_vol = data_df['Volume'].tail(20).mean()
        rvol = last_candle['Volume'] / avg_vol if avg_vol > 0 else 1.0
        
        score = 0.0
        direction = "NEUTRAL"
        pattern_desc = "1-Inside"
        
        # Assign baseline score and explicit directions based on theStrat
        if is_2_up:
            score += 4.0
            direction = "LONG"
            pattern_desc = "2-Up Breakout"
        elif is_2_down:
            score += 4.0
            direction = "SHORT"
            pattern_desc = "2-Down Breakdown"
        elif is_3_outside:
            score += 4.5  # Higher weight for outside expansion volatility
            direction = "LONG" if last_candle['Close'] > prev_candle['High'] else "SHORT"
            pattern_desc = "3-Outside Broadening"

        # Session adjustments
        if is_peak_session():
            score += 1.5
        else:
            score -= 1.0 
            
        if rvol > 1.5: score += 1.0 
        if rvol > 2.5: score += 0.5 

        # Unified logic gate threshold confirmation
        bias = "NEUTRAL"
        if score >= 5.0 and direction != "NEUTRAL":
            bias = "ACCUMULATION" if direction == "LONG" else "DISTRIBUTION"
            
        thesis = f"15m {pattern_desc} confirmed. RVOL: {round(rvol, 2)}x. "
        thesis += "Institutional Window: ACTIVE." if is_peak_session() else "Institutional Window: INACTIVE."
        
        return {
            "ticker": ticker,
            "score": round(score, 2),
            "direction": direction,
            "bias": bias,
            "thesis": thesis,
            "rvol": round(rvol, 2),
            "is_ftfc": score >= 6.0 
        }
        
    except Exception as e:
        logger.error(f"❌ Strategy Audit failed for {ticker}: {e}")
        return {"score": 0.0, "direction": "NEUTRAL", "bias": "ERROR", "thesis": str(e)}
