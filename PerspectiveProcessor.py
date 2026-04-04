import cv2
import numpy as np

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
