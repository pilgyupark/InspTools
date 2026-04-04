from tkinter import messagebox
from FeatureEngine import FeatureEngine
from LoFTREngine import LoFTREngine
from ImageHandler import ImageHandler
from PerspectiveProcessor import PerspectiveProcessor
from ROISelector import ROISelector
import tkinter as tk
import cv2
import numpy as np

class MainFrame:
    def __init__(self, root):
        self.root = root
        self.orb_engine = FeatureEngine()  # 기존 ORB 엔진
        self.loftr_engine = LoFTREngine()  # 새로운 LoFTR 엔진
        self.processor = PerspectiveProcessor()

        self.use_loftr = tk.BooleanVar(value=True) # LoFTR 사용 여부 체크박스용
        self.scene_img = None
        self.template_img = None # LoFTR은 이미지 자체가 필요함

        self._setup_ui()

    def register_roi(self):
        if self.scene_img is None: return
        roi_img = ROISelector.select_from_image(self.scene_img)
        if roi_img is not None:
            self.template_img = roi_img
            # ORB용 데이터도 미리 계산
            self.temp_kp, self.temp_des = self.orb_engine.detect_and_compute(roi_img)
            messagebox.showinfo("Success", "ROI 등록 완료 (LoFTR 모드 지원)")

    def run_match(self):
        if self.scene_img is None or self.template_img is None: return

        if self.use_loftr.get():
            # LoFTR 매칭 실행
            pts1, pts2 = self.loftr_engine.match(self.template_img, self.scene_img)
            if len(pts1) > 10:
                M, _ = cv2.findHomography(pts1, pts2, cv2.RANSAC, 5.0)
            else: M = None
        else:
            # 기존 ORB 매칭 실행
            scene_kp, scene_des = self.orb_engine.detect_and_compute(self.scene_img)
            matches = self.orb_engine.get_good_matches(self.temp_des, scene_des)
            M = self.processor.find_homography_points(self.temp_kp, scene_kp, matches)

        if M is not None:
            h, w = self.template_img.shape[:2]
            corners = self.processor.transform_corners(M, h, w)
            res_img = cv2.polylines(self.scene_img.copy(), [np.int32(corners)], True, (0, 255, 0), 5)
            self._update_display(res_img)
