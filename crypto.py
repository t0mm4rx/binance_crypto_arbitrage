import ccxt
import secrets
from datetime import datetime
import telegram

class Crypto:

	binance = None
	bittrex = None
	balance = 0
	bot = None

	def __init__(self):
		self.init_ccxt()
		self.bot = telegram.Bot(token=secrets.TELEGRAM)

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
		balance = exchange.fetchBalance()
		if (asset in balance):
			return balance[asset]['free']
		return 0

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
		ticker = exchange.fetchTicker('{}/{}'.format(asset1, asset2))
		if (mode == 'bid'):
			return ticker['bid']
		if (mode == 'ask'):
			return ticker['ask']
		return (ticker['ask'] + ticker['bid']) / 2

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
		Create a market buy order. You can specify either to buy a fixed amount
		of the given asset, or a percentage of all your balance.
	"""
	def buy(self, exchange, asset1, asset2, amount_percentage=None, amount=None):
		if (amount_percentage):
			asset2_available = self.get_balance(exchange, asset2) * amount_percentage
			amount = asset2_available / self.get_price(exchange, asset1, asset2, mode='ask')
			print("Buying {:.6} {} with {:.2f}% ({:.8f}) of {} available on {}.".format(
				amount,
				asset1,
				amount_percentage * 100,
				asset2_available,
				asset2,
				exchange
			))
			exchange.createMarketBuyOrder(
				'{}/{}'.format(asset1, asset2),
				amount
			)
		elif (amount):
			print("Buying {:.6f} {} with {} on {}.".format(
				amount,
				asset1,
				asset2,
				exchange
			))
			exchange.createMarketBuyOrder(
				'{}/{}'.format(asset1, asset2),
				amount
			)
		else:
			print("Amount should be given, not buying!")
			return

	"""
		Create a market sell order. You can specify either to sell a fixed amount
		of the given asset, or a percentage of all your balance.
	"""
	def sell(self, exchange, asset1, asset2, amount_percentage=None, amount=None):
		if (amount_percentage):
			amount = self.get_balance(exchange, asset1) * amount_percentage
			print("Selling {:.2f}% ({:.6f}) of {} to {} on {}.".format(
				amount_percentage * 100,
				amount,
				asset1,
				asset2,
				exchange
			))
			exchange.createMarketSellOrder(
				'{}/{}'.format(asset1, asset2),
				amount
			)
		elif (amount):
			print("Selling {} {} to {} on {}.".format(
				amount,
				asset1,
				asset2,
				exchange
			))
			exchange.createMarketSellOrder(
				'{}/{}'.format(asset1, asset2),
				amount
			)
		else:
			print("Amount should be given, not selling!")
			return

	"""
		Executes forward arbitrage on given asset:
		ETH -> ALT -> BTC -> ETH
	"""
	def run_arbitrage_forward(self, exchange, asset):
		print("Arbitrage on {}: ETH -> {} -> BTC -> ETH".format(exchange, asset))
		balance_before = self.get_balance(exchange, "ETH")
		self.buy(exchange, asset, "ETH", amount_percentage=0.8)
		self.sell(exchange, asset, "BTC", amount_percentage=1)
		self.buy(exchange, "ETH", "BTC", amount_percentage=1)
		balance_after = self.get_balance(exchange, "ETH")
		diff = balance_after - balance_before
		diff_eur = diff * self.get_price(exchange, 'ETH', 'EUR')
		print("Différence: {:.6f} ETH = {:.6f} EUR".format(diff, diff_eur))
		self.balance += diff
		self.log("Arbitrage {:5} on {:10}, diff: {:8.6f}ETH, balance: {:7.6f}ETH".format(asset, str(exchange), diff, self.balance))

	"""
		Executes backward arbitrage on given asset:
		ETH -> BTC -> ALT -> ETH.
	"""
	def run_arbitrage_backward(self, exchange, asset):
		print("Arbitrage on {}: ETH -> BTC -> {} -> ETH".format(exchange, asset))
		balance_before = self.get_balance(exchange, "ETH")
		self.sell(exchange, "ETH", "BTC", amount_percentage=0.8)
		self.buy(exchange, asset, "BTC", amount_percentage=1)
		self.sell(exchange, asset, "ETH", amount_percentage=1)
		balance_after = self.get_balance(exchange, "ETH")
		diff = balance_after - balance_before
		diff_eur = diff * self.get_price(exchange, 'ETH', 'EUR')
		print("Différence: {:.6f} ETH = {:.6f} EUR".format(diff, diff_eur))
		self.balance += diff
		self.log("Arbitrage {:5} on {:10}, diff: {:8.6f}ETH, balance: {:7.6f}ETH".format(asset, exchange, diff, self.balance))

	"""
		Logs in logs.txt file and in Telegram chat.
	"""
	def log(self, text):
		formatted_text = "[{}] {}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), text)
		self.bot.sendMessage(chat_id=secrets.TELEGRAM_CHAT, text=formatted_text)
		with open('logs.txt', 'a+') as file:
			file.write(formatted_text)
			file.write("\n")
