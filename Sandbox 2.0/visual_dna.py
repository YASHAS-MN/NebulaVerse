import numpy as np
from PIL import Image
import math
import sys
import os

def binary_to_image(file_path):
    # Read binary data
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # Calculate image size (sqrt of file size for a square)
    size = int(math.sqrt(len(data))) + 1
    
    # Pad data with zeros to fit the square
    padded_data = data + b'\x00' * (size**2 - len(data))
    
    # Convert to 2D numpy array (grayscale)
    img_array = np.frombuffer(padded_data, dtype=np.uint8).reshape((size, size))
    
    # Save as PNG
    img = Image.fromarray(img_array)
    output_name = f"{os.path.basename(file_path)}_dna.png"
    img.save(output_name)
    return output_name, size

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 visual_dna.py <file>")
    else:
        name, size = binary_to_image(sys.argv[1])
        print(f"Visual DNA generated: {name} ({size}x{size} pixels)")
