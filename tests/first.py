# test
print('test')
import numpy as np
from nobitex.nobitex import Client

username = 'am.civil71@gmail.com'
password = 'QL@BkkScCYE5X3g'
c = Client(username=username, password=password)
c.login()
r = c.orderbook('BTCIRT')
r = c.trades('BTCIRT')
r = c.market_stats('btc', 'rls')
r = c.market_ohlc('BTCIRT', '1d', 1560120967, 1562230967)
r = c.global_market_stats()
r = c.user_profile()
r = c.login_attemps()
r = c.user_limitations()
r = c.user_wallets()
print(r)
