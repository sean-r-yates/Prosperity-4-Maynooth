from datamodel import OrderDepth, TradingState, Order
from typing import Dict, List
import numpy as np


class Trader:

    def bid(self):
        return 15 # dunno how much to bid yet

    def __init__(self):
        self.position_limits = {
            "ASH_COATED_OSMIUM": 80,
            "INTARIAN_PEPPER_ROOT": 80,
        }

        self.price_history = {
            "ASH_COATED_OSMIUM": [],
            "INTARIAN_PEPPER_ROOT": [],
        }

        self.orders = {}
        self.conversions = 0
        self.traderData = ""
  
    def get_position(self, state, product):
        return state.position.get(product, 0)

    def get_best_prices(self, order_depth):
        best_bid = max(order_depth.buy_orders.keys()) if order_depth.buy_orders else None
        best_ask = min(order_depth.sell_orders.keys()) if order_depth.sell_orders else None
        return best_bid, best_ask

    def compute_fair_price(self, product, order_depth):
        best_bid, best_ask = self.get_best_prices(order_depth)

        if best_bid is None or best_ask is None:
            return None

        mid = (best_bid + best_ask) / 2

        # orderbook imbalance
        bid_vol = sum(order_depth.buy_orders.values())
        ask_vol = -sum(order_depth.sell_orders.values())

        imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol + 1e-6)

        fair = mid + imbalance * 2 

        return fair

    def update_price_history(self, product, price):
        self.price_history[product].append(price)
        self.price_history[product] = self.price_history[product][-50:]

    def get_signal(self, product):
        prices = self.price_history[product]

        if len(prices) < 10:
            return 0

        #short = np.mean(prices[-5:])
        #long = np.mean(prices[-20:])

        #if short > long:
        #    return 1   # bullish
        #elif short < long:
        #    return -1  # bearish
        #return 0

        #gpt suggestion - signal was too weak/simplistic 

        x = np.arrange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]

        if slope > 0:
            return 1
        elif slope < 0:
            return -1


    def osmium_market_making(self, state, order_depth, fair_price, spread):
        # plan:
        # place buy + sell orders
        # handle spread - instead of fixed spread, implement volatility-based spread
        # handle sizing

        position = self.get_position(state, 'ASH_COATED_OSMIUM')
        limit = self.position_limits['ASH_COATED_OSMIUM']

        best_bid, best_ask = self.get_best_prices(order_depth)

        #undercutting
        buy_price = best_bid + 1
        sell_price = best_ask - 1

        max_size = 10
        buy_size = min(max_size, limit - position)
        sell_size = min(max_size, position + limit)

        if buy_size > 0:
            self.orders['ASH_COATED_OSMIUM'].append(Order('ASH_COATED_OSMIUM', buy_price, buy_size))
        if sell_size > 0:
            self.orders['ASH_COATED_OSMIUM'].append(Order('ASH_COATED_OSMIUM', sell_price, -sell_size))


    def trade_osmium(self, state):
        # plan: 
        # compute fair price
        # compute volatility
        # decide:
        #   - take trades?
        #   - bias (buy/sell/neutral)

        order_depth = state.order_depths['ASH_COATED_OSMIUM']
        #sell_orders = order_depth.sell_orders
        #buy_orders = order_depth.buy_orders

        best_bid, best_ask = self.get_best_prices(order_depth)
        mid_price = (best_bid + best_ask)/2

        self.update_price_history('ASH_COATED_OSMIUM', mid_price)

        prices = self.price_history['ASH_COATED_OSMIUM']

        if len(prices) < 20:
            return
        
        # volatility-based spread
        returns = np.diff(np.log(prices)) #returns measure how significant was the change
        volatility = np.std(returns) #

        fair_price = np.mean(prices[-20:]) # avg of last 20 prices  | for osmium, mid price alone should be enough 

        spread = max(1, int(volatility * 10000))

        self.osmium_market_making(state, order_depth, fair_price, spread)

    def trade_pepper(self, state):

        order_depth = state.order_depths['INTARIAN_PEPPER_ROOT']
        sell_orders = order_depth.sell_orders
        buy_orders = order_depth.buy_orders

    def trade_product(self, state, product):

        order_depth = state.order_depths[product]
        position = self.get_position(state, product)
        limit = self.position_limits[product]

        best_bid, best_ask = self.get_best_prices(order_depth)

        if best_bid is None or best_ask is None:
            return

        mid_price = (best_bid + best_ask) / 2
        self.update_price_history(product, mid_price)

        fair_price = self.compute_fair_price(product, order_depth)
        signal = self.get_signal(product)

        # adjust fair price
        fair_price += signal * 1.5

        # aggressive taking
        for ask, volume in order_depth.sell_orders.items():
            if ask < fair_price:
                buy_size = min(-volume, limit - position)
                if buy_size > 0:
                    self.orders[product].append(Order(product, ask, buy_size))
                    position += buy_size

        for bid, volume in order_depth.buy_orders.items():
            if bid > fair_price:
                sell_size = min(volume, position + limit)
                if sell_size > 0:
                    self.orders[product].append(Order(product, bid, -sell_size))
                    position -= sell_size

        # passive market making
        spread = 2

        bid_price = int(fair_price - spread)
        ask_price = int(fair_price + spread)

        buy_size = limit - position
        sell_size = position + limit

        if buy_size > 0:
            self.orders[product].append(Order(product, bid_price, buy_size))

        if sell_size > 0:
            self.orders[product].append(Order(product, ask_price, -sell_size))

    def run(self, state: TradingState):

        self.orders = {product: [] for product in state.order_depths.keys()}

        for product in state.order_depths:
            if product in self.position_limits:
                self.trade_product(state, product)

        return self.orders, self.conversions, self.traderData