import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from typing import Dict
import yaml
import os

from Roi import Roi


class ViewFrame(ttk.Frame):        
    def __init__(self, parent, cameras: Dict[str, str] = None):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self.baseimg: Image = None
        self.dispimg: Image = None
        self.tk_img: ImageTk = None
        self.img_id: int = None
        self.cur_roi: Roi = None
        self.scale: float = 1.0
        self.islive: bool = False
        self.roi_move: int = 0
        self.roi_size: int = 0

        if cameras is not None:
            self.cameras = cameras
        else:
            self.load_cameras("cameras.yaml")  # cameras.yaml 파일에서 카메라 정보 로드

        # 1. top frame 생성 하고
        # 그 안에 Open Image, Save Image 버튼과 카메라 선택 콤보박스, Live 버튼 그리고 roi_btn_frame 생성, 이미지상에 마우스 픽셀 위치 및 픽셀값 표시하는 label 추가
        # 2. roi_btn_frame 안에 ROI 추가, ROI 삭제 버튼 생성
        # 3. 이미지 캔버스 생성

        # 이미지 열기 및 저장
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=5, pady=0)
        open_button = ttk.Button(top_frame, text="Open Image", command=self.on_open_image)
        open_button.pack(side=tk.LEFT, padx=5, pady=0)
        save_button = ttk.Button(top_frame, text="Save Image", command=self.on_save_image)
        save_button.pack(side=tk.LEFT, padx=5, pady=0)

        # 카메라 선택 및 Live
        self.cameras_combo = ttk.Combobox(top_frame, values=list(self.cameras.keys()), state="readonly")
        self.cameras_combo.pack(side=tk.LEFT, padx=5)
        self.cameras_combo.current(0)
        self.live_button = ttk.Button(top_frame, style="Stop.TButton", text="▶ Live On", command=self.on_live, width=12)
        self.live_button.pack(side=tk.LEFT, padx=5)

        # 확대 축소 
        zoom_in_button = ttk.Button(top_frame, command=lambda: self.on_zoom(min(self.scale/0.8, 5.0)), text="+")
        zoom_in_button.pack(side=tk.LEFT, padx=5, pady=0)
        zoom_out_button = ttk.Button(top_frame, command=lambda: self.on_zoom(max(0.1, self.scale*0.8)), text="-")
        zoom_out_button.pack(side=tk.LEFT, padx=5, pady=0)
        zoom_reset_button = ttk.Button(top_frame, command=self.on_reset_zoom, text="ㅁ")
        zoom_reset_button.pack(side=tk.LEFT, padx=5, pady=0)

        # ROI 버튼
        roi_btn_frame = ttk.Frame(top_frame)
        roi_btn_frame.pack(side=tk.LEFT, padx=20)
        self.create_roi_buttons(roi_btn_frame)

        # 캔버스 및 스크롤
        scroll_frame = ttk.Frame(self)
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.canvas = tk.Canvas(scroll_frame, bg="#000000")
        hbar = ttk.Scrollbar(scroll_frame, orient=tk.HORIZONTAL)
        vbar = ttk.Scrollbar(scroll_frame, orient=tk.VERTICAL)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        hbar.config(command=self.canvas.xview)
        vbar.config(command=self.canvas.yview)
        self.canvas.config(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

        self.img_id = self.canvas.create_image(0, 0, anchor="nw")
        self.cur_roi = Roi(self.canvas, 100, 100, 200, 200, mode=Roi.MODE_IDLE)
        
        # 이벤트 바인딩
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)       # Windows
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)         # Linux (스크롤 업)
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)         # Linux (스크롤 다운)
        self.bind("<Configure>", self.on_resize)  # 창 크기 변경 감지

    def create_roi_buttons(self, frame: ttk.Frame):
        # 1. top frame 생성, 그 안에 size, ↑, move 버튼 생성
        top_frame = ttk.Frame(frame)
        top_frame.pack(fill=tk.X, pady=0)
        self.size_button = ttk.Button(top_frame, text="Size", command=self.on_roi_size, width=5)
        self.size_button.pack(side=tk.LEFT, padx=0, pady=0)
        up_button = ttk.Button(top_frame, text="↑", command=self.on_roi_up, width=5)
        up_button.pack(side=tk.LEFT, padx=0, pady=0)
        self.move_button = ttk.Button(top_frame, text="Move", command=self.on_roi_move, width=5)
        self.move_button.pack(side=tk.LEFT, padx=0, pady=0)
        # 2. bottom frame 생성, 그 안에 ↓, ←, → 버튼, 픽셀 정보 라벨 생성
        bottom_frame = ttk.Frame(frame)
        bottom_frame.pack(fill=tk.X, pady=0)
        left_button = ttk.Button(bottom_frame, text="←", command=self.on_roi_left, width=5)
        left_button.pack(side=tk.LEFT, padx=0, pady=0)
        down_button = ttk.Button(bottom_frame, text="↓", command=self.on_roi_down, width=5)
        down_button.pack(side=tk.LEFT, padx=0, pady=0)
        right_button = ttk.Button(bottom_frame, text="→", command=self.on_roi_right, width=5)
        right_button.pack(side=tk.LEFT, padx=0, pady=0)
        
        self.pixel_info_label = ttk.Label(bottom_frame, text="픽셀 위치: (x, y) | 픽셀값: (R, G, B)")
        self.pixel_info_label.pack(side=tk.RIGHT, padx=5)

    def load_cameras(self, path: str):
        # cameras.yaml 파일을 읽어와서 카메라 정보를 self.cameras 딕셔너리에 저장하는 함수
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if isinstance(data, dict):
                items = data.get("OMEGA_A_JEP", [])
                self.cameras = {str(item['name']): str(item['url']) for item in items}
            else:
                self.cameras = {}
                raise ValueError("Unsupported cameras.yaml format")
        except Exception as e:
            self.cameras = {}
            messagebox.showerror("오류", f"카메라 정보를 불러오는 중 오류가 발생했습니다: {e}")
    
    def on_open_image(self):
        file_path = filedialog.askopenfilename( title="Select a image file", initialdir=os.getcwd(), filetypes=[("Image files", "*.bmp *.jpg *.png")])
        self.open_image(file_path)

    def open_image(self, file_path:str):
        try:
            if file_path:
                img = Image.open(file_path)
                self.baseimg = img
                self.scale = 1.0
                self.update_canvas()
        except Exception as e:
            messagebox.showerror("오류", f"이미지 열기 중 오류 발생:\n{e}")
    
    def on_save_image(self):
        file_path = filedialog.asksaveasfilename(title="이미지 저장", defaultextension=".jpg", filetypes=[("JPEG 파일", "*.jpg;*.jpeg"), ("BMP 파일", "*.bmp"), ("PNG 파일", "*.png")],)
        self.save_image(file_path)
    
    def save_image(self, file_path:str):
        try:
            if file_path:
                self.baseimg.save(file_path)
                messagebox.showinfo("저장 완료", f"이미지가 저장되었습니다:\n{os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("오류", f"이미지 저장 중 오류 발생:\n{e}")

    def on_live(self):
        self.islive = not self.islive
        if self.islive: # Live 시작
            self.live_button.config(text="■ Live Off", style="Live.TButton")
            self.update_live(self.cameras_combo.get())
        else: # Live 정지
            self.live_button.config(text="▶ Live On", style="Stop.TButton")
            if self.live_timer_id:
                self.after_cancel(self.live_timer_id)
                self.live_timer_id = None

    def update_live(self, cam_id:str):
        print(f"cam[{cam_id}].read()")
        img: Image = None # self.cams[cam_id].read()
        if img:
            self.baseimg = img
            self.update_canvas()
        if self.islive:
            self.live_timer_id = self.after(30, self.update_live, cam_id)

    def on_mouse_wheel(self, event):
        # 마우스 휠로 확대/축소
        if event.num == 4 or event.delta > 0:
            self.on_zoom(min(self.scale/0.8, 5.0))
        elif event.num == 5 or event.delta < 0:
            self.on_zoom(max(0.1, self.scale*0.8))

    def on_resize(self, event):
        if self.baseimg is None:
            return
        if event.widget == self:
            # new scal 계산
            ch, cw = event.height, event.width
            ih, iw = self.baseimg.height, self.baseimg.width
            new_scale = min(ch/ih, cw/iw)

            self.cur_roi.update_scale(self.scale, new_scale)
            self.scale = new_scale
            self.update_canvas()

    def on_zoom(self, new_scale:float):
        if self.baseimg is None:
            return
        self.cur_roi.update_scale(self.scale, new_scale)
        self.scale = new_scale
        self.update_canvas()

    def on_reset_zoom(self):
        if self.baseimg is None:
            return
        # new scal 계산
        ch, cw = self.canvas.winfo_height(), self.canvas.winfo_width()
        ih, iw = self.baseimg.height, self.baseimg.width
        new_scale = min(ch/ih, cw/iw)

        self.cur_roi.update_scale(self.scale, new_scale)
        self.scale = new_scale
        self.update_canvas()

    def update_canvas(self):
        if self.baseimg is None:
            return
        
        # 현재 배율에 맞춰 이미지 리사이즈
        width = int(self.baseimg.width * self.scale)
        height = int(self.baseimg.height * self.scale)
        self.dispimg = self.baseimg.resize((width, height), Image.NEAREST)

        self.tk_img = ImageTk.PhotoImage(self.dispimg) # tk 이미지 객체로 변환
        self.canvas.image = self.tk_img # GC 방지

        self.canvas.itemconfig(self.img_id, image=self.tk_img)
        x1, y1, x2, y2 = self.cur_roi.get_coords()
        self.cur_roi.update_geometry(x1, y1, x2, y2)

        self.canvas.config(scrollregion=(0, 0, width, height))

    def update_roi_coords(self, img_coords) -> None:
        if img_coords and len(img_coords) == 4:
            coords = [(coord*self.scale) for coord in img_coords]
            self.cur_roi.update_geometry(coords[0], coords[1], coords[2], coords[3])
        else:
            self.cur_roi.update_geometry(100, 100, 200, 200)
        self.cur_roi.set_mode(Roi.MODE_EDIT)

    def get_roi_coords(self) -> list[int]:
        canvas_coords = self.cur_roi.get_coords()
        coords = [int(coord/self.scale) for coord in canvas_coords]
        self.cur_roi.set_mode(Roi.MODE_IDLE)
        return coords
    
    def on_roi_size(self) -> None:
        self.roi_move = 0
        if self.roi_size == 0:
            self.roi_size = 1
        elif self.roi_size == 1:
            self.roi_size = 10
        elif self.roi_size == 10:
            self.roi_size = 1

        self.move_button.config(text='move')
        self.size_button.config(text=f'size_{self.roi_size}')
        self.cur_roi.set_mode(Roi.MODE_EDIT)
    
    def on_roi_move(self) -> None:
        self.roi_size = 0
        if self.roi_move == 0:
            self.roi_move = 1
        elif self.roi_move == 1:
            self.roi_move = 10
        elif self.roi_move == 10:
            self.roi_move = 1

        self.size_button.config(text='size')
        self.move_button.config(text=f'move_{self.roi_size}')
        self.cur_roi.set_mode(Roi.MODE_EDIT)

    def on_roi_up(self) -> None:
        x1, y1, x2, y2 = self.cur_roi.get_coords()
        if self.roi_move:
            x1, y1, x2, y2 = x1, max(0, y1-self.roi_move), x2, max(self.cur_roi.min_size, y2-self.roi_move)
        if self.roi_size:
            x1, y1, x2, y2 = x1, max(0, y1-self.roi_size), x2, min(y2+self.roi_size, self.canvas.winfo_height())
            
        self.cur_roi.update_geometry(x1, y1, x2, y2)
        self.cur_roi.set_mode(Roi.MODE_EDIT)

    def on_roi_down(self) -> None:
        x1, y1, x2, y2 = self.cur_roi.get_coords()
        if self.roi_move:
            x1, y1, x2, y2 = x1, min(y1+self.roi_move, self.canvas.winfo_height()-self.cur_roi.min_size), x2, min(y2+self.roi_move, self.canvas.winfo_height())
        if self.roi_size:
            x1, y1, x2, y2 = x1, min(y1+self.roi_size, self.canvas.winfo_height()-self.cur_roi.min_size), x2, max(self.cur_roi.min_size, y2-self.roi_size)
            
        self.cur_roi.update_geometry(x1, y1, x2, y2)
        self.cur_roi.set_mode(Roi.MODE_EDIT)

    def on_roi_left(self) -> None:
        x1, y1, x2, y2 = self.cur_roi.get_coords()
        if self.roi_move:
            x1, y1, x2, y2 = max(0, x1-self.roi_move), y1, max(self.cur_roi.min_size, x2-self.roi_move), y2
        if self.roi_size:
            x1, y1, x2, y2 = min(x1+self.roi_size, self.canvas.winfo_width()), y1, max(self.cur_roi.min_size, x2-self.roi_size), y2
            
        self.cur_roi.update_geometry(x1, y1, x2, y2)
        self.cur_roi.set_mode(Roi.MODE_EDIT)

    def on_roi_right(self) -> None:
        x1, y1, x2, y2 = self.cur_roi.get_coords()
        if self.roi_move:
            x1, y1, x2, y2 = min(x1+self.roi_move, self.canvas.winfo_width()-self.cur_roi.min_size), y1, min(x2+self.roi_move, self.canvas.winfo_width()), y2
        if self.roi_size:
            x1, y1, x2, y2 = max(0, x1-self.roi_size), y1, min(x2+self.roi_size, self.canvas.winfo_width()), y2
            
        self.cur_roi.update_geometry(x1, y1, x2, y2)
        self.cur_roi.set_mode(Roi.MODE_EDIT)
    
    def __delete__(self):
        self.islive = False