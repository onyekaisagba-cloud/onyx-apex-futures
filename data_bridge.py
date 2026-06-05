import pandas as pd
import logging
from yahooquery import Ticker

logger = logging.getLogger("OnyxApexData")

# Mapping Yahoo-style Futures Symbols to our Apex Standard
SYMBOL_MAP = {
    "/NQ": {"yahoo": "NQ=F", "alias": "NAS100"},
    "/ES": {"yahoo": "ES=F", "alias": "US500"},
    "/CL": {"yahoo": "CL=F", "alias": "WTI"},
    "/6E": {"yahoo": "EURUSD=X", "alias": "EURUSD"},
    "/BTC": {"yahoo": "BTC=F", "alias": "BTCUSD"},
    "/ZN": {"yahoo": "ZN=F", "alias": "UST10Y"}
}

def get_futures_ohlcv(symbol, period="5d", interval="15m"):
    """
    Surgically retrieves OHLCV data for the designated contract.
    Standardizes the dataframe index and schema for the Onyx Apex Strategy module.
    """
    mapping = SYMBOL_MAP.get(symbol)
    if not mapping:
        logger.error(f"❌ Symbol {symbol} not recognized in APEX Map.")
        return None
    
    yahoo_ticker = mapping['yahoo']

    try:
        tk = Ticker(yahoo_ticker)
        df = tk.history(period=period, interval=interval)
        
        if df is None or df.empty:
            logger.warning(f"⚠️ No data returned for {symbol} ({yahoo_ticker})")
            return None

        # 🟢 FIX: Bulletproof Index Alignment
        # Handle cases where yahooquery returns a MultiIndex (symbol, date)
        if isinstance(df.index, pd.MultiIndex):
            df = df.xs(yahoo_ticker)
        else:
            # If it's a single index but still contains 'symbol' as a column or index metadata,
            # reset it to guarantee the datetime string becomes the primary workable index level.
            if 'date' in df.columns:
                df.set_index('date', inplace=True)
            elif df.index.name == 'date':
                pass # Already correctly positioned
            else:
                # Fallback to force clear indexing names
                df.reset_index(inplace=True)
                if 'date' in df.columns:
                    df.set_index('date', inplace=True)

        # Ensure index is parsed cleanly into datetime objects for chronological sorting
        df.index = pd.to_datetime(df.index)

        # Standardizing column names explicitly
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }, inplace=True)

        # Keep only the essential columns required by strategy_futures.py
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df[required_cols]

        return df

    except Exception as e:
        logger.error(f"❌ Data Bridge failed for {symbol}: {e}")
        return None

if __name__ == "__main__":
    # Internal Test Call
    logging.basicConfig(level=logging.INFO)
    logger.info("Testing Apex Data Bridge for /NQ...")
    data = get_futures_ohlcv("/NQ")
    if data is not None:
        print("\n📊 DATA BRIDGE SANITY CHECK SUCCESSFUL:")
        print(data.tail(5))
