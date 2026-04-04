import torch
import kornia.feature as KF
import cv2
import numpy as np

class LoFTREngine:
    def __init__(self):
            # LoFTR 모델 로드 (실외/실내 모델 중 선택 가능)
                    self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                            self.matcher = KF.LoFTR(pretrained='outdoor').to(self.device)
                                    self.matcher.eval()

                                        def match(self, img1, img2):
                                                """두 이미지 사이의 대응점(Correspondences)을 직접 찾아 반환합니다."""
                                                        # 1. 전처리 (Tensor 변환 및 GrayScale)
                                                                t1 = self._preprocess(img1)
                                                                        t2 = self._preprocess(img2)

                                                                                with torch.no_grad():
                                                                                            input_dict = {"image0": t1, "image1": t2}
                                                                                                        correspondences = self.matcher(input_dict)

                                                                                                                # 2. 결과 추출
                                                                                                                        mkpts0 = correspondences['keypoints0'].cpu().numpy()
                                                                                                                                mkpts1 = correspondences['keypoints1'].cpu().numpy()
                                                                                                                                        mconf = correspondences['confidence'].cpu().numpy()

                                                                                                                                                # 신뢰도가 높은 매칭점만 필터링 (0.8 이상 추천)
                                                                                                                                                        valid = mconf > 0.8
                                                                                                                                                                return mkpts0[valid], mkpts1[valid]

                                                                                                                                                                    def _preprocess(self, img):
                                                                                                                                                                            if len(img.shape) == 3:
                                                                                                                                                                                        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                                                                                                                                                                                                img_tensor = torch.from_numpy(img).float()[None, None] / 255.0
                                                                                                                                                                                                        return img_tensor.to(self.device)


class VisionApp:
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
                                                                                                                                                                                                                                                                                                                                    