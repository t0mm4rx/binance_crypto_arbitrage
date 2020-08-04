import ccxt
import secrets
from datetime import datetime
import telegram

class Crypto:

	binance = None
	balance = 0
	bot = None

	def __init__(self):
		self.init_ccxt()
		self.bot = telegram.Bot(token=secrets.TELEGRAM)

	def init_ccxt(self):
		self.binance = ccxt.binance({
			'apiKey': secrets.KEY,
		    'secret': secrets.SECRET,
			'timeout': 30000,
		    'enableRateLimit': True,
		})

	"""
		Get your binance balance for given asset.
	"""
	def get_balance(self, asset):
		balance = self.binance.fetchBalance()['info']['balances']
		for a in balance:
			if (a['asset'] == asset):
				return float(a['free'])

	"""
		Get an asset price, mode can be average, bid or ask.
	"""
	def get_price(self, asset1, asset2, mode='average'):
		ticker = self.binance.fetchTicker('{}/{}'.format(asset1, asset2))
		if (mode == 'bid'):
			return ticker['bid']
		if (mode == 'ask'):
			return ticker['ask']
		return (ticker['ask'] + ticker['bid']) / 2

	"""
		Estimate the profit from backward arbitrage on given asset.
	"""
	def estimate_arbitrage_forward(self, asset):
		step1 = (1 / self.get_price(asset, 'ETH', mode='ask')) * 0.999
		step2 = (step1 * self.get_price(asset, 'BTC', mode='bid')) * 0.999
		step3 = (step2 / self.get_price('ETH', 'BTC', mode='ask')) * 0.999
		return (step3 - 1) * 100

	"""
		Estimate the profit from backward arbitrage on given asset.
	"""
	def estimate_arbitrage_backward(self, asset):
		step1 = (self.get_price('ETH', 'BTC', mode='bid')) * 0.999
		step2 = (step1 / self.get_price(asset, 'BTC', mode='ask')) * 0.999
		step3 = (step2 * self.get_price(asset, 'ETH', mode='bid')) * 0.999
		return (step3 - 1) * 100

	"""
		Create a market buy order. You can specify either to buy a fixed amount
		of the given asset, or a percentage of all your balance.
	"""
	def buy(self, asset1, asset2, amount_percentage=None, amount=None):
		if (amount_percentage):
			asset2_available = self.get_balance(asset2) * amount_percentage
			amount = asset2_available / self.get_price(asset1, asset2, mode='ask')
			print("Buying {:.6} {} with {:.2f}% ({:.8f}) of {} available.".format(
				amount,
				asset1,
				amount_percentage * 100,
				asset2_available,
				asset2
			))
			self.binance.createMarketBuyOrder(
				'{}/{}'.format(asset1, asset2),
				amount
			)
		elif (amount):
			print("Buying {:.6f} {} with {}.".format(
				amount,
				asset1,
				asset2
			))
			self.binance.createMarketBuyOrder(
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
	def sell(self, asset1, asset2, amount_percentage=None, amount=None):
		if (amount_percentage):
			amount = self.get_balance(asset1) * amount_percentage
			print("Selling {:.2f}% ({:.6f}) of {} to {}.".format(
				amount_percentage * 100,
				amount,
				asset1,
				asset2
			))
			self.binance.createMarketSellOrder(
				'{}/{}'.format(asset1, asset2),
				amount
			)
		elif (amount):
			print("Selling {} {} to {}.".format(
				amount,
				asset1,
				asset2
			))
			self.binance.createMarketSellOrder(
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
	def run_arbitrage_forward(self, asset):
		print("Arbitrage: ETH -> {} -> BTC -> ETH".format(asset))
		balance_before = self.get_balance("ETH")
		self.buy(asset, "ETH", amount_percentage=0.8)
		self.sell(asset, "BTC", amount_percentage=1)
		self.buy("ETH", "BTC", amount_percentage=1)
		balance_after = self.get_balance("ETH")
		diff = balance_after - balance_before
		diff_eur = diff * self.get_price('ETH', 'EUR')
		print("Différence: {:.6f} ETH = {:.6f} EUR".format(diff, diff_eur))
		self.balance += diff
		self.log("Arbitrage {:5}, diff: {:8.6f}ETH, balance: {:7.6f}ETH".format(asset, diff, self.balance))

	"""
		Executes backward arbitrage on given asset:
		ETH -> BTC -> ALT -> ETH.
	"""
	def run_arbitrage_backward(self, asset):
		print("Arbitrage: ETH -> BTC -> {} -> ETH".format(asset))
		balance_before = self.get_balance("ETH")
		self.sell("ETH", "BTC", amount_percentage=0.8)
		self.buy(asset, "BTC", amount_percentage=1)
		self.sell(asset, "ETH", amount_percentage=1)
		balance_after = self.get_balance("ETH")
		diff = balance_after - balance_before
		diff_eur = diff * self.get_price('ETH', 'EUR')
		print("Différence: {:.6f} ETH = {:.6f} EUR".format(diff, diff_eur))
		self.balance += diff
		self.log("Arbitrage {:5}, diff: {:8.6f}ETH, balance: {:7.6f}ETH".format(asset, diff, self.balance))

	"""
		Logs in logs.txt file and in Telegram chat.
	"""
	def log(self, text):
		formatted_text = "[{}] {}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), text)
		self.bot.sendMessage(chat_id=secrets.TELEGRAM_CHAT, text=formatted_text)
		with open('logs.txt', 'a+') as file:
			file.write(formatted_text)
			file.write("\n")
