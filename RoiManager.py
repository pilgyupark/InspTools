import tkinter as tk
import cv2
import numpy as np

class RoiManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ROI Sync Example")
        
        # 초기 ROI [x, y, w, h]
        self.roi = [100, 100, 200, 200]
        self.dragging = False
        
        # 1. Tkinter UI 설정
        self.label = tk.Label(self.root, text="ROI (x, y, w, h):")
        self.label.pack()
        
        self.roi_var = tk.StringVar(value=str(self.roi))
        self.entry = tk.Entry(self.root, textvariable=self.roi_var, width=30)
        self.entry.pack(pady=5)
        
        # Entry에서 엔터 키를 누르면 OpenCV 창 업데이트
        self.entry.bind("<Return>", self.update_from_entry)
        
        # 2. 이미지 초기화 및 OpenCV 창 생성
        self.img = np.zeros((600, 800, 3), dtype=np.uint8)
        cv2.namedWindow("Image")
        cv2.setMouseCallback("Image", self.mouse_event)
        
        self.show_loop()

    def update_from_entry(self, event=None):
        """Entry 입력값을 ROI 변수에 반영"""
        try:
            # 문자열 [100, 100, 200, 200]을 리스트로 변환
            new_roi = eval(self.roi_var.get())
            if isinstance(new_roi, list) and len(new_roi) == 4:
                self.roi = new_roi
        except:
            self.roi_var.set(str(self.roi)) # 에러 시 이전 값으로 복구

    def mouse_event(self, event, x, y, flags, param):
        """OpenCV 마우스 조작 이벤트"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.dragging = True
            self.roi[0], self.roi[1] = x, y  # 시작점 설정
            
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.dragging:
                self.roi[2] = x - self.roi[0] # 너비 계산
                self.roi[3] = y - self.roi[1] # 높이 계산
                # 실시간으로 Entry 값 갱신
                self.roi_var.set(str(self.roi))
                
        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging = False
            # 음수 크기(역방향 드래그) 처리 등 정규화 가능

    def show_loop(self):
        """이미지 갱신 루프"""
        while True:
            display_img = self.img.copy()
            x, y, w, h = self.roi
            # ROI 사각형 그리기
            cv2.rectangle(display_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.imshow("Image", display_img)
            
            # Tkinter 업데이트
            self.root.update()
            
            # 'q' 누르면 종료
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cv2.destroyAllWindows()
        self.root.quit()

if __name__ == "__main__":
    RoiManager()
