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