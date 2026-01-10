from PIL import Image
import os

def remove_green_bg(input_path, output_path):
    try:
        img = Image.open(input_path).convert("RGBA")
        datas = img.getdata()

        newData = []
        # Green screen range
        for item in datas:
            # Check if pixel is predominantly green
            # (r, g, b, a)
            # Standard green screen is (0, 255, 0)
            # We use a threshold. If Green is high and Red/Blue are low.
            if item[1] > 200 and item[0] < 100 and item[2] < 100:
                newData.append((255, 255, 255, 0)) # Transparent
            else:
                newData.append(item)

        img.putdata(newData)
        img.save(output_path, "PNG")
        print(f"Processed: {output_path}")
    except Exception as e:
        print(f"Error processing {input_path}: {e}")

# Paths
base_src = r"C:\Users\Jithi\.gemini\antigravity\brain\f825bff9-1bd7-4742-b0ec-cec7c37cb2df"
base_dest = r"c:\Users\Jithi\Desktop\coc\frontend\public\assets"

files = [
    ("pine_tree_green_bg_1768040841384.png", "pine-tree.png"),
    ("oak_tree_green_bg_1768040860559.png", "oak-tree.png"),
    ("rock_large_green_bg_1768040875447.png", "rock-large.png"),
    ("treasure_chest_green_bg_1768040892181.png", "treasure-chest.png")
]

for src, dest in files:
    src_path = os.path.join(base_src, src)
    dest_path = os.path.join(base_dest, dest)
    remove_green_bg(src_path, dest_path)
