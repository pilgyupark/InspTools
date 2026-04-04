import cv2
import numpy as np
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
                
class FeatureEngine:
        def __init__(self):
                self.orb = cv2.ORB_create(nfeatures=2500)
                        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

                            def detect_and_compute(self, image):
                                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
                                            return self.orb.detectAndCompute(gray, None)

                                                def get_good_matches(self, des1, des2, limit=50):
                                                        if des1 is None or des2 is None: return []
                                                                matches = self.bf.match(des1, des2)
                                                                        return sorted(matches, key=lambda x: x.distance)[:limit]


class PerspectiveProcessor:
        @staticmethod
            def find_homography_points(kp1, kp2, matches):
                    src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
                            dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
                                    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                                            return M

                                                @staticmethod
                                                    def transform_corners(M, template_h, template_w):
                                                            pts = np.float32([[0, 0], [0, template_h-1], [template_w-1, template_h-1], [template_w-1, 0]]).reshape(-1, 1, 2)
                                                                    return cv2.perspectiveTransform(pts, M)

class ROISelector:
        @staticmethod
            def select_from_image(image):
                    window_name = "Drag to Select ROI (Enter: Confirm, C: Cancel)"
                            # cv2.selectROI는 내부적으로 마우스 이벤트를 처리함
                                    roi = cv2.selectROI(window_name, image, fromCenter=False, showCrosshair=True)
                                            cv2.destroyWindow(window_name)
                                                    
                                                            x, y, w, h = roi
                                                                    if w > 0 and h > 0:
                                                                                return image[y:y+h, x:x+w]
                                                                                        return None

import tkinter as tk
from tkinter import filedialog, messagebox

class VisionApp:
    def __init__(self, root):
            self.root = root
                    self.engine = FeatureEngine()
                            self.processor = PerspectiveProcessor()
                                    
                                            self.scene_img = None
                                                    self.temp_kp, self.temp_des, self.temp_shape = None, None, None
                                                            
                                                                    self._setup_ui()

                                                                        def _setup_ui(self):
                                                                                self.root.title("Advanced ROI Template Matcher")
                                                                                        btn_bar = tk.Frame(self.root)
                                                                                                btn_bar.pack(pady=10)

                                                                                                        tk.Button(btn_bar, text="1. 이미지 로드", command=self.load_scene).pack(side=tk.LEFT, padx=5)
                                                                                                                tk.Button(btn_bar, text="2. ROI 등록", command=self.register_roi).pack(side=tk.LEFT, padx=5)
                                                                                                                        tk.Button(btn_bar, text="3. 매칭 실행", command=self.run_match).pack(side=tk.LEFT, padx=5)

                                                                                                                                self.canvas = tk.Canvas(self.root, width=800, height=600, bg="gray")
                                                                                                                                        self.canvas.pack()

                                                                                                                                            def load_scene(self):
                                                                                                                                                    path = filedialog.askopenfilename()
                                                                                                                                                            if path:
                                                                                                                                                                        self.scene_img = ImageHandler.load_image(path)
                                                                                                                                                                                    self._update_display(self.scene_img)

                                                                                                                                                                                        def register_roi(self):
                                                                                                                                                                                                if self.scene_img is None: return
                                                                                                                                                                                                        roi_img = ROISelector.select_from_image(self.scene_img)
                                                                                                                                                                                                                if roi_img is not None:
                                                                                                                                                                                                                            self.temp_shape = roi_img.shape[:2]
                                                                                                                                                                                                                                        self.temp_kp, self.temp_des = self.engine.detect_and_compute(roi_img)
                                                                                                                                                                                                                                                    messagebox.showinfo("Success", "ROI가 템플릿으로 등록되었습니다.")

                                                                                                                                                                                                                                                        def run_match(self):
                                                                                                                                                                                                                                                                if self.temp_des is None or self.scene_img is None: return
                                                                                                                                                                                                                                                                        
                                                                                                                                                                                                                                                                                scene_kp, scene_des = self.engine.detect_and_compute(self.scene_img)
                                                                                                                                                                                                                                                                                        matches = self.engine.get_good_matches(self.temp_des, scene_des)
                                                                                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                                                                        if len(matches) > 10:
                                                                                                                                                                                                                                                                                                                    M = self.processor.find_homography_points(self.temp_kp, scene_kp, matches)
                                                                                                                                                                                                                                                                                                                                if M is not None:
                                                                                                                                                                                                                                                                                                                                                corners = self.processor.transform_corners(M, *self.temp_shape)
                                                                                                                                                                                                                                                                                                                                                                res_img = cv2.polylines(self.scene_img.copy(), [np.int32(corners)], True, (0,255,0), 5)
                                                                                                                                                                                                                                                                                                                                                                                self._update_display(res_img)

                                                                                                                                                                                                                                                                                                                                                                                    def _update_display(self, img):
                                                                                                                                                                                                                                                                                                                                                                                            self.tk_img = ImageHandler.to_tk_image(img)
                                                                                                                                                                                                                                                                                                                                                                                                    self.canvas.create_image(400, 300, image=self.tk_img)

                                                                                                                                                                                                                                                                                                                                                                                                    if __name__ == "__main__":
                                                                                                                                                                                                                                                                                                                                                                                                        root = tk.Tk()
                                                                                                                                                                                                                                                                                                                                                                                                            app = VisionApp(root)
                                                                                                                                                                                                                                                                                                                                                                                                                root.mainloop()
                                                                                                                                                                                                                                                                                                                                                                                                        