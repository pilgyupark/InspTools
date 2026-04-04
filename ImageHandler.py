import cv2
from PIL import Image, ImageTk

class ImageHandler:
    @staticmethod
    def load_image(path):
        return cv2.imread(path)

    @staticmethod
    def to_tk_image(cv_img, target_size=(800, 600)):
        """OpenCV 이미지를 Tkinter용 이미지로 변환 및 리사이즈"""
        img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w = img_rgb.shape[:2]
        ratio = min(target_size[0]/w, target_size[1]/h)
        new_size = (int(w * ratio), int(h * ratio))
        img_res = cv2.resize(img_rgb, new_size)
        return ImageTk.PhotoImage(Image.fromarray(img_res))
    