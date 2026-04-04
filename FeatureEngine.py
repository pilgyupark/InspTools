import cv2

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

