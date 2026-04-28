import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplcursors
import glob

price_files = sorted(glob.glob('Round 4/prices_round_4_day_*.csv'))
trade_files = sorted(glob.glob('Round 4/trades_round_4_day_*.csv'))

print("Price files:", price_files)
print("Trade files:", trade_files)

products = ['HYDROGEL_PACK', 'VELVETFRUIT_EXTRACT']

def make_scatter_handler(scatter):
    def handler(sel):
        scatter_local = sel.artist
        x = sel.target[0]
        timestamps = scatter_local._timestamps
        idx = np.abs(timestamps - x).argmin()
        if hasattr(scatter_local, '_trade_info') and idx < len(scatter_local._trade_info):
            sel.annotation.set_text(scatter_local._trade_info[idx])
            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)
        else:
            sel.annotation.set_text("")
    return handler

fig, axes = plt.subplots(len(price_files), 2, figsize=(14, 5 * len(price_files)))

for idx, price_file in enumerate(price_files):
    day = price_file.split('_day_')[1].replace('.csv', '')
    price_df = pd.read_csv(price_file, sep=';')
    
    trade_file = f'Round 4/trades_round_4_day_{day}.csv'
    trade_df = pd.read_csv(trade_file, sep=';')
    
    for p_idx, product in enumerate(products):
        ax = axes[idx, p_idx] if len(price_files) > 1 else axes[p_idx]
        product_price_df = price_df[price_df['product'] == product].copy()
        product_price_df = product_price_df[product_price_df['mid_price'] > 0]
        product_price_df['rolling_mean'] = product_price_df['mid_price'].rolling(window=50).mean()
        
        ax.plot(product_price_df['timestamp'], product_price_df['rolling_mean'], marker='o', markersize=2, label='Mid Price')
        
        product_trade_df = trade_df[trade_df['symbol'] == product]
        
        scatter = ax.scatter(product_trade_df['timestamp'], product_trade_df['price'], 
                            c='red', s=30, zorder=5, alpha=0.7, label='Trades')
        
        timestamps = product_trade_df['timestamp'].values
        trade_info = []
        for _, trade in product_trade_df.iterrows():
            buyer = trade['buyer'].replace('Mark ', 'M')
            seller = trade['seller'].replace('Mark ', 'M')
            trade_info.append(f"{buyer} bought, {seller} sold\nQty: {trade['quantity']}")
        scatter._timestamps = timestamps
        scatter._trade_info = trade_info
        
        mplcursors.cursor(scatter, hover=True).connect("add", make_scatter_handler(scatter))
        
        ax.set_title(f"{product} - Day {day}")
        ax.set_xlabel('Timestamp')
        ax.set_ylabel('Mid Price')
        ax.grid(True)
        ax.legend()

plt.tight_layout()
plt.show()