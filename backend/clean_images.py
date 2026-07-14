import os
import shutil

image_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'exam_images')

keep_dirs = {'2026_河北卷_生物', '2026_陕晋青宁卷_生物'}

for item in os.listdir(image_dir):
    item_path = os.path.join(image_dir, item)
    if os.path.isdir(item_path) and item not in keep_dirs:
        shutil.rmtree(item_path)
        print(f'删除: {item}')

print('完成')