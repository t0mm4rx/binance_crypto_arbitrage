daily_interest = 1
initial_balance = 100
number_of_days = 1000

for _ in range(number_of_days):
	initial_balance *= (1 + daily_interest / 100)

print(initial_balance)