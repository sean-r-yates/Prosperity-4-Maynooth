from datamodel import OrderDepth, TradingState, Order
from typing import Dict, List
import numpy as np


class Trader:

    def __init__(self):

        # ---------------- PRODUCTS ----------------
        self.vouchers = ["VEV_5100", "VEV_5200", "VEV_5300"]

        self.position_limits = {
            "HYDROGEL_PACK": 200,
            "VELVETFRUIT_EXTRACT": 200,
        }

        for v in self.vouchers:
            self.position_limits[v] = 300

        # ---------------- STATE ----------------
        self.price_history = {
            "HYDROGEL_PACK": [],
            "VELVETFRUIT_EXTRACT": [],
        }

        self.orders = {}
        self.conversions = 0
        self.traderData = ""

        # ---------------- MARK TRACKER ----------------
        self.mark_trades = {p: [] for p in self.vouchers}
        self.last_mark_trade_time = {}

    # ========================
    # HELPERS
    # ========================
    def get_best_prices(self, depth):
        bid = max(depth.buy_orders) if depth.buy_orders else None
        ask = min(depth.sell_orders) if depth.sell_orders else None
        return bid, ask

    def mid_price(self, depth):
        bid, ask = self.get_best_prices(depth)
        if bid and ask:
            return (bid + ask) / 2
        return None

    def update_history(self, product, price):
        self.price_history[product].append(price)
        self.price_history[product] = self.price_history[product][-100:]

    def get_position(self, state, product):
        return state.position.get(product, 0)

    # ========================
    # MARK TRACKING
    # ========================
    def update_mark(self, state: TradingState):

        for product, trades in state.market_trades.items():

            if product not in self.mark_trades:
                continue

            for t in trades:
                if t.buyer == "Mark 14":
                    self.mark_trades[product].append(("BUY", t.quantity))
                elif t.seller == "Mark 14":
                    self.mark_trades[product].append(("SELL", t.quantity))

            self.mark_trades[product] = self.mark_trades[product][-20:]

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

        size = int(10 * min(abs(z), 2))

        if z < -threshold and pos < limit:
            self.orders[product].append(Order(product, ask, size))

        elif z > threshold and pos > -limit:
            self.orders[product].append(Order(product, bid, -size))

    # ========================
    # VOUCHER TRADING
    # ========================
    def trade_vouchers(self, state: TradingState):

        # --- underlying ---
        u_depth = state.order_depths["VELVETFRUIT_EXTRACT"]
        ubid, uask = self.get_best_prices(u_depth)
        if ubid is None or uask is None:
            return

        S = (ubid + uask) / 2

        # --- collect market ---
        market = {}
        for v in self.vouchers:
            depth = state.order_depths[v]
            bid, ask = self.get_best_prices(depth)
            if bid is None or ask is None:
                continue

            spread = ask - bid
            if spread > 6:  # spread filter
                continue

            market[v] = {
                "mid": (bid + ask) / 2,
                "bid": bid,
                "ask": ask,
                "spread": spread
            }

        if len(market) < 3:
            return

        # --- FAIR VALUE (cross-strike) ---
        fair = {}
        fair["VEV_5200"] = (market["VEV_5100"]["mid"] + market["VEV_5300"]["mid"]) / 2
        fair["VEV_5100"] = market["VEV_5200"]["mid"] - 50
        fair["VEV_5300"] = market["VEV_5200"]["mid"] + 50

        # =========================
        # TRADE LOOP
        # =========================
        for v in self.vouchers:

            if v not in market:
                continue

            m = market[v]
            f = fair[v]

            bid, ask = m["bid"], m["ask"]
            spread = m["spread"]

            pos = self.get_position(state, v)
            limit = self.position_limits[v]

            # inventory penalty
            penalty = abs(pos) / limit * 2

            edge_buy = f - ask - penalty
            edge_sell = bid - f - penalty

            threshold = spread * 0.6 + 1

            # -----------------
            # MARK SIGNAL
            # -----------------
            signal = self.mark_signal(v)

            # boost edge if Mark agrees
            if signal > 0.5:
                edge_buy += 1
            elif signal < -0.5:
                edge_sell += 1

            size = 5

            if edge_buy > threshold and pos < limit:
                self.orders[v].append(Order(v, ask, size))

            elif edge_sell > threshold and pos > -limit:
                self.orders[v].append(Order(v, bid, -size))

    # ========================
    # MAIN
    # ========================
    def run(self, state: TradingState):

        self.orders = {p: [] for p in state.order_depths}

        # --- update mark tracking ---
        self.update_mark(state)

        # --- spot ---
        self.trade_spot(state, "HYDROGEL_PACK", 60, 1.2)
        self.trade_spot(state, "VELVETFRUIT_EXTRACT", 50, 1.5)

        # --- vouchers ---
        self.trade_vouchers(state)

        return self.orders, self.conversions, self.traderData