from FeatureEngine import FeatureEngine
from ImageHandler import ImageHandler
from PerspectiveProcessor import PerspectiveProcessor
from ROISelector import ROISelector
import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np

class MainFrame:
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
