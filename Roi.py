import tkinter as tk

class Roi:
    def __init__(self, canvas: tk.Canvas, x1, y1, x2, y2, *, min_size=20, handle_radius=4, width=1, dash=(2, 2),
                 rect_color="goldenrod", cross_color="hotpink", handle_color="#00ff00"):
        self.canvas = canvas
        
        # 기하학적 설정 (픽셀 단위)
        self.min_size = min_size
        self.handle_radius = handle_radius  # 현광 녹색 원(핸들)의 반지름
        
        # ROI 상태 변수
        self.selected_handle = None # 현재 드래그 중인 핸들 타입
        self.drag_data = {"x": 0, "y": 0} # 이동/크기조절 시작 좌표

        # --- 1. 캔버스 객체 생성 ---
        
        # A. 황토색 점선 직사각형 (Goldenrod dashed rectangle)
        # tags는 이 객체들을 하나의 세트로 묶어 관리하기 위해 사용합니다.
        self.rect = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=rect_color, width=width, dash=dash,
            tags="roi_bound"
        )

        # B. 핑크색 중심 십자선 (Pink center cross)
        self.cross_h = self.canvas.create_line(0, 0, 0, 0, fill=cross_color, width=width, tags="roi_core")
        self.cross_v = self.canvas.create_line(0, 0, 0, 0, fill=cross_color, width=width, tags="roi_core")
        
        # C. 현광 녹색 원 핸들 (hot green handles: corners and midpoints)
        # 총 8개: [NW, N, NE, W, E, SW, S, SE] 순서
        self.handles = []
        handle_tags = [
            "nw", "n", "ne",
            "w",       "e",
            "sw", "s", "se"
        ]
        for tag in handle_tags:
            handle = self.canvas.create_oval(
                0, 0, 0, 0,
                fill=handle_color, outline="black", width=width,
                tags=("roi_handle", tag) # 두 개의 태그 부여
            )
            self.handles.append(handle)
        # --- 2. 초기 위치 업데이트 ---
        self.update_geometry(x1, y1, x2, y2)

        # --- 3. 이벤트 바인딩 (상호작용) ---
        
        # 위치 이동 (황토색 점선 사각형 클릭 시)
        self.canvas.tag_bind("roi_bound", "<ButtonPress-1>", self.on_rect_press)
        self.canvas.tag_bind("roi_bound", "<B1-Motion>", self.on_rect_drag)
        self.canvas.tag_bind("roi_bound", "<ButtonRelease-1>", self.on_release)

        # 위치 이동 (핑크색 중심 십자선 클릭 시)
        self.canvas.tag_bind("roi_core", "<ButtonPress-1>", self.on_rect_press)
        self.canvas.tag_bind("roi_core", "<B1-Motion>", self.on_rect_drag)
        self.canvas.tag_bind("roi_core", "<ButtonRelease-1>", self.on_release)
        
        # 마우스 커서 변경 (황토색 점선 사각형 위에 있을 때 - 이동 커서)
        self.canvas.tag_bind("roi_bound", "<Enter>", lambda e: self.canvas.config(cursor="fleur"))
        self.canvas.tag_bind("roi_bound", "<Leave>", lambda e: self.canvas.config(cursor=""))
        
        # 마우스 커서 변경 (핑크색 중심 십자선 위에 있을 때 - 이동 커서)
        self.canvas.tag_bind("roi_core", "<Enter>", lambda e: self.canvas.config(cursor="fleur"))
        self.canvas.tag_bind("roi_core", "<Leave>", lambda e: self.canvas.config(cursor=""))

        # 크기 조절 (현광 녹색 원 클릭 시)
        self.canvas.tag_bind("roi_handle", "<ButtonPress-1>", self.on_handle_press)
        self.canvas.tag_bind("roi_handle", "<B1-Motion>", self.on_handle_drag)
        self.canvas.tag_bind("roi_handle", "<ButtonRelease-1>", self.on_release)
        
        # 마우스 커서 변경 (핸들 위에 있을 때)
        cursors = {
            "nw": "top_left_corner", "n": "top_side", "ne": "top_right_corner",
            "w": "left_side", "e": "right_side",
            "sw": "bottom_left_corner", "s": "bottom_side", "se": "bottom_right_corner"
        }
        for tag, cursor in cursors.items():
            self.canvas.tag_bind(tag, "<Enter>", lambda e, c=cursor: self.canvas.config(cursor=c))
        
        self.canvas.tag_bind("roi_handle", "<Leave>", lambda e: self.canvas.config(cursor=""))

    def get_coords(self):
        """현재 ROI의 [x1, y1, x2, y2] 좌표를 반환합니다."""
        return self.canvas.coords(self.rect)

    def update_geometry(self, x1, y1, x2, y2):
        """좌표를 기반으로 모든 내부 객체(직사각형, 십자선, 핸들)의 위치를 다시 그립니다."""
        # 1. 메인 직사각형 업데이트
        self.canvas.coords(self.rect, x1, y1, x2, y2)
        
        # 계산 편의를 위한 변수
        cx = (x1 + x2) / 2 # 중심 X
        cy = (y1 + y2) / 2 # 중심 Y
        r = self.handle_radius
        
        # 2. 중심 십자선 업데이트
        cross_size = 6 # 십자선 총 길이
        self.canvas.coords(self.cross_h, cx - cross_size, cy, cx + cross_size, cy)
        self.canvas.coords(self.cross_v, cx, cy - cross_size, cx, cy + cross_size)
        
        # 3. 8개 핸들(현광 녹색 원) 위치 업데이트
        positions = [
            (x1, y1), (cx, y1), (x2, y1), # Top row
            (x1, cy),           (x2, cy), # Middle row
            (x1, y2), (cx, y2), (x2, y2)  # Bottom row
        ]
        
        for handle, (hx, hy) in zip(self.handles, positions):
            self.canvas.coords(handle, hx-r, hy-r, hx+r, hy+r)

    # --- 대화형 동작 함수들 (Interaction Handlers) ---

    def on_rect_press(self, event):
        """직사각형을 클릭했을 때 동작"""
        if self.selected_handle:
            return
        
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        # 커서를 잡는 모양(fleur 또는 hand2)으로 변경
        self.canvas.config(cursor="fleur")

    def on_rect_drag(self, event):
        """직사각형을 드래그하여 위치를 이동할 때 동작"""
        if self.selected_handle:
            return
        
        # 마우스 이동 거리 계산
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        
        # 현재 좌표 가져오기
        x1, y1, x2, y2 = self.get_coords()
        
        # 좌표 업데이트 (이동)
        self.update_geometry(x1 + dx, y1 + dy, x2 + dx, y2 + dy)
        
        # 드래그 시작점 업데이트
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_handle_press(self, event):
        """핸들을 클릭했을 때 동작"""
        # 클릭된 객체의 태그 중 핸들 식별 태그(nw, n, e 등)를 찾음
        item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(item)
        for tag in tags:
            if tag in ["nw", "n", "ne", "w", "e", "sw", "s", "se"]:
                self.selected_handle = tag
                break
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_handle_drag(self, event):
        """핸들을 드래그하여 크기를 조절할 때 동작"""
        if not self.selected_handle:
            return

        # 마우스 이동 거리 계산
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        
        # 현재 좌표 가져오기
        x1, y1, x2, y2 = self.get_coords()
        
        # 선택된 핸들에 따라 좌표 수정 (크기 조절 로직)
        h = self.selected_handle
        if "n" in h: y1 += dy # 북쪽 포함 핸들 (nw, n, ne)
        if "s" in h: y2 += dy # 남쪽 포함 핸들 (sw, s, se)
        if "w" in h: x1 += dx # 서쪽 포함 핸들 (nw, w, sw)
        if "e" in h: x2 += dx # 동쪽 포함 핸들 (ne, e, se)

        # 뒤집힘 방지 최소 크기 제한 (예: 20x20)
        if x2 - x1 < self.min_size:
            if "w" in h: x1 = x2 - self.min_size
            else: x2 = x1 + self.min_size
        if y2 - y1 < self.min_size:
            if "n" in h: y1 = y2 - self.min_size
            else: y2 = y1 + self.min_size

        # 그래픽 업데이트
        self.update_geometry(x1, y1, x2, y2)
        
        # 드래그 시작점 업데이트
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_release(self, event):
        """마우스 버튼을 뗐을 때"""
        self.selected_handle = None
        self.canvas.config(cursor="") # 커서 원복

    def delete(self):
        """ROI를 캔버스에서 완전히 제거합니다."""
        self.canvas.delete(self.rect)
        self.canvas.delete(self.cross_h)
        self.canvas.delete(self.cross_v)
        for handle in self.handles:
            self.canvas.delete(handle)

# ==========================================
# 클래스 사용 예제 (실행 가능한 코드)
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Tkinter ROI Class Example")

    # 예제 캔버스 생성 (그림과 유사하게 눈금 배경 적용)
    # 실제 눈금을 그리는 대신 배경색을 밝은 회색으로 설정
    canvas_width = 800
    canvas_height = 600
    canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg="#f5f5f0") # Grid-like paper color
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # 캔버스에 아주 옅은 눈금선 그리기 (그림 분위기 재현)
    grid_size = 20
    for x in range(0, canvas_width, grid_size):
        canvas.create_line(x, 0, x, canvas_height, fill="#e0e0e0", dash=(1, 5))
    for y in range(0, canvas_height, grid_size):
        canvas.create_line(0, y, canvas_width, y, fill="#e0e0e0", dash=(1, 5))

    # --- ROI 클래스 인스턴스 생성 ---
    # 초기 좌표 (x1, y1, x2, y2) 설정
    my_roi = Roi(canvas, x1=200, y1=150, x2=600, y2=450)

    # 안내 메시지
    label = tk.Label(root, text="검정색 원(핸들)을 드래그하여 ROI 크기를 조절해보세요.", pady=10)
    label.pack()

    def print_coords():
        print(f"현재 ROI 좌표: {my_roi.get_coords()}")

    btn = tk.Button(root, text="좌표 출력 (Console)", command=print_coords)
    btn.pack(pady=5)

    root.mainloop()
