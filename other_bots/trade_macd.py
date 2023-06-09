import sys
from typing import List, Tuple
import pandas as pd

class Bot:
    def __init__(self):
        self.botState = BotState()
        self.boughtPrice = 0
        self.totaBought = 0
        self.bought = False
        self.prevTendency = "flat"

    def run(self):
        while True:
            reading = input()
            if len(reading) == 0:
                continue
            self.parse(reading)

    def parse(self, info: str):
        tmp = info.split(" ")
        if tmp[0] == "settings":
            self.botState.update_settings(tmp[1], tmp[2])
        if tmp[0] == "update":
            if tmp[1] == "game":
                self.botState.update_game(tmp[2], tmp[3])
        if tmp[0] == "action":
            # This won't work every time, but it works sometimes!
            self.trading_strategy()
            # print("short emas: ", short_emas, "long emas", long_emas, file=sys.stderr)
    def tendency(self, short_ema, long_ema):
        if short_ema > long_ema:
            return "up"
        elif short_ema < long_ema:
            return "down"
        else:
            return "flat"

    def trading_strategy(self):
        short_emas, long_emas, macd_line, signal_line, histogram = self.calculate_macd(self.botState.charts["USDT_BTC"].closes, 12, 26, 20)
        # print("signal_line", signal_line, file=sys.stderr)
        ema_200 = self.calculate_ema(self.botState.charts["USDT_BTC"].closes, 200)
        # print(f'My stacks are {dollars}. The current closing price is {current_closing_price}. So I can afford {affordable}', file=sys.stderr)
        # if self.botState.stacks["USDT"] < 100:
        #     print("no_moves", flush=True)
        # else:
        boughtPriceDiff = 0
        if self.totaBought > 0:
            boughtPriceDiff = (self.botState.charts["USDT_BTC"].closes[-1] * 100 / self.boughtPrice) - 100
        # print(f"(({short_emas[-1]} < {macd_line[-1]}) & ({long_emas[-1]} < {macd_line[-1]}))", file=sys.stderr)
        print(f"({macd_line[-1]} < {signal_line[-1]}) = {(macd_line[-1] > signal_line[-1])}", file=sys.stderr)
        tendency = self.tendency(short_emas[-1], long_emas[-1])
        
        
        
        if (tendency == "up") & (self.prevTendency != "up"):
            dollars = self.botState.stacks["USDT"]
            current_closing_price = self.botState.charts["USDT_BTC"].closes[-1]
            cuantity = dollars / current_closing_price
            print(f'buy USDT_BTC {cuantity}', flush=True)
            self.totaBought += cuantity
            self.boughtPrice = current_closing_price
            self.bought = True
            
        elif (tendency == "down") & (self.prevTendency == "down") & (self.bought == True):
            print(f'sell USDT_BTC {self.totaBought}', flush=True)
            print("sell 1", file=sys.stderr)
            self.totaBought = 0
            self.bought = False
            
        # elif ((boughtPriceDiff <= -0.5) & (ema_200[-1] < ema_200[-2])): # Stop loss, maybe not need to chck ema_200
        #     print(f'sell USDT_BTC {self.totaBought}', flush=True)
        #     print("sell 2", file=sys.stderr)
        #     self.totaBought = 0
        #     self.bought = False
        else:
            print("no_moves", flush=True)
        self.prevTendency = tendency
            
    
    def calculate_macd(self, closePrice, short_period, long_period, signal_period):
        ema_short = self.calculate_ema(closePrice, short_period)
        ema_long = self.calculate_ema(closePrice, long_period)
        
        macd_line = [s - l for s, l in zip(ema_short, ema_long)]
        signal_line = self.calculate_ema(macd_line, signal_period)
        histogram = [m - s for m, s in zip(macd_line, signal_line)]
        
        return ema_short, ema_long, macd_line, signal_line, histogram

    def calculate_ema(self, data, period):
        ema = []
        multiplier = 2 / (period + 1)
        ema.append(data[0])  # First EMA value is the same as the first data point

        for i in range(1, len(data)):
            ema_value = (data[i] - ema[i-1]) * multiplier + ema[i-1]
            ema.append(ema_value)

        return ema


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


if __name__ == "__main__":
    mybot = Bot()
    mybot.run()
