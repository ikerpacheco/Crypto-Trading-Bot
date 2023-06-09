import sys
import time
from typing import List, Tuple

class Bot:
    def __init__(self):
        self.botState = BotState()
        self.strategy = TradingStrategy()

    def run(self):
        while True:
            reading = input()
            if len(reading) == 0:
                continue
            print(reading, file=sys.stderr)
            self.parse(reading)

    def parse(self, info: str):
        tmp = info.split(" ")
        if tmp[0] == "settings":
            self.botState.update_settings(tmp[1], tmp[2])
        elif tmp[0] == "update":
            if tmp[1] == "game":
                self.botState.update_game(tmp[2], tmp[3])
        elif tmp[0] == "action":
            self.trading_strategy()

    def trading_strategy(self):
        dollars = self.botState.stacks["USDT"]
        current_closing_price = self.botState.charts["USDT_BTC"].closes[-1]
        affordable = dollars / current_closing_price

        if dollars < 100:
            print("no_moves", flush=True)
        elif dollars > 1300:
            print("no_moves", flush=True)
        else:
            action = self.strategy.decide_action(self.botState)
            if action == "buy":
                amount = 0.5 * affordable
                self.execute_trade("buy", "USDT_BTC", amount)
            elif action == "sell":
                amount = 0.5 * affordable
                self.execute_trade("sell", "USDT_BTC", amount)
            else:
                print("no_moves", flush=True)

    def execute_trade(self, action: str, pair: str, amount: float):
        print(f'{action} {pair} {amount:.8f}', flush=True)


class Candle:
    def __init__(self, format, intel):
        tmp = intel.split(",")
        for (i, key) in enumerate(format):
            value = tmp[i]
            if key == "pair":
                self.pair = value
            if key == "date":
                self.date = int(value)
            if key == "high":
                self.high = float(value)
            if key == "low":
                self.low = float(value)
            if key == "open":
                self.open = float(value)
            if key == "close":
                self.close = float(value)
            if key == "volume":
                self.volume = float(value)

    def __repr__(self):
        return str(self.pair) + str(self.date) + str(self.close) + str(self.volume)


class Chart:
    def __init__(self):
        self.dates = []
        self.opens = []
        self.highs = []
        self.lows = []
        self.closes = []
        self.volumes = []
        self.indicators = {}

    def add_candle(self, candle: Candle):
        self.dates.append(candle.date)
        self.opens.append(candle.open)
        self.highs.append(candle.high)
        self.lows.append(candle.low)
        self.closes.append(candle.close)
        self.volumes.append(candle.volume)

    def calculate_ema(self, period: int) -> List[float]:
        closes = self.closes
        ema_values = []

        if len(closes) >= period:
            sma = sum(closes[:period]) / period
            multiplier = 2 / (period + 1)
            ema_values.append(sma)

            for close in closes[period:]:
                ema = (close - ema_values[-1]) * multiplier + ema_values[-1]
                ema_values.append(ema)
        
        return ema_values


class BotState:
    def __init__(self):
        self.timeBank = 0
        self.maxTimeBank = 0
        self.timePerMove = 1
        self.candleInterval = 1
        self.candleFormat = []
        self.candlesTotal = 0
        self.candlesGiven = 0
        self.initialStack = 0
        self.transactionFee = 0.1
        self.date = 0
        self.stacks = dict()
        self.charts = dict()

    def update_chart(self, pair: str, new_candle_str: str):
        if not (pair in self.charts):
            self.charts[pair] = Chart()
        new_candle_obj = Candle(self.candleFormat, new_candle_str)
        self.charts[pair].add_candle(new_candle_obj)

    def update_stack(self, key: str, value: float):
        self.stacks[key] = value

    def update_settings(self, key: str, value: str):
        if key == "timebank":
            self.maxTimeBank = int(value)
            self.timeBank = int(value)
        if key == "time_per_move":
            self.timePerMove = int(value)
        if key == "candle_interval":
            self.candleInterval = int(value)
        if key == "candle_format":
            self.candleFormat = value.split(",")
        if key == "candles_total":
            self.candlesTotal = int(value)
        if key == "candles_given":
            self.candlesGiven = int(value)
        if key == "initial_stack":
            self.initialStack = int(value)
        if key == "transaction_fee_percent":
            self.transactionFee = float(value)

    def update_game(self, key: str, value: str):
        if key == "next_candles":
            new_candles = value.split(";")
            self.date = int(new_candles[0].split(",")[1])
            for candle_str in new_candles:
                candle_infos = candle_str.strip().split(",")
                self.update_chart(candle_infos[0], candle_str)
        if key == "stacks":
            new_stacks = value.split(",")
            for stack_str in new_stacks:
                stack_infos = stack_str.strip().split(":")
                self.update_stack(stack_infos[0], float(stack_infos[1]))


from typing import List, Tuple

class TradingStrategy:
    def __init__(self):
        self.previous_action = None
        self.long_period = 30
        self.std_multiplier = 2
        self.macd_fast_period = 12
        self.macd_slow_period = 26
        self.macd_signal_period = 9

    def calculate_bollinger_bands(self, prices: List[float], period: int) -> Tuple[List[float], List[float]]:
        sma = sum(prices[:period]) / period
        std = (sum((x - sma) ** 2 for x in prices[:period]) / period) ** 0.5
        upper_band = sma + self.std_multiplier * std
        lower_band = sma - self.std_multiplier * std
        return upper_band, lower_band

    def calculate_macd(self, prices: List[float]) -> Tuple[List[float], List[float]]:
        macd_fast = self.calculate_ema(prices, self.macd_fast_period)
        macd_slow = self.calculate_ema(prices, self.macd_slow_period)
    
    # Ensure macd_fast and macd_slow have the same length
        min_length = min(len(macd_fast), len(macd_slow))
        macd_fast = macd_fast[-min_length:]
        macd_slow = macd_slow[-min_length:]
    
        macd_line = [f - s for f, s in zip(macd_fast, macd_slow)]
        macd_signal = self.calculate_ema(macd_line, self.macd_signal_period)
    
    # Ensure macd_line and macd_signal have the same length
        min_length = min(len(macd_line), len(macd_signal))
        macd_line = macd_line[-min_length:]
        macd_signal = macd_signal[-min_length:]
    
        return macd_line, macd_signal


    def calculate_ema(self, values: List[float], period: int) -> List[float]:
        ema_values = []

        if len(values) >= period:
            sma = sum(values[:period]) / period
            multiplier = 2 / (period + 1)
            ema_values.append(sma)

            for value in values[period:]:
                ema = (value - ema_values[-1]) * multiplier + ema_values[-1]
                ema_values.append(ema)
        
        return ema_values

    def decide_action(self, botState: BotState) -> str:
        chart = botState.charts["USDT_BTC"]
        closes = chart.closes

        if len(closes) > self.long_period:
            upper_band, lower_band = self.calculate_bollinger_bands(closes, self.long_period)

            current_closing_price = closes[-1]
            affordable = botState.stacks["USDT"] / current_closing_price

            macd_line, macd_signal = self.calculate_macd(closes)
            macd_histogram = [macd_line[i] - macd_signal[i] for i in range(len(macd_line))]

            if macd_histogram[-1] > 0 and macd_histogram[-2] < 0:
                if current_closing_price < lower_band:
                    if self.previous_action != "buy":
                        self.previous_action = "buy"
                        return "buy"
                else:
                    return "no_moves"
            elif macd_histogram[-1] < 0 and macd_histogram[-2] > 0:
                if current_closing_price > upper_band:
                    if self.previous_action != "sell":
                        self.previous_action = "sell"
                        return "sell"
                else:
                    return "no_moves"

        return "no_moves"

if __name__ == "__main__":
    mybot = Bot()
    mybot.run()
