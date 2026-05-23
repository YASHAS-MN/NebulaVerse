import math
import sys

def calculate_entropy(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    if not data: return 0
    entropy = 0
    for x in range(256):
        p_x = data.count(x) / len(data)
        if p_x > 0:
            entropy += - p_x * math.log(p_x, 2)
    return entropy

if __name__ == "__main__":
    file = sys.argv[1]
    print(f"Entropy Score for {file}: {calculate_entropy(file):.4f}")
