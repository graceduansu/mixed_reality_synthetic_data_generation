from PIL import Image


def overlay(bg_img_path, overlay_img_path, dest_img_path):

    # Opening the primary image (used in background)
    bg_img = Image.open(bg_img_path)
    
    # Opening the secondary image (overlay image)
    overlay_img = Image.open(overlay_img_path)
    
    # Pasting overlay image on top of background img 
    # starting at coordinates (0, 0)
    overlay_img = overlay_img.resize(bg_img.size[:2])
    bg_img.paste(overlay_img, (0,0), mask = overlay_img, )
    
    bg_img.save(dest_img_path)