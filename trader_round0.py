from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string

class Trader:

    def __init__(self):
        self.orders = {}
        self.conversions = 0
        self.traderData = "SAMPLE"

        #emeralds
        self.emeralds_buy_orders = 0
        self.emeralds_sell_orders = 0
        self.emeralds_position = 0

        #tomatoes
        self.tomatoes_buy_orders = 0
        self.tomatoes_sell_orders = 0
        self.tomatoes_position = 0

    def send_sell_order(self, product, price, amount, msg=None):
        self.orders[product].append(Order(product, price, amount))

        #if msg is not None:
            #logger.print(msg)


    def send_buy_order(self, product, price, amount, msg=None):
        self.orders[product].append(Order(product, int(price), amount))

        #if msg is not None:
            #logger.print(msg)    

    def get_product_pos(self, state, product):
        if product == 'EMERALDS':
            pos = state.position.get('EMERALDS', 0)
        elif product == 'TOMATOES':
            pos = state.position.get('TOMATOES', 0)
        else:
            raise ValueError(f"Unknown product: {product}")

        return pos

    def search_buys(self, state, product, acceptable_price, depth=1):
        order_depth = state.order_depths[product]
        if len(order_depth.sell_orders) != 0:
            orders = list(order_depth.sell_orders.items())
            for ask, amount in orders[0:max(len(orders), depth)]: 

                pos = self.get_product_pos(state, product) 
                if int(ask) < acceptable_price or (abs(ask - acceptable_price) < 1 and (pos < 0 and abs(pos - amount) < abs(pos))):
                    if product == 'EMERALDS':
                        size = min(50-self.emeralds_position-self.emeralds_buy_orders, -amount)
                        self.emeralds_buy_orders += size 
                        self.send_buy_order(product, ask, size, msg=f"TRADE BUY {str(size)} x @ {ask}")

                    elif product == 'TOMATOES':
                        size = min(50-self.tomatoes_position-self.tomatoes_buy_orders, -amount)
                        self.tomatoes_buy_orders += size 
                        self.send_buy_order(product, ask, size, msg=f"TRADE BUY {str(size)} x @ {ask}")
    
    def search_sells(self, state, product, acceptable_price, depth=1):   
        order_depth = state.order_depths[product]
        if len(order_depth.buy_orders) != 0:
            orders = list(order_depth.buy_orders.items())
            for bid, amount in orders[0:max(len(orders), depth)]: 
                
                pos = self.get_product_pos(state, product)   
                if int(bid) > acceptable_price or (abs(bid-acceptable_price) < 1 and (pos > 0 and abs(pos - amount) < abs(pos))):
                    if product == 'EMERALDS':
                        size = min(self.emeralds_position + 50 - self.emeralds_sell_orders, amount)
                        self.emeralds_sell_orders += size
                        self.send_sell_order(product, bid, -size, msg=f"TRADE SELL {str(-size)} x @ {bid}")

                    elif product == 'TOMATOES':
                        size = min(self.tomatoes_position + 50 - self.tomatoes_sell_orders, amount)
                        self.tomatoes_sell_orders += size
                        self.send_sell_order(product, bid, -size, msg=f"TRADE SELL {str(-size)} x @ {bid}")

    def get_bid(self, state, product, price):        
        order_depth = state.order_depths[product]
        if len(order_depth.buy_orders) != 0:
            orders = list(order_depth.buy_orders.items())
            for bid, _ in orders: 
                if bid < price: # DONT COPY SHIT MARKETS
                    return bid
        
        return None

    def get_ask(self, state, product, price):      
        order_depth = state.order_depths[product]
        if len(order_depth.sell_orders) != 0:
            orders = list(order_depth.sell_orders.items())
            for ask, _ in orders: 
                if ask > price: # DONT COPY A SHITY MARKET
                    return ask
        
        return None

    def get_second_bid(self, state, product):
        order_depth = state.order_depths[product]
        if len(order_depth.buy_orders) != 0:
            orders = list(order_depth.buy_orders.items())
            if len(orders) < 2:
                return None
            else:
                bid, _ = orders[1]
                return bid
            
        return None
    
    def get_second_ask(self, state, product):
        order_depth = state.order_depths[product]
        if len(order_depth.sell_orders) != 0:
            orders = list(order_depth.sell_orders.items())
            if len(orders) < 2:
                return None
            else:
                ask, _ = orders[1]
                return ask
            
        return None        



    def trade_emeralds(self, state):
        
        #buy anything at a good price
        self.search_buys(state, 'EMERALDS', 10000, depth=3)
        self.search_sells(state, 'EMERALDS', 10000, depth=3)

        #check if there's another market maker
        best_ask = self.get_ask(state, 'EMERALDS', 10000)
        best_bid = self.get_bid(state, 'EMERALDS', 10000)

        buy_price = 9990
        ask_price = 10010

        if best_ask is not None and best_bid is not None:
            ask = best_ask
            bid = best_bid
            
            sell_price = ask - 1
            buy_price = bid + 1
    
        max_buy =  50 - self.emeralds_position - self.emeralds_buy_orders 
        max_sell = self.emeralds_position + 50 - self.emeralds_sell_orders

        self.send_sell_order('EMERALDS', sell_price, -max_sell, msg=f"EMERALDS: MARKET MADE Sell {max_sell} @ {sell_price}")
        self.send_buy_order('EMERALDS', buy_price, max_buy, msg=f"EMERALDS: MARKET MADE Buy {max_buy} @ {buy_price}")



    def run(self, state: TradingState):
        """Only method required. It takes all buy and sell orders for all
        symbols as an input, and outputs a list of orders to be sent."""

        #haven't finished this one yet
    

        return self.result, self.conversions, self.traderData
