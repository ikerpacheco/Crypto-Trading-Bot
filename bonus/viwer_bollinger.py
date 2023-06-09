import pandas as pd
import mplfinance as mpf
from typing import List, Tuple


# Read data from CSV file
data = pd.read_csv('trade_training-datasets/training-set_USDT_BTC-3.csv')

# Convert the 'date' column to pandas DateTime format
data['date'] = pd.to_datetime(data['date'])

# Check for variations in the 'volume' column name
volume_column = next((col for col in data.columns if col.lower().strip() == 'volume'), None)
if volume_column is None:
    raise ValueError("Volume column not found in the input DataFrame.")

# Calculate MACD
def calculate_bollinger_bands(std_multiplier, prices, period):
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper_band = sma + std_multiplier * std
    lower_band = sma - std_multiplier * std
    return upper_band.tolist(), lower_band.tolist()
    
up, low = calculate_bollinger_bands(2, data['close'], 30)

# Prepare the data for candlestick visualization
data_for_candlestick = data[['date', 'open', 'high', 'low', 'close', volume_column]]
data_for_candlestick.set_index('date', inplace=True)
data_for_candlestick.index.name = 'Date'

# Plotting the trading graph with candlestick style and MACD indicator
mpf.plot(data_for_candlestick, type='candle', style='yahoo', title='Trading Graph with MACD Indicator',
         ylabel='Price', ylabel_lower='MACD', figsize=(10, 6), mav=(12, 26), volume=True,
         addplot=[mpf.make_addplot(up, panel=1, color='orange', secondary_y=True),
                  mpf.make_addplot(low, panel=1, color='purple', secondary_y=True)]
         )

# Displaying the plot
mpf.show()