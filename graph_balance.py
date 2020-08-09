import matplotlib.pyplot as plt
import os

if (not os.path.isfile("balance.csv")):
	print("No balance.csv record.")
	exit()

with open("balance.csv", "r") as file:
	lines = file.readlines()[1:]
	values = []
	for line in lines:
		values.append(float(line.split(',')[1][:-1]))

plt.plot(values)
plt.savefig('balance.png')
plt.show()
