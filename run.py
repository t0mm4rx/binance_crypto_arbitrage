from crypto import Crypto

alts = [
	"ZIL",
	"VIB",
	"RLC",
	"LINK",
	"NEBL",
	"BRD",
	"LTC",
	"IOTA",
	"BQX",
	"QSP",
	"PIVX",
	"XZC",
	"MTL",
	"XEM",
	"AE",
	"EVX",
	"STEEM",
	"ONT",
	"VIB",
	"BNT",
	"VET",
	"ADX",
	"QKC",
	"CDT",
	"BNB",
	"THETA",
	"ZEC",
	"DASH",
	"QLC"
]

def run():
	global crypto
	crypto.log("Starting to listen the markets")
	while True:
		for alt in alts:
			delta_forward = crypto.estimate_arbitrage_forward(alt)
			delta_backward = crypto.estimate_arbitrage_backward(alt)
			print("{:5}: {:8.4f}% / {:8.4f}%".format(alt, delta_forward, delta_backward))
			if (delta_forward > 0):
				crypto.log("Found opportunity for {:5} @{:.4f}".format(alt, delta_forward))
				crypto.run_arbitrage_forward(alt)
			elif (delta_backward > 0):
				crypto.log("Found opportunity for {:5} @{:.4f}".format(alt, delta_backward))
				crypto.run_arbitrage_backward(alt)

if (__name__ == "__main__"):
	global crypto
	crypto = Crypto()
	try:
		run()
	except:
		crypto.log("Script stopped")
