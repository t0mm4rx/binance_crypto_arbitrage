import ccxt
import secrets
from datetime import datetime
import telegram
import time

"""
	This class is a manager for multiple crypto exchanges.
	You can get your balance, create orders...
	Most of functions takes exchange as argument, this is the exchnage you want
	to use. For example, to use binance:
	crypto.get_fees(crypto.binance)
	Asset1 and asset2 represents A1/A2 pair. If you want this ETH/BTC price,
	asset1 is 'ETH' and asset2 is 'BTC'.
"""
class Crypto:

	binance = None
	bittrex = None
	balance = 0
	bot = None
	cache_prices = []
	cache_order_books = []

	def __init__(self):
		self.init_ccxt()
		self.bot = telegram.Bot(token=secrets.TELEGRAM)

	"""
		Reset caches.
	"""
	def flush_cache(self):
		self.cache_prices = []
		self.cache_order_books = []

	"""
		Check if a price is cached, if yes, returns it.
		exchange:	the wanted exchange.
		asset1:		first asset.
		asset2:		second asset.
	"""
	def get_price_cache(self, exchange, asset1, asset2):
		for item in self.cache_prices:
			if (item['exchange'] == str(exchange) and item['asset1'] == asset1 and item['asset2'] == asset2):
				return item['ticker']
		return None

	"""
		Check if an order book is cached, if yes, returns it.
		exchange:	the wanted exchange.
		asset1:		first asset.
		asset2:		second asset.
	"""
	def get_order_book_cache(self, exchange, asset1, asset2):
		for item in self.cache_order_books:
			if (item['exchange'] == str(exchange) and item['asset1'] == asset1 and item['asset2'] == asset2):
				return item['book']
		return None

	"""
		Put price in cache.
		exchange:	the wanted exchange.
		asset1:		first asset.
		asset2:		second asset.
		ticker:		the ccxt object that contains the price to cache.
	"""
	def cache_price(self, exchange, asset1, asset2, ticker):
		self.cache_prices.append({
			'exchange': str(exchange),
			'asset1': asset1,
			'asset2': asset2,
			'ticker': ticker
		})

	"""
		Put order book in cache.
		exchange:	the wanted exchange.
		asset1:		first asset.
		asset2:		second asset.
		book:		the ccxt object that contains the order book to cache.
	"""
	def cache_order_book(self, exchange, asset1, asset2, book):
		self.cache_order_books.append({
			'exchange': str(exchange),
			'asset1': asset1,
			'asset2': asset2,
			'book': book
		})

	"""
		Init exchanges, create connections with secrets file.
	"""
	def init_ccxt(self):
		self.binance = ccxt.binance({
			'apiKey': secrets.BINANCE_KEY,
		    'secret': secrets.BINANCE_SECRET,
			'timeout': 30000,
		    'enableRateLimit': True,
		})
		self.bittrex = ccxt.bittrex({
			'apiKey': secrets.BITTREX_KEY,
		    'secret': secrets.BITTREX_SECRET,
			'timeout': 30000,
		    'enableRateLimit': True,
		})

	"""
		Get your balance for given asset.
		exchange:	the wanted exchange.
		asset:		the wanted asset.
		returns:	the amount of the given asset you own.
	"""
	def get_balance(self, exchange, asset):
		try:
			balance = exchange.fetchBalance()
			if (asset in balance):
				return balance[asset]['free']
			return 0
		except Exception as e:
			self.log("Error while getting balance: {}".format(str(e)))
			raise

	"""
 		Get the multiplicator for each exchange. If the fee is 0.1%, then the
		multiplicator will be 0.999.
		exchange:	the wanted exchange.
		returns:	the multiplicator for the given exchange.
	"""
	def get_fees(self, exchange):
		if (str(exchange) == "Binance"):
			return 0.999
		elif (str(exchange) == "Bittrex"):
			return 0.998

	"""
		Get an asset price.
		exchange:	the wanted exchange.
		asset1:		first asset.
		asset2:		second asset.
		mode:		can be average, bid or ask.
		returns:	the current price if success, None if something is wrong.
	"""
	def get_price(self, exchange, asset1, asset2, mode='average'):
		if (mode != 'average' and mode != 'ask' and mode != 'bid'):
			print("Mode should be average, ask or bid")
			return None
		try:
			ticker = None
			if (self.get_price_cache(exchange, asset1, asset2)):
				ticker = self.get_price_cache(exchange, asset1, asset2)
			else:
				ticker = exchange.fetchTicker('{}/{}'.format(asset1, asset2))
				self.cache_price(exchange, asset1, asset2, ticker)
			if (mode == 'bid'):
				return ticker['bid']
			if (mode == 'ask'):
				return ticker['ask']
			return (ticker['ask'] + ticker['bid']) / 2
		except Exception as e:
			self.log("Error while fetching price for {}/{}: {}".format(asset1, asset2, str(e)))
			return None

	"""
		Get order book for given asset.
		exchange:	the wanted exchange.
		asset1:		first asset.
		asset2:		second asset.
		mode:		can be bids or asks
		returns:	the order book as a 2D array, None if something is wrong.
	"""
	def get_order_book(self, exchange, asset1, asset2, mode="bids"):
		if (mode != 'bids' and mode != 'asks'):
			print('Get order book: mode should be bids or asks.')
			return None
		try:
			order_book = self.get_order_book_cache(exchange, asset1, asset2)
			if (not order_book):
				order_book = exchange.fetchOrderBook('{}/{}'.format(asset1, asset2))
				self.cache_order_book(exchange, asset1, asset2, order_book)
			return order_book[mode]
		except Exception as e:
			self.log("Error while fetching order book for {}/{}: {}".format(asset1, asset2, str(e)))
			return None

	"""
		Check if at least one order is open for the given asset and exchange.
		exchange:	the wanted exchange.
		asset1:		first asset.
		asset2:		second asset.
		returns:	True/False if there is an open order.
	"""
	def is_open_order(self, exchange, asset1, asset2):
		try:
			data = exchange.fetchOpenOrders('{}/{}'.format(asset1, asset2))
			return len(data) > 0
		except Exception as e:
			self.log("Error while fetching open orders for {}/{}: {}".format(asset1, asset2, str(e)))
			return False

	"""
		Cancel all orders for given assets.
		exchange:	the wanted exchange.
		asset1:		first asset.
		asset2:		second asset.
		returns:	True if success, False if something is wrong.
	"""
	def cancel_orders(self, exchange, asset1, asset2):
		try:
			orders = exchange.fetchOpenOrders('{}/{}'.format(asset1, asset2))
			for order in orders:
				exchange.cancelOrder(order['id'], '{}/{}'.format(asset1, asset2))
			return True
		except Exception as e:
			self.log("Error while canceling orders for {}/{}: {}".format(asset1, asset2, str(e)))
			return False

	"""
		Estimate the profit for forward arbitrage on given asset.
		exchange:	the wanted exchange.
		asset:		the asset to try forward triarb.
		returns:	the estimated percentage difference after triarb.
	"""
	def estimate_arbitrage_forward(self, exchange, asset):
		try:
			alt_ETH = self.get_buy_limit_price(exchange, asset, 'ETH')
			alt_BTC = self.get_sell_limit_price(exchange, asset, 'BTC')
			if (not alt_BTC or not alt_ETH):
				self.log("Less than 3 orders for {} on {}, skipping.".format(asset, str(exchange)))
				return -100
			step1 = (1 / alt_ETH) * self.get_fees(exchange)
			step2 = (step1 * alt_BTC) * self.get_fees(exchange)
			step3 = (step2 / self.get_price(exchange, 'ETH', 'BTC', mode='ask')) * self.get_fees(exchange)
			return (step3 - 1) * 100
		except ZeroDivisionError:
			return -1

	"""
		Estimate the profit for backward arbitrage on given asset.
		exchange:	the wanted exchange.
		asset:		the asset to try backward triarb.
		returns:	the estimated percentage difference after triarb.
	"""
	def estimate_arbitrage_backward(self, exchange, asset):
		try:
			alt_BTC = self.get_buy_limit_price(exchange, asset, 'BTC')
			alt_ETH = self.get_sell_limit_price(exchange, asset, 'ETH')
			if (not alt_BTC or not alt_ETH):
				self.log("Less than 3 orders for {} on {}, skipping.".format(asset, str(exchange)))
				return -100
			step1 = (self.get_price(exchange, 'ETH', 'BTC', mode='bid')) * self.get_fees(exchange)
			step2 = (step1 / alt_BTC) * self.get_fees(exchange)
			step3 = (step2 * alt_ETH) * self.get_fees(exchange)
			return (step3 - 1) * 100
		except ZeroDivisionError:
			return -1

	"""
		Create a buy order. 'amount' or 'amount_percentage' should be specified.
		If limit is specified it will be a limit order, otherwise it will be
		a market order.
		If timeout is specified, then the limit order will be cancelled if the
		order isn't completed after timeout.
		exchange:			the wanted exchange.
		asset1:				first asset.
		asset2:				second asset.
		amount_percentage:	percentage of first asset you want to buy with.
		amount:				fixed amount of second asset you want to buy.
		limit:				the maximum price you want to buy asset2.
		timeout:			the maximum delay to wait before canceling limit order.
		returns:			True if the trade has been completed, False if not.
	"""
	def buy(self, exchange, asset1, asset2, amount_percentage=None, amount=None, limit=None, timeout=None):
		try:
			if (amount_percentage):
				asset2_available = self.get_balance(exchange, asset2) * amount_percentage
				amount = asset2_available / self.get_price(exchange, asset1, asset2, mode='ask')
			self.log("Buying {:.6} {} with {} on {}.".format(
				amount,
				asset1,
				asset2,
				exchange
			))
			if (limit):
				self.log("Limit @{}.".format(limit))
			if (not limit):
				self.log("Buying at market price.")
				exchange.createMarketBuyOrder(
					'{}/{}'.format(asset1, asset2),
					amount
				)
				return True
			else:
				exchange.createLimitBuyOrder(
					'{}/{}'.format(asset1, asset2),
					amount,
					limit
				)
				if (timeout):
					time.sleep(timeout)
					if (self.is_open_order(exchange, asset1, asset2)):
						self.cancel_orders(exchange, asset1, asset2)
						self.log("Canceled limit order for {}/{} after timeout.".format(asset1, asset2))
						return False
					else:
						self.log("Limit order executed.")
						return True
				else:
					return False
		except Exception as e:
			self.log("Error while buying: {}".format(str(e)))
			return False

	"""
		Create a sell order. 'amount' or 'amount_percentage' should be specified.
		If limit is specified it will be a limit order, otherwise it will be
		a market order.
		If timeout is specified, then the limit order will be cancelled if the
		order isn't completed after timeout.
		exchange:			the wanted exchange.
		asset1:				first asset.
		asset2:				second asset.
		amount_percentage:	percentage of first asset you want to sell.
		amount:				fixed amount of first asset you want to sell.
		limit:				the minimum price you want to sell asset1.
		timeout:			the maximum delay to wait before canceling limit order.
		returns:			True if the trade has been completed, False if not.
	"""
	def sell(self, exchange, asset1, asset2, amount_percentage=None, amount=None, limit=None, timeout=None):
		try:
			if (amount_percentage):
				amount = self.get_balance(exchange, asset1) * amount_percentage
			self.log("Selling {:.6f} {} to {} on {}.".format(
				amount,
				asset1,
				asset2,
				exchange
			))
			if (limit):
				self.log("Limit @{}.".format(limit))
			if (not limit):
				self.log("Selling at market price.")
				exchange.createMarketSellOrder(
					'{}/{}'.format(asset1, asset2),
					amount
				)
				return True
			else:
				exchange.createLimitSellOrder(
					'{}/{}'.format(asset1, asset2),
					amount,
					limit
				)
				if (timeout):
					time.sleep(timeout)
					if (self.is_open_order(exchange, asset1, asset2)):
						self.cancel_orders(exchange, asset1, asset2)
						self.log("Canceled limit order for {}/{} after timeout.".format(asset1, asset2))
						return False
					else:
						self.log("Limit order executed.")
						return True
				else:
					return False
		except Exception as e:
			self.log("Error while selling: {}".format(str(e)))
			return False

	"""
		Executes forward arbitrage on given asset:
		ETH -> ALT -> BTC -> ETH.
		exchange:	the wanted exchange.
		asset:		the asset to forward triarb.
	"""
	def run_arbitrage_forward(self, exchange, asset):
		self.log("Arbitrage on {}: ETH -> {} -> BTC -> ETH".format(exchange, asset))
		balance_before = self.get_balance(exchange, "ETH")
		alt_ETH = self.get_buy_limit_price(exchange, asset, 'ETH')
		alt_BTC = self.get_sell_limit_price(exchange, asset, 'BTC')
		result1 = self.buy(exchange, asset, "ETH", amount_percentage=0.8, limit=alt_ETH, timeout=1)
		if (not result1):
			self.log("Failed to convert ETH to {} @{}.".format(asset, alt_ETH))
			return
		result2 = self.sell(exchange, asset, "BTC", amount_percentage=1, limit=alt_BTC, timeout=1)
		if (not result2):
			self.log("Failed to convert {} to BTC @{}. {} should be remaining on wallet.".format(asset, alt_BTC, asset))
			return
		self.buy(exchange, "ETH", "BTC", amount_percentage=1)
		balance_after = self.get_balance(exchange, "ETH")
		diff = balance_after - balance_before
		diff_eur = diff * self.get_price(exchange, 'ETH', 'EUR')
		self.balance += diff
		self.log("Arbitrage {:5} on {:10}, diff: {:8.6f}ETH ({:.6f} EUR), balance: {:7.6f}ETH".format(asset, str(exchange), diff, diff_eur, self.balance), mode="notification")
		self.log("Balance: {} --> {} ETH".format(balance_before, balance_after))

	"""
		Executes backward arbitrage on given asset:
		ETH -> BTC -> ALT -> ETH.
		exchange:	the wanted exchange.
		asset:		the asset to backward triarb.
	"""
	def run_arbitrage_backward(self, exchange, asset):
		self.log("Arbitrage on {}: ETH -> BTC -> {} -> ETH".format(exchange, asset))
		balance_before = self.get_balance(exchange, "ETH")
		alt_BTC = self.get_buy_limit_price(exchange, asset, 'BTC')
		alt_ETH = self.get_sell_limit_price(exchange, asset, 'ETH')
		self.sell(exchange, "ETH", "BTC", amount_percentage=0.8)
		self.buy(exchange, asset, "BTC", amount_percentage=1, limit=alt_BTC)
		self.sell(exchange, asset, "ETH", amount_percentage=1, limit=alt_ETH)
		balance_after = self.get_balance(exchange, "ETH")
		diff = balance_after - balance_before
		diff_eur = diff * self.get_price(exchange, 'ETH', 'EUR')
		self.balance += diff
		self.log("Arbitrage {:5} on {:10}, diff: {:8.6f}ETH ({:.6f} EUR), balance: {:7.6f}ETH".format(asset, str(exchange), diff, diff_eur, self.balance), mode="notification")
		self.log("Balance: {} --> {} ETH".format(balance_before, balance_after))

	"""
		Get the safest and lowest price to limit buy the given asset.
		We start from the third lowest price to avoid volatility, then we
		returns the first price with enough value to fullfill the order.
		exchange:	the wanted exchange.
		asset1:		first asset.
		asset2:		second asset.
		returns:	the advised price to place limit buy order.
	"""
	def get_buy_limit_price(self, exchange, asset1, asset2, amount=1):
		bids = self.get_order_book(exchange, asset1, asset2, mode="asks")
		bids.sort()
		if (len(bids) < 3):
			return None
		for bid in bids[3:]:
			if (bid[1] >= amount):
				return bid[0]

	"""
		Get the safest and highest price to limit sell the given asset.
		We start from the third highest price to avoid volatility, then we
		returns the first price with enough value to fullfill the order.
		exchange:	the wanted exchange.
		asset1:		first asset.
		asset2:		second asset.
		returns:	the advised price to place limit sell order.
	"""
	def get_sell_limit_price(self, exchange, asset1, asset2, amount=1):
		asks = self.get_order_book(exchange, asset1, asset2, mode="bids")
		asks.sort(reverse=True)
		if (len(asks) < 3):
			return None
		for ask in asks[3:]:
			if (ask[1] >= amount):
				return ask[0]

	"""
		Logs given string.
		text:	the string to log.
		mode:	can be log or notification, if notification it will send a message to the Telegram bot.
	"""
	def log(self, text, mode="log"):
		formatted_text = "[{}] {}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), text)
		if (mode == "notification"):
			self.bot.sendMessage(chat_id=secrets.TELEGRAM_CHAT, text=formatted_text)
		if (mode == "notification" or mode == "log"):
			with open('logs.txt', 'a+') as file:
				file.write(formatted_text)
				file.write("\n")
