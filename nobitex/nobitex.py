import requests as rq
import json
import time
import datetime
import jdatetime

base_url = 'https://api.nobitex.ir'
login_url = '/auth/login/'
orderbook_url = '/v2/orderbook'
trades_url = '/v2/trades'
statistics_url = '/market/stats'
stats_ohlc_url = '/market/udf/history?symbol={}&resolution={}&from={}&to={}'
stats_global_url = '/market/global-stats'
profile_url = '/users/profile'
login_attemps_url = '/users/login-attempts'
referral_code = '/users/get-referral-code'
add_card_url = '/users/cards-add'
add_account_url = '/users/accounts-add'
user_limitations_url = '/users/limitations'
wallets_list_url = '/users/wallets/list'
wallet_balance_url = '/users/wallets/balance'
user_transactions_url = '/users/wallets/transactions/list'
user_deposits_url = '/users/wallets/deposits/list'
generate_addres_url = '/users/wallets/generate-address'
order_add_url = '/market/orders/add'
order_status_url = '/market/orders/status'
order_update_url = '/market/orders/update-status'
order_cancel_url = '/market/orders/cancel-old'

# function decorator for checking Response
def check_load_response(field=[]):
    def check_load_response_decorator(func):
        def function_wrapper(self, *args, **kwargs):
            res = func(self, *args, **kwargs)
            # check the response
            assert res.ok, 'Response is not ok!'
            assert res.status_code == 200, 'Response status code is not 200, status code:{}'.format(
                res.status_code)
            # get the content of response and put it in a dictionary
            res = json.loads(res.text)
            if 'status' in res.keys():
                assert res['status'] is not 'success', 'Response failed, status:{}'.format(
                    res['status'])
            elif 's' in res.keys():
                assert res['s'] is not 'ok', 'Response failed, status:{}'.format(
                    res['status'])
            else:
                assert False, 'Response status field is not defined! Response:{}'.format(res)
            field_list = field if isinstance(field, list) else [field, ]
            def fn(): return list(filter(lambda x: x in res.keys(), field_list)) == field_list
            assert fn(), "Response hasn't {} arguments,Response:{}".format(field_list, res)
            result = dict()
            for f in field_list:
                result[f] = res[f]
            return result
        return function_wrapper
    return check_load_response_decorator

# check login_required"btc"
def login_required(func):
    def function_wrapper(self, *args, **kwargs):
        now = time.time()
        dt = now-self.login_time
        if self.headers == None:
            # it did not logged in until now
            self.login()
        else:
            if self.remember == 'no':
                req_dt = 24*60*60
                if dt>req_dt:
                    self.login()
            elif self.remember == 'yes':
                req_dt = 30*24*60*60
                # check dt of login
                if dt>req_dt:
                    self.login()
            else:
                # assert self.remember is not defined
                assert False, "remember must be 'yes' or 'no', remember:{}".format(self.remember)
        res = func(self, *args, **kwargs)
        # check if the response has authorization error, auth and call function
        if res.status_code==401:
            self.login()
            res = func(self, *args, **kwargs)
        return res
    return function_wrapper

# check string is floatable
def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

coins = ['btc', 'eth', 'ltc', 'xrp', 'bch',
            'bnb', 'eos', 'xlm', 'etc', 'trx']
base_coins = ['usdt', 'rls']

class Client:

    def __init__(self, username=None, password=None, remember='no'):
        self.username = username
        self.password = password
        self.remember = remember
        self.headers = None
        self.d2t = lambda d: time.mktime(d.timetuple()) + d.microsecond / 1E6 
        self.login_time = 0.0

    def loads(self, response):
        return json.loads(response.content)

    def log(self, text):
        print(text)

    def connect(self, url, data={}, method='post'):
        url = base_url + url
        if method == 'post':
            res = rq.post(url, data=data, headers=self.headers)
        elif method == 'get':
            res = rq.get(url, headers=self.headers)
        return res

    @check_load_response('key')
    def _login(self, username=None, password=None, remember=None):
        self.username = username if username != None else self.username
        self.password = password if password != None else self.password
        self.remember = remember if remember != None else self.remember
        data = {'username': self.username,
                'password': self.password,
                'remember': self.remember}
        res = self.connect(login_url, data=data)
        return res

    def login(self):
        key = self._login()
        self.headers = {'Authorization': 'Token '+key['key']}
        self.login_time = time.time()

    def get_symbols(self, market='all'):
        assert market in ['all', 'irt', 'IRT', 'usdt', 'USDT', 'original', 'professional'],\
            'market type is not defined, market:{}'.format(market)
        symbols = ['BTCIRT', 'ETHIRT', 'LTCIRT', 'XRPIRT', 'BCHIRT', 'BNBIRT',
                   'EOSIRT', 'XLMIRT', 'ETCIRT', 'TRXIRT', 'USDTIRT', 'BTCUSDT',
                   'ETHUSDT', 'LTCUSDT', 'XRPUSDT', 'BCHUSDT', 'BNBUSDT', 'EOSUSDT',
                   'XLMUSDT', 'ETCUSDT', 'TRXUSDT']
        irt_symbols = ['BTCIRT', 'ETHIRT', 'LTCIRT', 'XRPIRT', 'BCHIRT',
                       'BNBIRT', 'EOSIRT', 'XLMIRT', 'ETCIRT', 'TRXIRT', 'USDTIRT']
        usdt_symbols = ['BTCUSDT', 'ETHUSDT', 'LTCUSDT', 'XRPUSDT',
                        'BCHUSDT', 'BNBUSDT', 'EOSUSDT', 'XLMUSDT', 'ETCUSDT', 'TRXUSDT']
        if market == 'all':
            return symbols
        elif market == 'irt' or market == 'IRT' or market == 'original':
            return irt_symbols
        elif market == 'usdt' or market == 'USDT' or market == 'professional':
            return usdt_symbols
        else:
            assert False, 'market type is not defined, market:{}'.format(
                market)

    @check_load_response(['bids', 'asks'])
    def orderbook(self, symbol):
        url = orderbook_url
        data = {'symbol': symbol}
        res = self.connect(url, data=data)
        return res

    @check_load_response('trades')
    def trades(self, symbol):
        url = trades_url
        data = {'symbol': symbol}
        res = self.connect(url, data=data)
        return res

    @check_load_response('stats')
    def market_stats(self, coin, base_coin):
        assert base_coin in base_coins, '{} is not defined base coin. base coins:{}'.format(
            base_coin, base_coins)
        assert coin in coins, '{} is not defined coin. coins:{}'.format(coin, coins)
        url = statistics_url
        data = {"srcCurrency": coin, "dstCurrency": base_coin}
        res = self.connect(url, data=data)
        return res

    @check_load_response(['t', 'o', 'h', 'l', 'c', 'v'])
    def market_ohlc(self, symbol, resolution, from_, to):
        # check symbol
        assert symbol in self.get_symbols(), '{} is not defined. symbols:{}'.format(symbol, self.get_symbols())
        # check resolutions 
        resolutions = {'1h':60,'3h':180,'6h':360,'12h':720,'1d':'D','2d':'2D','3d':'3D'}
        assert resolution in resolutions.keys(), '{} is not defined. resolutions:{}'.format(resolution, resolutions)
        # time, datetime and jdatetime are supported
        assert isinstance(from_, (int, float, datetime.datetime, jdatetime.datetime)), '{} is not correct time format. please use time, datetime or jdatetime module.'.format(from_)
        assert isinstance(to, (int, float, datetime.datetime, jdatetime.datetime)), '{} is not correct time format. please use time, datetime or jdatetime module.'.format(to)
        # convert datetime and jdatetime to time format
        if not isinstance(from_, (float, int)):
            from_ = self.d2t(from_)
        if not isinstance(to, (float, int)):
            to = self.d2t(to)
        # nobitex accept int for 'from' and 'to'
        from_, to = int(from_), int(to)
        # 'from' must be before 'to'
        assert from_<to , 'from must be lower than to.from:{}, to:{}'.format(from_, to)

        url = stats_ohlc_url
        url = url.format(symbol, resolutions[resolution], from_, to)
        res = self.connect(url, method='get')
        return res
    
    @check_load_response(coins)
    def global_market_stats(self):
        url = stats_global_url
        res = self.connect(url)
        return res

    @check_load_response(['profile','tradeStats'])
    @login_required
    def user_profile(self):
        url = profile_url
        res = self.connect(url, method='get')
        return res

    @check_load_response('attempts')
    @login_required
    def login_attemps(self):
        url = login_attemps_url
        res = self.connect(url, method='get')
        return res

    @check_load_response()
    @login_required
    def add_bank_card(self, card_number, bank_name):
        assert isinstance(card_number,(str,int)), 'Card number is not valid, Card number:{}'.format(card_number)
        assert isinstance(bank_name, str), 'Bank name must be string, Bank name:{}'.format(bank_name)
        url = add_card_url
        data = {"number":str(card_number),"bank":str(bank_name)}
        self.connect(url, data=data)

    @check_load_response()
    @login_required
    def add_bank_account(self, card_number, bank_name, shaba):
        assert isinstance(card_number,(str,int)), 'Card number is not valid, Card number:{}'.format(card_number)
        assert isinstance(bank_name, str), 'Bank name must be string, Bank name:{}'.format(bank_name)
        assert isinstance(shaba, str), 'Shaba must be string, Shaba:{}'.format(shaba)
        url = add_card_url
        data = {"number":str(card_number),"bank":str(bank_name)}
        self.connect(url, data=data)

    @check_load_response('limitations')
    @login_required
    def user_limitations(self):
        url = user_limitations_url
        res = self.connect(url)
        return res
    
    @check_load_response('wallets')
    @login_required
    def user_wallets(self):
        url = wallets_list_url
        res = self.connect(url)
        return res

    @check_load_response('balance')
    @login_required
    def user_balance(self, coin):
        url = wallet_balance_url
        assert coin in coins,'Coin is not in {}, Coin:{}'.format(coins,coin)
        data = {"currency":coin}
        res = self.connect(url, data=data)
        return res

    @check_load_response('transactions')
    @login_required
    def user_transactions(self, wallet_id):
        wallet_id = str(wallet_id)
        assert wallet_id.isdigit(),'Wallet id must be a number, Id:{}'.format(wallet_id)
        url = user_transactions_url
        data = {'wallet':wallet_id}
        res = self.connect(url, data=data)
        return res
    
    @check_load_response(['diposits','withdraws'])
    @login_required
    def user_diposits_withdraw(self, wallet_id):
        wallet_id = str(wallet_id)
        assert wallet_id.isdigit(),'Wallet id must be a number, Id:{}'.format(wallet_id)
        url = user_deposits_url
        data = {'wallet':wallet_id}
        res = self.connect(url, data=data)
        return res

    @check_load_response('address')
    @login_required
    def generate_address(self,wallet_id):
        wallet_id = str(wallet_id)
        assert wallet_id.isdigit(),'Wallet id must be a number, Id:{}'.format(wallet_id)
        url = generate_addres_url
        data = {'wallet':wallet_id}
        res = self.connect(url, data=data)
        return res

    @check_load_response('order')
    @login_required
    def order_add(self, order_type, excution, coin, base_coin, amount, price=None):
        assert order_type in ['buy','sell'], 'Order type must be `buy` or `sell`, Order type:{}'.format(order_type)
        assert excution in ['limit','market'], 'Order type must be `buy` or `market`, Order limit:{}'.format(excution)
        assert coin in coins, 'Coin must be in {}, Coin:{}'.format(coins, coin)
        assert base_coin in base_coins, 'Base coin must be in {}, Base coin:{}'.format(base_coins, base_coin)
        assert isfloat(amount), 'Amount must be a number, Amount:{}'.format(amount)
        assert isfloat(price) or price==None, 'Price must be a number, Price:{}'.format(price)
        url = order_add_url
        if price==None:
            data = {"type":order_type,"srcCurrency":coin,"dstCurrency":base_coin,"amount":amount}
        else:
            data = {"type":order_type,"srcCurrency":coin,"dstCurrency":base_coin,"amount":amount,"price":price}
        res = self.connect(url, data=data)
        return res
    
    @check_load_response('order')
    @login_required
    def order_status(self, order_id):
        order_id = str(order_id)
        assert order_id.isdigit(), 'Order id must be digit. Id:{}'.format(order_id)
        url = order_status_url
        data = {"id":order_id}
        res = self.connect(url, data=data)
        return res

    @check_load_response('updatedStatus')
    @login_required
    def order_update_status(self, order_id, status):
        order_id = str(order_id)
        assert order_id.isdigit(), 'Order id must be digit. Id:{}'.format(order_id)
        assert status in ['new','active','canceled'], \
            'Order status must be one of `new`, `active` or `canceled`,Order status:{}'.format(status)
        url = order_status_url
        data = {"order":order_id,"status":status}
        res = self.connect(url, data=data)
        return res

    @check_load_response()
    @login_required
    def order_cancel(self, excution, coin, base_coin, hours='all'):
        url = order_cancel_url
        assert excution in ['limit','market'], 'Order type must be `buy` or `market`, Order limit:{}'.format(excution)
        assert coin in coins, 'Coin must be in {}, Coin:{}'.format(coins, coin)
        assert base_coin in base_coins, 'Base coin must be in {}, Base coin:{}'.format(base_coins, base_coin)
        assert isfloat(hours) or hours=='all', 'Hours must be `all` or floatable, Hours:{}'.format(hours)
        if hours=='all':
            data = {"execution":excution,"srcCurrency":coin,"dstCurrency":base_coin}
        else:
            data = {"execution":excution,"srcCurrency":coin,"dstCurrency":base_coin,"hours":hours}
        res = self.connect(url, data=data)
        return res

    def order_update(self,order_id):
        raise NotImplementedError
