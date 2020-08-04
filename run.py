from crypto import Crypto
import currencies
import sys
import threading

def process_asset(crypto, alt):
	delta_forward = crypto.estimate_arbitrage_forward(alt)
	delta_backward = crypto.estimate_arbitrage_backward(alt)
	print("{:5}: {:8.4f}% / {:8.4f}%".format(alt, delta_forward, delta_backward))
	if (delta_forward > 0):
		crypto.log("Found opportunity for {:5} @{:.4f}".format(alt, delta_forward))
		crypto.run_arbitrage_forward(alt)
	elif (delta_backward > 0):
		crypto.log("Found opportunity for {:5} @{:.4f}".format(alt, delta_backward))
		crypto.run_arbitrage_backward(alt)

def run(crypto, thread_number):
	while True:
		for i in range(0, len(currencies.alternatives), thread_number):
			to_process = currencies.alternatives[i:i+thread_number]
			threads = []
			for currency in to_process:
				t = threading.Thread(target=process_asset, args=(crypto, currency))
				t.start()
				threads.append(t)
			for t in threads:
				t.join()

if (__name__ == "__main__"):
	crypto = Crypto()
	crypto.log("Starting to listen the markets")
	thread_number = 4
	run(crypto, 4)
