from datamodel import OrderDepth, TradingState, Order
from typing import Dict, List
import numpy as np


class Trader:

    def __init__(self):

        # -------- PRODUCTS --------
        self.vouchers = ["VEV_5100", "VEV_5200", "VEV_5300"]

        self.position_limits = {
            "HYDROGEL_PACK": 200,
            "VELVETFRUIT_EXTRACT": 200,
        }

        for v in self.vouchers:
            self.position_limits[v] = 300

        # -------- STATE --------
        self.price_history = {
            "HYDROGEL_PACK": [],
            "VELVETFRUIT_EXTRACT": [],
        }

        self.mark_trades = {v: [] for v in self.vouchers}

        self.orders = {}
        self.conversions = 0
        self.traderData = ""

    # ========================
    # HELPERS
    # ========================
    def get_best_prices(self, depth):
        bid = max(depth.buy_orders) if depth.buy_orders else None
        ask = min(depth.sell_orders) if depth.sell_orders else None
        return bid, ask

    def mid_price(self, depth):
        bid, ask = self.get_best_prices(depth)
        if bid is not None and ask is not None:
            return (bid + ask) / 2
        return None

    def get_position(self, state, product):
        return state.position.get(product, 0)

    def update_history(self, product, price):
        self.price_history[product].append(price)
        self.price_history[product] = self.price_history[product][-100:]

    # ========================
    # MARK TRACKING
    # ========================
    def update_mark(self, state: TradingState):

        for product, trades in state.market_trades.items():

            if product not in self.mark_trades:
                continue

            for t in trades:
                if t.buyer == 'Mark 14':
                    self.mark_trades[product].append(("BUY", t.quantity))
                elif t.seller == 'Mark 14':
                    self.mark_trades[product].append(("SELL", t.quantity))

            self.mark_trades[product] = self.mark_trades[product][-15:]

    def mark_signal(self, product):

        trades = self.mark_trades.get(product, [])
        if not trades:
            return 0

        score = 0
        for side, size in trades:
            w = min(size / 10, 2)
            score += w if side == "BUY" else -w

        return score / len(trades)

    # ========================
    # SPOT TRADING
    # ========================
    def trade_spot(self, state, product, window=50, threshold=1.5):

        depth = state.order_depths[product]
        bid, ask = self.get_best_prices(depth)
        if bid is None or ask is None:
            return

        mid = (bid + ask) / 2
        self.update_history(product, mid)

        if len(self.price_history[product]) < window:
            return

        prices = self.price_history[product][-window:]
        mean = np.mean(prices)
        std = np.std(prices)
        if std == 0:
            return

        z = (mid - mean) / std

        pos = self.get_position(state, product)
        limit = self.position_limits[product]

        size = int(8 * min(abs(z), 2))

        if z < -threshold and pos < limit:
            self.orders[product].append(Order(product, ask, size))

        elif z > threshold and pos > -limit:
            self.orders[product].append(Order(product, bid, -size))

    # ========================
    # VOUCHER TRADING (FIXED)
    # ========================
    def trade_vouchers(self, state: TradingState):

        market = {}

        # --- collect clean data ---
        for v in self.vouchers:
            depth = state.order_depths.get(v)
            if depth is None:
                continue

            bid, ask = self.get_best_prices(depth)
            if bid is None or ask is None:
                continue

            spread = ask - bid
            if spread > 5:   # strict filter
                continue

            market[v] = {
                "mid": (bid + ask) / 2,
                "bid": bid,
                "ask": ask,
                "spread": spread
            }

        if len(market) < 3:
            return

        # --- FAIR VALUE (ONLY INTERPOLATION) ---
        fair = {}
        fair["VEV_5200"] = (market["VEV_5100"]["mid"] + market["VEV_5300"]["mid"]) / 2

        # edges (do NOT invent values)
        fair["VEV_5100"] = market["VEV_5100"]["mid"]
        fair["VEV_5300"] = market["VEV_5300"]["mid"]

        # --- compute signals ---
        signals = []

        for v in self.vouchers:

            if v not in market:
                continue

            mid = market[v]["mid"]
            spread = market[v]["spread"]

            mispricing = mid - fair[v]

            # strict threshold
            threshold = spread * 1.2 + 1

            if abs(mispricing) > threshold:
                signals.append((abs(mispricing), v, mispricing))

        # --- only best 2 trades ---
        signals.sort(reverse=True)
        signals = signals[:2]

        for _, v, mispricing in signals:

            m = market[v]
            bid, ask = m["bid"], m["ask"]
            spread = m["spread"]

            pos = self.get_position(state, v)
            limit = self.position_limits[v]

            # inventory penalty
            penalty = abs(pos) / limit * 1.5

            # mark confirmation
            signal = self.mark_signal(v)

            # =========================
            # BUY (underpriced)
            # =========================
            if mispricing < 0:

                if signal < -0.3:
                    continue  # Mark disagrees

                edge = fair[v] - ask - penalty

                if edge > spread:
                    size = min(5, limit - pos)
                    if size > 0:
                        self.orders[v].append(Order(v, ask, size))

            # =========================
            # SELL (overpriced)
            # =========================
            elif mispricing > 0:

                if signal > 0.3:
                    continue  # Mark disagrees

                edge = bid - fair[v] - penalty

                if edge > spread:
                    size = min(5, limit + pos)
                    if size > 0:
                        self.orders[v].append(Order(v, bid, -size))

        # =========================
        # EXIT LOGIC (VERY IMPORTANT)
        # =========================
        for v in self.vouchers:

            if v not in market:
                continue

            pos = self.get_position(state, v)
            if pos == 0:
                continue

            mid = market[v]["mid"]
            f = fair[v]

            # close when mispricing disappears
            if pos > 0 and mid >= f:
                self.orders[v].append(Order(v, market[v]["bid"], -min(5, pos)))

            elif pos < 0 and mid <= f:
                self.orders[v].append(Order(v, market[v]["ask"], min(5, -pos)))

    # ========================
    # MAIN
    # ========================
    def run(self, state: TradingState):

        self.orders = {p: [] for p in state.order_depths}

        # update mark tracker
        self.update_mark(state)

        # spot
        self.trade_spot(state, "HYDROGEL_PACK", 60, 1.2)
        self.trade_spot(state, "VELVETFRUIT_EXTRACT", 50, 1.5)

        # vouchers
        self.trade_vouchers(state)

        return self.orders, self.conversions, self.traderData