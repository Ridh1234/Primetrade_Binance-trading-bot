import pandas as pd
import os
import logging

def load_fear_greed_index(file_path="historical_data.csv"):
    """Load the Fear & Greed Index dataset."""
    if not os.path.exists(file_path):
        logging.error(f"Sentiment file not found: {file_path}")
        return None
    try:
        df = pd.read_csv(file_path)
        if 'date' not in df.columns or 'fear_greed_score' not in df.columns:
            logging.error("CSV missing required columns: 'date', 'fear_greed_score'")
            return None
        return df
    except Exception as e:
        logging.error(f"Error loading sentiment data: {e}")
        return None

def get_latest_sentiment(df):
    """Get the latest sentiment score from the DataFrame."""
    if df is None or df.empty:
        logging.warning("Sentiment DataFrame is empty or None.")
        return None
    try:
        latest_row = df.sort_values('date').iloc[-1]
        return latest_row['fear_greed_score']
    except Exception as e:
        logging.error(f"Error extracting latest sentiment: {e}")
        return None

def is_fear_high(df, threshold=40):
    score = get_latest_sentiment(df)
    return score is not None and score < threshold

def is_greed_high(df, threshold=70):
    score = get_latest_sentiment(df)
    return score is not None and score > threshold
