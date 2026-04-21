import time
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from backend.utils.ocr import extract_text_from_image

# Create a synthetic image
width, height = 200, 50
image = Image.new('RGB', (width, height), color=(255, 255, 255))
draw = ImageDraw.Draw(image)
draw.text((10, 10), "Hello World", fill=(0, 0, 0))

# Convert to bytes
img_byte_arr = io.BytesIO()
image.save(img_byte_arr, format='PNG')
img_bytes = img_byte_arr.getvalue()

start_time = time.time()
extracted_text = extract_text_from_image(img_bytes)
elapsed_time = time.time() - start_time

print(f"Elapsed: {elapsed_time:.4f}s")
print(f"Length: {len(extracted_text)}")
print(f"Text: {extracted_text.strip()}")
