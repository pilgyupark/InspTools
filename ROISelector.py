import cv2

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