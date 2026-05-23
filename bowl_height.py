import cv2
import numpy as np
import math
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
from skimage.measure import EllipseModel, ransac

# =========================================================================
# 1. 원호 복원 알고리즘 함수부 (이전 검증된 로직 유지)
# =========================================================================

def extract_arc_points_old(roi_img, thresh_low=50, thresh_high=150):
    if roi_img is None or roi_img.size == 0:
        return None
    gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, thresh_low, thresh_high)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    
    if not contours:
        return None
    
    best_contour = max(contours, key=len)
    points = best_contour.reshape(-1, 2).astype(np.float64)
    return points

def extract_arc_points(roi_img, thresh_low=50, thresh_high=150, min_contour_len=30):
    """
    [전천후 개선 버전] 
    ROI 내에서 발생하는 모든 에지 파편(좌/우/위/아래/대각선 짤림 무관)을 
    길이 기반으로 필터링한 후, 하나의 거대한 점집합으로 통합하여 반환합니다.
    """
    if roi_img is None or roi_img.size == 0:
        return None
        
    # 1. 전처리 (그레이스케일, 가우시안 블러, Canny 에지)
    gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, thresh_low, thresh_high)
    
    # 2. 모든 윤곽선 파편(조각) 추출
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    
    if not contours:
        return None
        
    valid_points_list = []
    
    # 3. 각 에지 조각들을 순회하며 유효한 곡선 성분만 수집
    for cnt in contours:
        # 노이즈 필터링: 너무 짧은 에지 조각(먼지, 글자, 질감 노이즈)은 버림
        if len(cnt) >= min_contour_len:
            # (N, 1, 2) 구조를 (N, 2) float64 배열로 변환하여 리스트에 축적
            pts = cnt.reshape(-1, 2).astype(np.float64)
            valid_points_list.append(pts)
            
    # 유효한 에지 조각이 하나도 없는 경우 세이프가드
    if not valid_points_list:
        return None
        
    # 4. [핵심] 수집된 모든 파편 점들을 하나의 대형 배열로 수직 병합 (Vstack)
    # 이제 좌우가 잘렸든 위아래가 잘렸든 상관없이 모든 유효 곡선 좌표가 하나로 통합됩니다.
    merged_points = np.vstack(valid_points_list)
    return merged_points

def fit_ellipse_ransac(points, min_samples=10, residual_threshold=1.5, max_trials=100):
    if points is None or len(points) < min_samples:
        return None
    try:
        model_robust, inliers = ransac(
            points, 
            EllipseModel, 
            min_samples=int(min_samples),
            residual_threshold=float(residual_threshold), 
            max_trials=int(max_trials)
        )
        if model_robust is None:
            return None
        
        cy, cx, b, a, theta = model_robust.params
        return {
            "center": (cx, cy),
            "major_axis": b * 2,
            "minor_axis": a * 2,
            "angle": math.degrees(theta),
            "inliers": inliers
        }
    except Exception:
        return None

def judge_height_defect(current_center, master_center, distance_threshold=5.0):
    cx_cur, cy_cur = current_center
    cx_mas, cy_mas = master_center
    distance_error = math.sqrt((cx_cur - cx_mas)**2 + (cy_cur - cy_mas)**2)
    status = "OK" if distance_error <= distance_threshold else "NG"
    return status, distance_error

# =========================================================================
# 2. Tkinter GUI 애플리케이션 클래스 부
# =========================================================================

class BowlInspectorGUI:
    def __init__(self, window):
        self.window = window
        self.window.title("Bowl Cover 원호 복원 파라미터 튜닝 툴")
        self.window.geometry("1400x850")
        
        # 이미지 및 ROI 관련 데이터 상태 관리
        self.cv_img = None          # 원본 OpenCV 이미지 (BGR)
        self.display_img = None     # 캔버스 출력용 PIL 이미지
        self.roi_rect = None        # 드래그 중인 사각형 ID
        
        # 기하학 좌표 데이터
        self.start_x = None
        self.start_y = None
        self.roi_coords = None      # (x1, y1, x2, y2) 원본 좌표계 기준
        self.master_center = None   # 기준 마스터 좌표 (X, Y)
        
        self._create_layout()

    def _create_layout(self):
        """좌측 제어판 패널 및 우측 이미지 캔버스 레이아웃 생성"""
        # 메인 좌우 분할 프레임
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- 좌측 컨트롤 패널 ---
        ctrl_panel = ttk.LabelFrame(main_frame, text=" 제어 및 파라미터 설정 ", padding="10")
        ctrl_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 이미지 로드 버튼
        btn_load = ttk.Button(ctrl_panel, text="1. 이미지 파일 열기", command=self.load_image)
        btn_load.pack(fill=tk.X, pady=(0, 15))
        
        # 마스터 좌표 설정 및 초기화 버튼
        self.btn_master = ttk.Button(ctrl_panel, text="2. 현재 중심을 Master로 등록", command=self.set_master, state=tk.DISABLED)
        self.btn_master.pack(fill=tk.X, pady=(0, 5))
        
        btn_clear_master = ttk.Button(ctrl_panel, text="Master 좌표 초기화", command=self.clear_master)
        btn_clear_master.pack(fill=tk.X, pady=(0, 15))
        
        # 변수 연동 슬라이더 수치용 변수 선엄
        self.val_canny_low = tk.IntVar(value=50)
        self.val_canny_high = tk.IntVar(value=150)
        self.val_ransac_samples = tk.IntVar(value=10)
        self.val_ransac_thresh = tk.DoubleVar(value=5.0)
        self.val_judge_thresh = tk.DoubleVar(value=5.0)
        
        # 슬라이더 컴포넌트 추가 공통 함수
        def add_slider_release(parent, label, var, from_, to, resolution=1):
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.X, pady=5)
            ttk.Label(frame, text=label).pack(side=tk.LEFT)
            lbl_val = ttk.Label(frame, text=str(var.get()))
            lbl_val.pack(side=tk.RIGHT)
            
            # 드래그 중에는 텍스트 수치만 빠르게 변경 (검사 연산 X)
            def on_slider_scroll(val):
                if resolution == 1:
                    var.set(int(float(val)))
                    lbl_val.config(text=str(var.get()))
                else:
                    var.set(round(float(val), 2))
                    lbl_val.config(text=f"{var.get():.2f}")
            
            scale = ttk.Scale(parent, from_=from_, to=to, variable=var, command=on_slider_scroll)
            scale.pack(fill=tk.X, pady=(0, 5))
            
            # [핵심] 마우스 왼쪽 버튼을 뗄 때(<ButtonRelease-1>)에만 메인 알고리즘 호출
            scale.bind("<ButtonRelease-1>", lambda event: self.run_inspection())
            
        # 파라미터 컨트롤 레이아웃 구성
        add_slider_release(ctrl_panel, "Canny Low Threshold:", self.val_canny_low, 1, 255)
        add_slider_release(ctrl_panel, "Canny High Threshold:", self.val_canny_high, 1, 255)
        add_slider_release(ctrl_panel, "RANSAC Min Samples:", self.val_ransac_samples, 5, 1000, 10)
        add_slider_release(ctrl_panel, "RANSAC Residual Thresh:", self.val_ransac_thresh, 1.0, 100.0, 10.0)
        add_slider_release(ctrl_panel, "높이 판정 허용 편차 (Pixel):", self.val_judge_thresh, 0.5, 20.0, 0.5)
        
        # --- 결과 표시 창 ---
        res_panel = ttk.LabelFrame(ctrl_panel, text=" 검사 결과 상태 데이터 ", padding="10")
        res_panel.pack(fill=tk.BOTH, expand=True, pady=15)
        
        self.lbl_master_pos = ttk.Label(res_panel, text="Master 중심: 미등록", font=("맑은 고딕", 10))
        self.lbl_master_pos.pack(anchor=tk.W, pady=2)
        self.lbl_current_pos = ttk.Label(res_panel, text="현재 복원 중심: - ", font=("맑은 고딕", 10))
        self.lbl_current_pos.pack(anchor=tk.W, pady=2)
        self.lbl_current_points = ttk.Label(res_panel, text="타원 정보: - ", font=("맑은 고딕", 10))
        self.lbl_current_points.pack(anchor=tk.W, pady=2)
        self.lbl_error = ttk.Label(res_panel, text="중심점 변위: -", font=("맑은 고딕", 10))
        self.lbl_error.pack(anchor=tk.W, pady=2)
        
        self.lbl_status = ttk.Label(res_panel, text="READY", font=("맑은 고딕", 22, "bold"), foreground="gray")
        self.lbl_status.pack(side=tk.BOTTOM, pady=10)
        
        # --- 우측 메인 대형 캔버스 패널 ---
        self.canvas_frame = ttk.Frame(main_frame)
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 마우스 스크롤/드래그 지원을 위한 스크롤바 바인딩 캔버스
        self.canvas = tk.Canvas(self.canvas_frame, bg="dark gray", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # ROI 지정을 위한 마우스 이벤트 바인딩
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    # =========================================================================
    # 3. 이벤트 핸들러 및 영상 연산 처리 인터페이스 부
    # =========================================================================
    
    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")])
        if not file_path:
            return
            
        # 고해상도 이미지 데이터 관리 아키텍처 적용
        self.cv_img = cv2.imread(file_path)
        self.roi_coords = None
        self.clear_master()
        
        self.display_current_image()

    def display_current_image(self, base_img=None):
        """오리지널 OpenCV 매트릭스를 Tkinter 캔버스 포맷으로 안전하게 전송 및 갱신"""
        if base_img is None:
            base_img = self.cv_img.copy()
            
        rgb_img = cv2.cvtColor(base_img, cv2.COLOR_BGR2RGB)
        self.display_img = ImageTk.PhotoImage(image=Image.fromarray(rgb_img))
        
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.display_img)
        # 캔버스 윈도우 스크롤 스케일 동적 보정
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if self.roi_rect:
            self.canvas.delete(self.roi_rect)
        self.roi_rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=2)

    def on_move_press(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.roi_rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        
        # 바운딩 박스 정규화 연산 [x1, y1, x2, y2]
        x1, x2 = min(int(self.start_x), int(end_x)), max(int(self.start_x), int(end_x))
        y1, y2 = min(int(self.start_y), int(end_y)), max(int(self.start_y), int(end_y))
        
        if (x2 - x1) > 10 and (y2 - y1) > 10 and self.cv_img is not None:
            self.roi_coords = (x1, y1, x2, y2)
            self.btn_master.config(state=tk.NORMAL)
            self.run_inspection()

    def run_inspection(self):
        """ROI 정보 및 슬라이더 파라미터가 실시간 변경될 시 알고리즘 함수 연동 연산"""
        if self.cv_img is None or self.roi_coords is None:
            return
            
        x1, y1, x2, y2 = self.roi_coords
        
        # 메인 영상 행렬 범위를 벗어나지 않도록 세이프가드 적용
        h, w = self.cv_img.shape[:2]
        x1, x2 = max(0, x1), min(w, x2)
        y1, y2 = max(0, y1), min(h, y2)
        
        # 1. ROI 크롭 영역 분할
        roi_img = self.cv_img[y1:y2, x1:x2].copy()
        
        # 2. 알고리즘 제 1단계 실행: 원호 특징 픽셀 검출
        points = extract_arc_points(roi_img, self.val_canny_low.get(), self.val_canny_high.get())
        
        img_out = self.cv_img.copy()
        
        if points is None:
            self.update_result_ui("NG_NO_EDGE", "-", "RED")
            self.display_current_image(img_out)
            return
            
        # 3. 알고리즘 제 2단계 실행: RANSAC 수학 모델 기반 가상 타원 역추적
        ellipse_data = fit_ellipse_ransac(
            points, 
            min_samples=self.val_ransac_samples.get(),
            residual_threshold=self.val_ransac_thresh.get()
        )
        
        if ellipse_data is None:
            self.update_result_ui("NG_FIT_FAIL", "-", "ORANGE")
            # 검출 실패 시 에지 픽셀만이라도 시각화 처리 해줌 (디버깅 용이)
            for p in points:
                cv2.circle(img_out, (int(p[0] + x1), int(p[1] + y1)), 1, (0, 0, 255), -1)
            self.display_current_image(img_out)
            return
            
        # 로컬 ROI 좌표를 글로벌 원본 이미지 좌표계로 보정 매핑
        local_cx, local_cy = ellipse_data["center"]
        global_cx = local_cx + x1
        global_cy = local_cy + y1
        self.current_center = (global_cx, global_cy)
        
        self.lbl_current_pos.config(text=f"현재 복원 중심: X={global_cx:.1f}, Y={global_cy:.1f}")
        
        # 시각화 그래픽스 드로잉 (가상 복원 타원 및 글로벌 중심 스폿)
        major, minor, angle = int(ellipse_data["major_axis"]/2), int(ellipse_data["minor_axis"]/2), int(ellipse_data["angle"])
        cv2.ellipse(
            img_out, 
            (int(global_cx), int(global_cy)), 
            (int(ellipse_data["major_axis"]/2), int(ellipse_data["minor_axis"]/2)), 
            int(ellipse_data["angle"]), 0, 360, (255, 0, 0), 2  # 파란색 가상 복원 선
        )
        cv2.circle(img_out, (int(global_cx), int(global_cy)), 6, (255, 0, 0), -1)
        
        # RANSAC 유효 인라이어 픽셀들을 녹색 점으로 시각화하여 품질 확인 유도
        inliers = ellipse_data["inliers"]
        for p in points[inliers]:
            cv2.circle(img_out, (int(p[0] + x1), int(p[1] + y1)), 2, (0, 255, 0), -1)
        count = len(points[inliers])
        self.lbl_current_points.config(text=f"타원 정보: 점수={count}, major={major}, minor={minor}, angle={angle}")

        # 4. 알고리즘 제 3단계 실행: 높이 변위 판정 로직
        if self.master_center is not None:
            status, error_val = judge_height_defect(
                self.current_center, 
                self.master_center, 
                distance_threshold=self.val_judge_thresh.get()
            )
            # 마스터 좌표 위치 노란색 크로스헤어로 표기
            cv2.drawMarker(img_out, (int(self.master_center[0]), int(self.master_center[1])), (0, 255, 255), cv2.MARKER_CROSS, 20, 2)
            color = "GREEN" if status == "OK" else "RED"
            self.update_result_ui(status, f"{error_val:.2f} px", color)
        else:
            self.update_result_ui("TEACHING 필요", "-", "BLUE")
            
        # 변경된 검사 결과 그래픽 적용 및 출력 업데이트
        self.display_current_image(img_out)

    def set_master(self):
        """현재 타원의 가상 중심을 높이 검사 판정의 절대 마스터 기준으로 티칭 저장"""
        if hasattr(self, 'current_center') and self.current_center is not None:
            self.master_center = self.current_center
            self.lbl_master_pos.config(text=f"Master 중심: X={self.master_center[0]:.1f}, Y={self.master_center[1]:.1f}")
            self.run_inspection()

    def clear_master(self):
        self.master_center = None
        self.lbl_master_pos.config(text="Master 중심: 미등록")
        if self.roi_coords is not None:
            self.run_inspection()

    def update_result_ui(self, status, error_text, color_str):
        self.lbl_status.config(text=status, foreground=color_str.lower())
        self.lbl_error.config(text=f"중심점 변위: {error_text}")


# =========================================================================
# 3. 프로그램 실행 진입점 (Main Entrypoint)
# =========================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = BowlInspectorGUI(root)
    root.mainloop()