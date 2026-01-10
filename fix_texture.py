from PIL import Image
import os

def crop_borders(image_path, output_path, crop_pixels):
    try:
        img = Image.open(image_path)
        width, height = img.size
        print(f"Original size: {width}x{height}")
        
        # Crop
        left = crop_pixels
        top = crop_pixels
        right = width - crop_pixels
        bottom = height - crop_pixels
        
        cropped_img = img.crop((left, top, right, bottom))
        print(f"New size: {cropped_img.size}")
        
        cropped_img.save(output_path)
        print(f"Saved cropped image to {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    input_path = "c:/Users/Jithi/Desktop/coc/frontend/public/assets/clean-turf.png"
    output_path = "c:/Users/Jithi/Desktop/coc/frontend/public/assets/clean-turf-fixed.png"
    # It looks like a significant border in the screenshot, maybe 4-8%?
    # Let's try inspecting or just cropping a safe amount.
    # If the image is 1024x1024, a 20px crop might be enough.
    # Let's assume the borders are noise.
    crop_pixels = 30 # Aggressive crop to remove frame
    crop_borders(input_path, output_path, crop_pixels)
