from PIL import Image

img = Image.open(r"..\demo_data\sample1.jpeg")

print("FORMAT:")
print(img.format)

print("\nEXIF:")
print(img.getexif())

print("\nINFO:")
print(img.info)