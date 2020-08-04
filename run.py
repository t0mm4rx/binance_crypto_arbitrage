from crypto import Crypto
import currencies
import threading
import sys

"""
	Check if an asset makes profit, if yes we execute the arbitrage
"""
def process_asset(crypto, exchange, alt):
	delta_forward = crypto.estimate_arbitrage_forward(exchange, alt)
	delta_backward = crypto.estimate_arbitrage_backward(exchange, alt)
	print("{:10} / {:5}: {:8.4f}% / {:8.4f}%".format(str(exchange), alt, delta_forward, delta_backward))
	if (delta_forward > 0):
		crypto.log("Found opportunity for {:5} @{:.4f}".format(alt, delta_forward))
		crypto.run_arbitrage_forward(exchange, alt)
	elif (delta_backward > 0):
		crypto.log("Found opportunity for {:5} @{:.4f}".format(alt, delta_backward))
		crypto.run_arbitrage_backward(exchange, alt)

"""
	Loop over currencies.
"""
def run(crypto, exchange, thread_number):
	alts = None
	if (str(exchange) == "Binance"):
		alts = currencies.binance_alternatives
	elif (str(exchange) == "Bittrex"):
		alts = currencies.bittrex_alternatives
	while True:
		for i in range(0, len(alts), thread_number):
			alts_batch = alts[i:i+thread_number]
			threads = []
			for asset in alts_batch:
				threads.append(threading.Thread(target=process_asset, args=(crypto, exchange, asset)))
				threads[-1].start()
			for thread in threads:
				thread.join()

"""
	Main
"""
if (__name__ == "__main__"):
	if (len(sys.argv) != 2):
		print("python3 run.py <exchange>")
		exit()
	exchange_str = sys.argv[1]
	exchanges = ["binance", "bittrex"]
	if (not exchange_str in exchanges):
		print("{} is not a valid exchange. Options:".format(exchange_str))
		for exchange in exchanges:
			print("- {}".format(exchange))
		exit()
	crypto = Crypto()
	exchange = None
	if (exchange_str == "binance"):
		exchange = crypto.binance
	if (exchange_str == "bittrex"):
		exchange = crypto.bittrex
	crypto.log("Starting to listen the {} markets".format(exchange_str))
	thread_number = 2
	run(crypto, exchange, thread_number)