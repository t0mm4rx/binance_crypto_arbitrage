import ccxt
import secrets
from datetime import datetime
import telegram

class Crypto:

	binance = None
	bittrex = None
	balance = 0
	bot = None
	cache = []

	def __init__(self):
		self.init_ccxt()
		self.bot = telegram.Bot(token=secrets.TELEGRAM)

	"""
		Reset cache.
	"""
	def flush_cache(self):
		self.cache = []

	"""
		Get cached price.
	"""
	def get_price_cache(self, exchange, asset1, asset2):
		for item in self.cache:
			if (item['exchange'] == str(exchange) and item['asset1'] == asset1 and item['asset2'] == asset2):
				return item['ticker']
		return None

	"""
		Put price in cache.
	"""
	def cache_price(self, exchange, asset1, asset2, ticker):
		self.cache.append({
			'exchange': str(exchange),
			'asset1': asset1,
			'asset2': asset2,
			'ticker': ticker
		})

	"""
		Init exchanges.
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
	"""
	def get_balance(self, exchange, asset):
		try:
			balance = exchange.fetchBalance()
			if (asset in balance):
				return balance[asset]['free']
			return 0
		except Exception as e:
			self.log("Error while getting balance: {}".format(str(e)), mode="log")
			raise

	"""
 		Get the amount of value received after fees.
	"""
	def get_fees(self, exchange):
		if (str(exchange) == "Binance"):
			return 0.999
		elif (str(exchange) == "Bittrex"):
			return 0.998

	"""
		Get an asset price, mode can be average, bid or ask.
	"""
	def get_price(self, exchange, asset1, asset2, mode='average'):
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
			self.log("Error while fetching price for {}/{}: {}".format(asset1, asset2, str(e)), mode="log")
			raise

	"""
		Get order book for given asset.
	"""
	def get_order_book(self, exchange, asset1, asset2, mode="bids"):
		if (mode != 'bids' and mode != 'asks'):
			print('Get order book: mode should be bids or asks.')
			return
		try:
			data = exchange.fetchOrderBook('{}/{}'.format(asset1, asset2))
			return data[mode]
		except Exception as e:
			self.log("Error while fetching order book for {}/{}: {}".format(asset1, asset2, str(e)), mode="log")
			raise

	"""
		Is there any open order for given asset.
	"""
	def is_open_order(self, exchange, asset1, asset2):
		try:
			data = exchange.fetchOpenOrders('{}/{}'.format(asset1, asset2))
			return len(data) > 0
		except Exception as e:
			self.log("Error while fetching open orders for {}/{}: {}".format(asset1, asset2, str(e)), mode="log")
			raise

	"""
		Cancel orders for given asset.
	"""
	def cancel_orders(self, exchange, asset1, asset2):
		try:
			orders = exchange.fetchOpenOrders('{}/{}'.format(asset1, asset2))
			for order in orders:
				exchange.cancelOrder(order['id'], '{}/{}'.format(asset1, asset2))
		except Exception as e:
			self.log("Error while canceling orders for {}/{}: {}".format(asset1, asset2, str(e)), mode="log")
			raise

	"""
		Estimate the profit from backward arbitrage on given asset.
	"""
	def estimate_arbitrage_forward(self, exchange, asset):
		try:
			step1 = (1 / self.get_price(exchange, asset, 'ETH', mode='ask')) * self.get_fees(exchange)
			step2 = (step1 * self.get_price(exchange, asset, 'BTC', mode='bid')) * self.get_fees(exchange)
			step3 = (step2 / self.get_price(exchange, 'ETH', 'BTC', mode='ask')) * self.get_fees(exchange)
			return (step3 - 1) * 100
		except ZeroDivisionError:
			return -1

	"""
		Estimate the profit from backward arbitrage on given asset.
	"""
	def estimate_arbitrage_backward(self, exchange, asset):
		try:
			step1 = (self.get_price(exchange, 'ETH', 'BTC', mode='bid')) * self.get_fees(exchange)
			step2 = (step1 / self.get_price(exchange, asset, 'BTC', mode='ask')) * self.get_fees(exchange)
			step3 = (step2 * self.get_price(exchange, asset, 'ETH', mode='bid')) * self.get_fees(exchange)
			return (step3 - 1) * 100
		except ZeroDivisionError:
			return -1

	"""
		Create a buy order. You can specify either to buy a fixed amount
		of the given asset, or a percentage of all your balance.
		If limit is set it will be a limit order.
		If timeout is set the limit order will be close after timeout.
	"""
	def buy(self, exchange, asset1, asset2, amount_percentage=None, amount=None, limit=None, timeout=None):
		try:
			if (amount_percentage):
				asset2_available = self.get_balance(exchange, asset2) * amount_percentage
				amount = asset2_available / self.get_price(exchange, asset1, asset2, mode='ask')
				self.log("Buying {:.6} {} with {:.2f}% ({:.8f}) of {} available on {}.".format(
					amount,
					asset1,
					amount_percentage * 100,
					asset2_available,
					asset2,
					exchange
				), mode="log")
				if (not limit):
					exchange.createMarketBuyOrder(
						'{}/{}'.format(asset1, asset2),
						amount
					)
				else:
					exchange.createLimitBuyOrder(
						'{}/{}'.format(asset1, asset2),
						amount,
						limit
					)
			elif (amount):
				self.log("Buying {:.6f} {} with {} on {}.".format(
					amount,
					asset1,
					asset2,
					exchange
				), mode="log")
				if (not limit):
					exchange.createMarketBuyOrder(
						'{}/{}'.format(asset1, asset2),
						amount
					)
				else:
					exchange.createLimitBuyOrder(
						'{}/{}'.format(asset1, asset2),
						amount,
						limit
					)
			else:
				self.log("Amount should be given, not buying!", mode="log")
				return
		except Exception as e:
			self.log("Error while buying: {}".format(str(e)), mode="log")
			raise

	"""
		Create a sell order. You can specify either to sell a fixed amount
		of the given asset, or a percentage of all your balance.
		If limit is set it will be a limit order.
		If timeout is set the limit order will be close after timeout.
	"""
	def sell(self, exchange, asset1, asset2, amount_percentage=None, amount=None, limit=None):
		try:
			if (amount_percentage):
				amount = self.get_balance(exchange, asset1) * amount_percentage
				self.log("Selling {:.2f}% ({:.6f}) of {} to {} on {}.".format(
					amount_percentage * 100,
					amount,
					asset1,
					asset2,
					exchange
				), mode="log")
				if (not limit):
					exchange.createMarketSellOrder(
						'{}/{}'.format(asset1, asset2),
						amount
					)
				else:
					exchange.createLimitSellOrder(
						'{}/{}'.format(asset1, asset2),
						amount,
						limit
					)

			elif (amount):
				self.log("Selling {} {} to {} on {}.".format(
					amount,
					asset1,
					asset2,
					exchange
				), mode="log")
				if (not limit):
					exchange.createMarketSellOrder(
						'{}/{}'.format(asset1, asset2),
						amount
					)
				else:
					exchange.createLimitSellOrder(
						'{}/{}'.format(asset1, asset2),
						amount,
						limit
					)
			else:
				self.log("Amount should be given, not selling!", mode="log")
				return
		except Exception as e:
			self.log("Error while selling: {}".format(str(e)), mode="log")
			raise

	"""
		Executes forward arbitrage on given asset:
		ETH -> ALT -> BTC -> ETH
	"""
	def run_arbitrage_forward(self, exchange, asset):
		self.log("Arbitrage on {}: ETH -> {} -> BTC -> ETH".format(exchange, asset), mode="log")
		balance_before = self.get_balance(exchange, "ETH")
		self.buy(exchange, asset, "ETH", amount_percentage=0.8)
		self.sell(exchange, asset, "BTC", amount_percentage=1)
		self.buy(exchange, "ETH", "BTC", amount_percentage=1)
		balance_after = self.get_balance(exchange, "ETH")
		diff = balance_after - balance_before
		diff_eur = diff * self.get_price(exchange, 'ETH', 'EUR')
		self.log("Différence: {:.6f} ETH = {:.6f} EUR".format(diff, diff_eur), mode="log")
		self.balance += diff
		self.log("Arbitrage {:5} on {:10}, diff: {:8.6f}ETH, balance: {:7.6f}ETH".format(asset, str(exchange), diff, self.balance))

	"""
		Executes backward arbitrage on given asset:
		ETH -> BTC -> ALT -> ETH
	"""
	def run_arbitrage_backward(self, exchange, asset):
		self.log("Arbitrage on {}: ETH -> BTC -> {} -> ETH".format(exchange, asset), mode="log")
		balance_before = self.get_balance(exchange, "ETH")
		self.sell(exchange, "ETH", "BTC", amount_percentage=0.8)
		self.buy(exchange, asset, "BTC", amount_percentage=1)
		self.sell(exchange, asset, "ETH", amount_percentage=1)
		balance_after = self.get_balance(exchange, "ETH")
		diff = balance_after - balance_before
		diff_eur = diff * self.get_price(exchange, 'ETH', 'EUR')
		self.log("Différence: {:.6f} ETH = {:.6f} EUR".format(diff, diff_eur), mode="log")
		self.balance += diff
		self.log("Arbitrage {:5} on {:10}, diff: {:8.6f}ETH, balance: {:7.6f}ETH".format(asset, str(exchange), diff, self.balance))

	"""
		Logs text. Default mode will send a notification to Telegram, log mode will only write to logs.txt.
	"""
	def log(self, text, mode="notification"):
		formatted_text = "[{}] {}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), text)
		if (mode == "notification"):
			self.bot.sendMessage(chat_id=secrets.TELEGRAM_CHAT, text=formatted_text)
		if (mode == "notification" or mode == "log"):
			with open('logs.txt', 'a+') as file:
				file.write(formatted_text)
				file.write("\n")
