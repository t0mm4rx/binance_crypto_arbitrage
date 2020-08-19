import ccxt
import secrets
from datetime import datetime
import telegram
import os
import time
import config
from operator import itemgetter

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
		self.bitfinex = ccxt.bitfinex2({
			'apiKey': secrets.BITFINEX_KEY,
			'secret': secrets.BITFINEX_SECRET,
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
		mode:		buy or sell.
		returns:	the multiplicator for the given exchange.
	"""
	def get_fees(self, exchange, mode):
		if (mode != 'buy' and mode != 'sell'):
			print("Get fees: mode should be buy or sell.")
			return
		if (str(exchange) == "Binance"):
			return 0.999
		elif (str(exchange) == "Bittrex"):
			return 0.998
		elif (str(exchange) == "Bitfinex"):
			if (mode == "buy"):
				return 0.998
			else:
				return 0.999

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
			step1 = (1 / alt_ETH) * self.get_fees(exchange, 'buy')
			step2 = (step1 * alt_BTC) * self.get_fees(exchange, 'sell')
			step3 = (step2 / self.get_price(exchange, 'ETH', 'BTC', mode='ask')) * self.get_fees(exchange, 'buy')
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
			step1 = (self.get_price(exchange, 'ETH', 'BTC', mode='bid')) * self.get_fees(exchange, 'sell')
			step2 = (step1 / alt_BTC) * self.get_fees(exchange, 'buy')
			step3 = (step2 * alt_ETH) * self.get_fees(exchange, 'sell')
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
		Summarize arbitrage, calculate loss/gain, print it, and save it on the disk.
		exchange:		the exchange with whom we did the arbitrage.
		balance_before:	the balance before the arbitrage.
		asset:			the asset that have been arbitrate
	"""
	def summarize_arbitrage(self, exchange, balance_before, asset):
		balance_after = self.get_balance(exchange, "ETH")
		diff = balance_after - balance_before
		self.save_gain(diff)
		diff_eur = diff * self.get_price(exchange, 'ETH', 'EUR')
		diff_percentage = diff / balance_before * 100
		balance_eur = self.get_last_balance() * self.get_price(exchange, 'ETH', 'EUR')
		self.log("➡️ Arbitrage {:5} on {:10}, diff: {:8.6f}ETH ({:.2f} EUR), balance: {:7.6f}ETH ({:.2f} EUR), {:.2f}%".format(asset, str(exchange), diff, diff_eur, self.get_last_balance(), balance_eur, diff_percentage), mode="notification")
		self.log("Balance: {} --> {} ETH".format(balance_before, balance_after))

	"""
		Executes forward arbitrage on given asset:
		ETH -> ALT -> BTC -> ETH.
		exchange:	the wanted exchange.
		asset:		the asset to forward triarb.
	"""
	def run_arbitrage_forward(self, exchange, asset):
		self.log("🔥 Arbitrage on {}: ETH -> {} -> BTC -> ETH".format(exchange, asset))
		balance_before = self.get_balance(exchange, "ETH")
		result1 = self.best_buy(exchange, asset, 'ETH', config.ETH_PERCENTAGE)
		if (not result1):
			self.log("❌ Failed to convert {} to ETH, canceling arbitrage.".format(asset), mode="notification")
			return
		result2 = self.best_sell(exchange, asset, 'BTC', 1)
		if (not result2):
			self.log("❌ Failed to convert {} to BTC, canceling arbitrage. Will convert back {} to ETH.".format(asset, asset), mode="notification")
			self.sell(exchange, asset, 'ETH', amount_percentage=1)
			self.summarize_arbitrage(exchange, balance_before, asset)
			return
		self.buy(exchange, "ETH", "BTC", amount_percentage=1)
		self.summarize_arbitrage(exchange, balance_before, asset)

	"""
		Executes backward arbitrage on given asset:
		ETH -> BTC -> ALT -> ETH.
		exchange:	the wanted exchange.
		asset:		the asset to backward triarb.
	"""
	def run_arbitrage_backward(self, exchange, asset):
		self.log("🔥 Arbitrage on {}: ETH -> BTC -> {} -> ETH".format(exchange, asset))
		balance_before = self.get_balance(exchange, "ETH")
		alt_BTC = self.get_buy_limit_price(exchange, asset, 'BTC')
		alt_ETH = self.get_sell_limit_price(exchange, asset, 'ETH')
		self.sell(exchange, "ETH", "BTC", amount_percentage=config.ETH_PERCENTAGE)
		result1 = self.best_buy(exchange, asset, 'BTC', 1)
		if (not result1):
			self.log("❌ Failed to convert BTC to {}, canceling arbitrage. Will convert BTC to ETH.".format(asset), mode="notification")
			self.buy(exchange, 'ETH', 'BTC', amount_percentage=1)
			self.summarize_arbitrage(exchange, balance_before, asset)
			return
		result2 = self.best_sell(exchange, asset, 'ETH', 1)
		if (not result2):
			self.log("❌ Failed to convert {} to ETH, canceling arbitrage. Forcing convertion from {} to ETH.".format(asset, asset), mode="notification")
			self.sell(exchange, asset, 'ETH', amount_percentage=1)
			self.summarize_arbitrage(exchange, balance_before, asset)
			return
		self.summarize_arbitrage(exchange, balance_before, asset)

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
		if (not bids):
			return None
		bids.sort()
		if (len(bids) < config.ORDERBOOK_INDEX_ESTIMATION):
			return None
		for bid in bids[config.ORDERBOOK_INDEX_ESTIMATION:]:
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
		if (not asks):
			return None
		asks.sort(reverse=True)
		if (len(asks) < config.ORDERBOOK_INDEX_ESTIMATION):
			return None
		for ask in asks[config.ORDERBOOK_INDEX_ESTIMATION:]:
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

	"""
		Get the waiting time needed to bypass DDOS protection.
		exchange:	the wanted exchange to limit.
		returns:	None if no need to limit, a number of seconds to wait if there is.
	"""
	def get_waiting(self, exchange):
		if (str(exchange) == "Bitfinex"):
			return 2
		return None

	"""
		Get last recorded balance, stored in balance.csv file.
		returns:	the last recorded balance in balance.csv file. If the file does not exist we create it.
	"""
	def get_last_balance(self):
		if (os.path.isfile('balance.csv')):
			with open('balance.csv', 'r') as file:
				lines = file.readlines()
				balance = float(lines[-1][:-1].split(',')[1])
				return balance
		else:
			with open('balance.csv', 'w+') as file:
				file.write('date time,balance in ETH\n')
				file.write('{},0\n'.format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
			return 0

	"""
		Add a new balance after a trade.
		gain:	the difference to add to last balance.
	"""
	def save_gain(self, gain):
		last = self.get_last_balance()
		new = last + gain
		with open("balance.csv", 'a') as file:
			file.write("{},{}\n".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), new))

	"""
		Buy at best price possible using decreasing buy limit orders.
	"""
	def best_buy(self, exchange, asset1, asset2, amount_percentage):
		orderbook = self.get_order_book(exchange, asset1, asset2, mode="asks")
		orderbook.sort(key=itemgetter(0))
		for price in orderbook[:config.MAX_ORDERBOOK_TRIES]:
			self.log("Trying to buy {} with {} @{:.8f}.".format(asset1, asset2, price[0]))
			result = self.buy(exchange, asset1, asset2, amount_percentage=amount_percentage, limit=price[0], timeout=config.WAIT_LIMIT_ORDER)
			if (result):
				self.log("✅ Bought {} with {} @{:.8f}.".format(asset1, asset2, price[0]))
				return True
			else:
				self.log("⏳ Failed to buy {} with {} at {:.8f}.".format(asset1, asset2, price[0]))
		self.log("❌ Was not able to buy {} with {}".format(asset1, asset2))
		return False

	"""
		Sell at best price possible using decreasing buy sell orders.
	"""
	def best_sell(self, exchange, asset1, asset2, amount_percentage):
		orderbook = self.get_order_book(exchange, asset1, asset2, mode="bids")
		orderbook.sort(key=itemgetter(0), reverse=True)
		for price in orderbook[:config.MAX_ORDERBOOK_TRIES]:
			self.log("Trying to sell {} to {} @{:.8f}.".format(asset1, asset2, price[0]))
			result = self.sell(exchange, asset1, asset2, amount_percentage=amount_percentage, limit=price[0], timeout=config.WAIT_LIMIT_ORDER)
			if (result):
				self.log("✅ Sold {} to {} @{:.8f}.".format(asset1, asset2, price[0]))
				return True
			else:
				self.log("⏳ Failed to sell {} to {} at {:.8f}.".format(asset1, asset2, price[0]))
		self.log("❌ Was not able to sell {} to {}".format(asset1, asset2))
		return False
