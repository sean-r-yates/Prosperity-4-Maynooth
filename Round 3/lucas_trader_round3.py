from datamodel import OrderDepth, TradingState, Order
from typing import Dict, List
import numpy as np

class Trader:

    def __init__(self):
        self.active_vouchers = ["VEV_5100", "VEV_5200", "VEV_5300"]

        self.position_limits = {
            "HYDROGEL_PACK": 200,
            "VELVETFRUIT_EXTRACT": 200,
            self.active_vouchers: 300
        }

        self.price_history = {
            "HYDROGEL_PACK": [],
            "VELVETFRUIT_EXTRACT": [],
        }

        self.orders = {}
        self.conversions = 0
        self.traderData = ""

    # ---------- helper functions
    def get_position(self, state, product):
        return state.position.get(product, 0)

    def get_best_prices(self, order_depth):
        best_bid = max(order_depth.buy_orders.keys()) if order_depth.buy_orders else None
        best_ask = min(order_depth.sell_orders.keys()) if order_depth.sell_orders else None
        return best_bid, best_ask

    def update_price_history(self, product, price):
        self.price_history[product].append(price)
        self.price_history[product] = self.price_history[product][-50:]

    def get_mid_price(self, order_depth):
        best_bid, best_ask = self.get_best_prices(order_depth)
        if best_bid is not None and best_ask is not None:
            return (best_bid + best_ask) / 2.0
        if best_bid is not None:
            return float(best_bid)
        if best_ask is not None:
            return float(best_ask)
        return None    

    #def ema(self, prices, alpha=0.1): #EMA as a dynamic fair value estimate
       # ema = prices[0]

    #--------- hydrogel

    def trade_hydrogel(self, state):
        product = "HYDROGEL_PACK"
        order_depth = state.order_depths[product]

        best_bid, best_ask = self.get_best_prices(order_depth)
        if best_bid is None or best_ask is None: #safety check
            return

        mid_price = (best_bid + best_ask)/2
        self.update_price_history(product, mid_price)

        window = 200
        if len(self.history[product]) < window:
            return
    
        prices = self.history[product][-window:]
        mean = np.mean(prices)
        std = np.std(prices)

        if std == 0:
            return
        
        z = (mid_price - mean) / std

        pos = self.get_position(state, product)
        limit = self.position_limits[product]

        threshold = 1.2

        size = int(10 *min(abs(z), 2))

        if z < -threshold and pos < limit:
            self.orders[product].append(Order(product, best_ask, size)) #buying
        elif z > threshold and pos > -limit: 
            self.orders[product].append(Order(product, best_bid, -size)) #selling

    #-------------- velvetfruit EXTRACTS

    def trade_velvetfruit(self, state):
        product = "VELVETFRUIT_EXTRACT"
        order_depth = state.order_depths[product]

        best_bid, best_ask = self.get_best_prices(order_depth)
        if best_bid is None or best_ask is None: #safety check
            return

        mid_price = (best_bid + best_ask)/2
        self.update_price_history(product, mid_price)

        window = 150
        if len(self.history[product]) < window:
            return
        
        prices = self.history[product][-window:]
        mean = np.mean(prices)
        std = np.std(prices)

        if std == 0:
            return
        
        z = (mid_price - mean) / std

        pos = self.get_position(state, product)
        limit = self.position_limits[product]

        threshold = 1.5

        if z < -threshold:
        # Strong BUY bias on dips
            size = int(15 * min(abs(z), 2))  # bigger size
            if pos < limit:
                self.orders[product].append(Order(product, best_ask, size)) 

        elif z > threshold:
            # More cautious on selling
            size = int(8 * min(abs(z), 2))
            if pos > -limit:
                self.orders[product].append(Order(product, best_bid, -size)) 

    #--------- VOUCHERS
    def trade_vouchers(self, state):
        orders = {product: [] for product in self.voucher_strikes}

        # --- Get underlying price ---
        u_depth = state.order_depths["VELVETFRUIT_EXTRACT"]
        if not u_depth.buy_orders or not u_depth.sell_orders:
            return orders

        ubid = max(u_depth.buy_orders)
        uask = min(u_depth.sell_orders)
        S = (ubid + uask) / 2

        # --- Estimate volatility ---
        prices = self.history["VELVETFRUIT_EXTRACT"]
        if len(prices) < 50:
            return orders

        recent = prices[-50:]
        vol = np.std(np.diff(recent))  # better than raw std

        # --- Compute fair values ---
        fair_values = {}
        market_prices = {}

        for product, K in self.voucher_strikes.items():
            depth = state.order_depths[product]
            if not depth.buy_orders or not depth.sell_orders:
                continue

            best_bid = max(depth.buy_orders)
            best_ask = min(depth.sell_orders)
            mid = (best_bid + best_ask) / 2

            # Simplified pricing
            time_value = 1.0 * vol
            fair = max(0, S - K) + time_value

            fair_values[product] = fair
            market_prices[product] = (mid, best_bid, best_ask)

        # --- 1. Absolute mispricing trades ---
        for product in fair_values:
            fair = fair_values[product]
            mid, bid, ask = market_prices[product]

            edge = mid - fair

            pos = state.position.get(product, 0)
            limit = 300

            size = 5

            if edge < -2 and pos < limit:
                orders[product].append(Order(product, ask, size))

            elif edge > 2 and pos > -limit:
                orders[product].append(Order(product, bid, -size))

        # --- 2. Relative value trades (IMPORTANT) ---
        sorted_products = sorted(self.voucher_strikes.items(), key=lambda x: x[1])

        for i in range(len(sorted_products) - 1):
            p1, k1 = sorted_products[i]
            p2, k2 = sorted_products[i + 1]

            if p1 not in fair_values or p2 not in fair_values:
                continue

            spread_market = market_prices[p1][0] - market_prices[p2][0]
            spread_fair = fair_values[p1] - fair_values[p2]

            diff = spread_market - spread_fair

            size = 3

            if diff > 2:
                # p1 too expensive relative to p2
                orders[p1].append(Order(p1, market_prices[p1][1], -size))
                orders[p2].append(Order(p2, market_prices[p2][2], size))

            elif diff < -2:
                # p1 too cheap relative to p2
                orders[p1].append(Order(p1, market_prices[p1][2], size))
                orders[p2].append(Order(p2, market_prices[p2][1], -size))

        return orders

   

    def run(self, state: TradingState):

        self.orders = {product: [] for product in state.order_depths.keys()}

        for product in state.order_depths:
            if product == "HYDROGEL_PACK":
                self.trade_hydrogel(state)
            elif product == "VELVETFRUIT_EXTRACT":
                self.trade_velvetfruit(state)

        return self.orders, self.conversions, self.traderData