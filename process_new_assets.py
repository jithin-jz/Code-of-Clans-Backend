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

# New files list
files = [
    ("game_bush_green_bg_1768041027459.png", "bush.png"),
    ("game_mushrooms_green_bg_1768041044726.png", "mushrooms.png"),
    ("game_fence_green_bg_1768041060415.png", "fence.png"),
    ("game_town_hall_green_bg_1768041077243.png", "town-hall.png")
]

for src, dest in files:
    src_path = os.path.join(base_src, src)
    dest_path = os.path.join(base_dest, dest)
    remove_green_bg(src_path, dest_path)
