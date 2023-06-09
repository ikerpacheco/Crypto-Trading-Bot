import sys

class Bot:
    def __init__(self):
        self.botState = BotState()
        self.strategy = TrendFollowingStrategy()

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
        if tmp[0] == "update":
            if tmp[1] == "game":
                self.botState.update_game(tmp[2], tmp[3])
        if tmp[0] == "action":
            self.trading_strategy()

    def trading_strategy(self):
        dollars = self.botState.stacks["USDT"]
        current_closing_price = self.botState.charts["USDT_BTC"].closes[-1]
        affordable = dollars / current_closing_price

        if dollars < 100:
            print("no_moves", flush=True)
        else:
            action = self.strategy.decide_action(self.botState)
            if action == "buy":
                amount = 0.5 * affordable
                self.execute_trade("buy", "USDT_BTC", amount)
            elif action == "sell":
                amount = 0.5 * affordable
                self.execute_trade("sell", "USDT_BTC", amount)

    def execute_trade(self, action: str, pair: str, amount: float):
        print(f'{action} {pair} {amount}', flush=True)


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


class TrendFollowingStrategy:
    def __init__(self):
        self.previous_action = None

    def decide_action(self, botState: BotState) -> str:
        closes = botState.charts["USDT_BTC"].closes

        # Calculate the short-term moving average (e.g., 10 periods)
        # print("DEBUG: Closes",closes, flush=True)
        short_term_ma = sum(closes[-10:]) / 10
        # print("DEBUG: Short term ma", short_term_ma, flush=True)

        # Calculate the long-term moving average (e.g., 50 periods)
        long_term_ma = sum(closes[-50:]) / 50
        # print("DEBUG: Long term ma", long_term_ma, flush=True)

        if short_term_ma > long_term_ma:
            if self.previous_action != "buy":
                self.previous_action = "buy"
                return "buy"
        else:
            if self.previous_action != "sell":
                self.previous_action = "sell"
                return "sell"

        return "no_moves"


if __name__ == "__main__":
    mybot = Bot()
    mybot.run()
