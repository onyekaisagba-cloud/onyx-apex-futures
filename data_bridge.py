import pandas as pd
import logging
from yahooquery import Ticker

logger = logging.getLogger("OnyxApexData")

# Mapping Yahoo-style Futures Symbols to our Apex Standard
SYMBOL_MAP = {
    "/NQ": "NQ=F",
    "/ES": "ES=F",
    "/ZN": "ZN=F",
    "/6E": "EURUSD=X", # Using FX Spot as proxy for high-liquidity 6E flow
    "/CL": "CL=F",
    "/BTC": "BTC=F"
}

def get_futures_ohlcv(symbol, period="5d", interval="15m"):
    """
    Surgically retrieves OHLCV data for the designated contract.
    Standardizes the dataframe for the Onyx Apex Strategy module.
    """
    yahoo_symbol = SYMBOL_MAP.get(symbol)
    if not yahoo_symbol:
        logger.error(f"❌ Symbol {symbol} not recognized in APEX Map.")
        return None

    try:
        tk = Ticker(yahoo_symbol)
        # Pulling intraday data
        df = tk.history(period=period, interval=interval)
        
        if df.empty:
            logger.warning(f"⚠️ No data returned for {symbol}")
            return None

        # Clean index for multi-index responses
        if isinstance(df.index, pd.MultiIndex):
            df = df.xs(yahoo_symbol)

        # Standardizing column names to match our strategy module
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }, inplace=True)

        return df

    except Exception as e:
        logger.error(f"❌ Data Bridge failed for {symbol}: {e}")
        return None

if __name__ == "__main__":
    # Internal Test Call
    logger.info("Testing Apex Data Bridge for /NQ...")
    data = get_futures_ohlcv("/NQ")
    if data is not None:
        print(data.tail(5))
