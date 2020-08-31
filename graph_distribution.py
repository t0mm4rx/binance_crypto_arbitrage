import matplotlib.pyplot as plt

lines = []
values = []

def process_percentage(n):
	n = n.replace('%', '')
	n = n.replace('\n', '')
	n = float(n)
	return n

with open('logs.txt', 'r') as file:
	lines = file.readlines()

for line in lines:
	split1 = line.split(':')
	if (len(split1) == 4):
		split2 = split1[3].split('/')
		if (len(split2) == 2):
			try:
				values.append(process_percentage(split2[0]))
				values.append(process_percentage(split2[1]))
			except:
				pass

plt.hist(values, range=[-1, 0], bins=40)
plt.show()
plt.savefig('distrib.png')
