from datamodel import OrderDepth, TradingState, Order
from typing import Dict, List
import numpy as np


class Trader:

    def bid(self):
        return 20 # dunno how much to bid yet

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

    def update_price_history(self, product, price):
        self.price_history[product].append(price)
        self.price_history[product] = self.price_history[product][-50:]

    def osmium_market_making(self, state, order_depth, fair_price, spread, position):
        # plan:
        # place buy + sell orders
        # handle spread - instead of fixed spread, implement volatility-based spread
        # handle sizing

        limit = self.position_limits['ASH_COATED_OSMIUM']

        best_bid, best_ask = self.get_best_prices(order_depth)

        buy_price = min(best_bid + 1, int(fair_price - spread)) #undercutting or volitility
        sell_price = max(best_ask - 1, int(fair_price + spread))

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

        best_bid, best_ask = self.get_best_prices(order_depth)
        if best_bid is None or best_ask is None: #safety check
            return

        mid_price = (best_bid + best_ask)/2
        self.update_price_history('ASH_COATED_OSMIUM', mid_price)

        prices = self.price_history['ASH_COATED_OSMIUM']

        if len(prices) < 20:
            return
        
        # volatility-based spread
        returns = np.diff(np.log(prices)) #returns measure how significant was the change
        volatility = np.std(returns) #

        fair_price = np.mean(prices[-20:]) # avg of last 20 prices  | for osmium, mid price alone should be enough 
        spread = max(1, int(volatility * 6000))

        position = self.get_position(state, 'ASH_COATED_OSMIUM')
        limit = self.position_limits['ASH_COATED_OSMIUM']

        #buy if cheap
        for ask, volume in list(order_depth.sell_orders.items())[:3]:
            if ask < fair_price - spread:
                buy_size = min(-volume, limit - position)
                if buy_size > 0:
                    self.orders['ASH_COATED_OSMIUM'].append(Order('ASH_COATED_OSMIUM', ask, buy_size))
                    position += buy_size

        # sell if expensive
        for bid, volume in list(order_depth.buy_orders.items())[:3]:
            if bid > fair_price + spread:
                sell_size = min(volume, position + limit)
                if sell_size > 0:
                    self.orders['ASH_COATED_OSMIUM'].append(Order('ASH_COATED_OSMIUM', bid, -sell_size))
                    position -= sell_size

        self.osmium_market_making(state, order_depth, fair_price, spread, position)

    def get_signal(self, product):
        prices = self.price_history[product]

        if len(prices) < 20:
            return 0

        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]

        if slope > 0:
            return 1
        elif slope < 0:
            return -1
        
    def trade_pepper(self, state):

        order_depth = state.order_depths['INTARIAN_PEPPER_ROOT']

        position = self.get_position(state, 'INTARIAN_PEPPER_ROOT')
        limit = self.position_limits['INTARIAN_PEPPER_ROOT'] #limit = 80

        best_bid, best_ask = self.get_best_prices(order_depth)
        if best_bid is None or best_ask is None:
            return

        mid_price = (best_bid + best_ask) / 2
        self.update_price_history('INTARIAN_PEPPER_ROOT', mid_price)

        signal = self.get_signal('INTARIAN_PEPPER_ROOT')
        if signal == 1:
            max_trade = 10
            buy_size = min(max_trade, limit - position)
            if buy_size > 0:
                self.orders['INTARIAN_PEPPER_ROOT'].append(Order('INTARIAN_PEPPER_ROOT', best_ask, buy_size))

        elif signal == -1: #since it goes up no matter what, maybe only reduce position and not fully sell
            max_trade = 10
            sell_size = min(max_trade, position)
            if sell_size > 0:
                self.orders['INTARIAN_PEPPER_ROOT'].append(Order('INTARIAN_PEPPER_ROOT', best_bid, -sell_size))

    def run(self, state: TradingState):

        self.orders = {product: [] for product in state.order_depths.keys()}

        for product in state.order_depths:
            if product == 'ASH_COATED_OSMIUM':
                self.trade_osmium(state)
            elif product == 'INTARIAN_PEPPER_ROOT':
                self.trade_pepper(state)

        return self.orders, self.conversions, self.traderData