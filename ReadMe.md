# Crypto currency arbitrage

**⚠️ This script is directly connected to your wallets. So if you use it keep it mind it's dealing with real money.**

## 🎯 What's the goal of this project
The goal of this project is to play with crypto currencies and make profit from triangular arbitrage. We want to create a Python arbitrage bot.

This script is listening to crypto market and is waiting for arbitrage opportunity. If it founds one, it automatically does the transaction. It also sends a message to a Telegram chat when it completes a transaction.

## 📈 What's triangular arbitrage
Triangular arbitrage is a way of making money on a market without predicting the future.

To understand what's traditional arbitrage is, imagine Alice selling Bitcoin 1000 dollars while Bob is buying Bitcoin 1100 dollars.

If you buy a Bitcoin to Alice and you sell it instantly to Bob, you have an instant profit of 100 dollars. You can use this method to make profit from different crypto exchanges, but it has severe constraints: every exchanges need to be running at same time, you need to pay fees on each transaction, you need to sync your wallets...

An other method to do arbitrage is called "Triangular arbitrage". This method can be used on a single platform.

To understang triangular arbitrage, imagine:

- Alice is selling a Bitcoin 1000 dollars
- Bob is exchanging 1 Bitcoin for 100 Litecoin
- Carlos is exchanging 1 Litecoin for 11 dollars.

We can buy 1 BTC for 1000 USD, then exchange our 1 BTC for 100 LTC, then our 100 LTC for 1100 USD. We won 100 USD during the transaction.

This bot uses ETH as base wallet, and BTC as exchange currency. So we have two types of arbitrage:

Forward: ETH -> ALT -> BTC -> ETH

and

Backward: ETH -> BTC -> ALT -> ETH

## 🔗 Dependencies

- ccxt
- python-telegram-bot

## 💱 Current exchanges

- Binance
- Bittrex

## 🤖 How to use

First, install all dependencies.

Create a Telegram bot using [this tutorial](https://medium.com/@mycodingblog/get-telegram-notification-when-python-script-finishes-running-a54f12822cdc).

Create API secrets for all exchanges.

Create a secrets.py file with your values:

```python
BINANCE_KEY="XXX"
BINANCE_SECRET="XXX"
BITTREX_KEY="XXX"
BITTREX_SECRET="XXX"
TELEGRAM="XXX:XXX"
TELEGRAM_CHAT="XXX"
```

Then run run.py file with Python 3.

You can use the Crypto class to do your own bot or operations:

```python
import crypto from Crypto
import currencies

# Create instance, connects to your exchange accounts
crypto = Crypto()

# Logs in Telegram and logs.txt
crypto.log("Hello world")

# Get your ETH balance on Binance
crypto.get_balance(crypto.binance, "ETH")

# Get the ETH/BTC bid price on Bittrex
crypto.get_price(crypto.bittrex, "ETH", "BTC", mode="bid")
# Get the LTC/BTC price on Bittrex
crypto.get_price(crypto.bittrex, "LTC", "BTC")
# Get the BTC/USDT ask price on Bittrex
crypto.get_price(crypto.bittrex, "ETH", "USDT", mode="ask")

# Estimate triangular arbitrage profit (in %) for given asset and exchange
crypto.estimate_arbitrage_forward(crypto.bittrex, "ZIL")
crypto.estimate_arbitrage_backward(crypto.bittrex, "ZIL")

# Create market buy/sell orders

# Buy 0.3 ETH with BTC at market price
crypto.buy(crypto.binance, "ETH", "BTC", amount=0.3)
# Buy ZIL with 30% of available ETH at market price
crypto.buy(crypto.binance, "ZIL", "ETH", amount_percentage=0.3)
# SELL 10 ZIL for BTC at market price
crypto.sell(crypto.binance, "ZIL", "BTC", amount=10)
# SELL 100% of available ZIL for BTC at market price
crypto.sell(crypto.binance, "ZIL", "BTC", amount_percentage=1)

# Create limit buy/sell orders

# Will buy ETH with BTC at 0.053 or better
crypto.buy(crypto.binance, "ETH", "BTC", amount=0.3, limit=0.053)
# Will sell ETH with BTC at 0.054 or better, if the order is not fullfilled after 3 seconds, we close the order
crypto.sell(crypto.binance, "ETH", "BTC", amount=0.3, limit=0.054, timeout=3)

# Get order book
crypto.get_order_book(crypto.bitfinex, 'ETH', 'BTC', mode='asks')

# Get compatible alt coins
print(currencies.binance_alternatives)
print(currencies.bittrex_alternatives)
```

API calls to get_price and get_order_book are cached, if you want to fetch refreshed data:
```python
# Clear cache
crypto.flush_cache()
```

## ❤️ Want to participate ?

If you need help setting up the bot on your side, or if you have any suggestions, DM me on Twitter [@AirM4rx](https://twitter.com/AirM4rx).

You can also make pull requests.

If you want to thank me: BTC: 3Dh7gEbDKbR6n3VAB1eK16eQgRGBJGU6vD
