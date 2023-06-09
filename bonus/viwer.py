import pandas as pd
import mplfinance as mpf
from typing import List, Tuple


# Read data from CSV file
data = pd.read_csv('trade_training-datasets/training-set_USDT_BTC-1.csv')

# Convert the 'date' column to pandas DateTime format
data['date'] = pd.to_datetime(data['date'])

# Check for variations in the 'volume' column name
volume_column = next((col for col in data.columns if col.lower().strip() == 'volume'), None)
if volume_column is None:
    raise ValueError("Volume column not found in the input DataFrame.")

# Calculate MACD and signal line
def calculate_macd(data, short_period, long_period, signal_period):
    ema_short = data['close'].rolling(window=short_period, min_periods=0).mean()
    ema_long = data['close'].rolling(window=long_period, min_periods=0).mean()
    macd_line = ema_short - ema_long
    signal_line = macd_line.rolling(window=signal_period, min_periods=0).mean()
    histogram = macd_line - signal_line
    return ema_short, ema_long, macd_line.tolist(), signal_line.tolist(), histogram.tolist()

# Set the period values
short_period = 12
long_period = 26
signal_period = 20

# Calculate MACD and signal line
ema_short, ema_long, macd_line, signal_line, histogram = calculate_macd(data, short_period, long_period, signal_period)

# Prepare the data for candlestick visualization
data_for_candlestick = data[['date', 'open', 'high', 'low', 'close', volume_column]]
data_for_candlestick.set_index('date', inplace=True)
data_for_candlestick.index.name = 'Date'

# Plotting the trading graph with candlestick style and MACD indicator
mpf.plot(data_for_candlestick, type='candle', style='yahoo', title='Trading Graph with MACD Indicator',
         ylabel='Price', ylabel_lower='MACD', figsize=(10, 6), mav=(12, 26), volume=True,
         addplot=[mpf.make_addplot(ema_short, panel=1, color='blue', secondary_y=True),
                  mpf.make_addplot(ema_long, panel=1, color='red', secondary_y=True),
                  mpf.make_addplot(histogram, panel=1, color='green', secondary_y=False)])

# Displaying the plot
mpf.show()
