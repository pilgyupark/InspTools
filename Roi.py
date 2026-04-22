import tkinter as tk


class Roi:
    MODE_VIEW = "view"
    MODE_EDIT = "edit"
    MODE_CREATE = "create"
    MODE_DELETE = "delete"
    VALID_MODES = {MODE_VIEW, MODE_EDIT, MODE_CREATE, MODE_DELETE}

    def __init__(
        self,
        canvas: tk.Canvas,
        x1,
        y1,
        x2,
        y2,
        *,
        min_size=20,
        cross_size = 6,
        handle_radius=4,
        width=1,
        dash=(2, 2),
        rect_color="goldenrod",
        cross_color="hotpink",
        handle_color="#00ff00",
        mode=MODE_VIEW,
    ):
        self.canvas = canvas

        # 기본 설정 값
        self.min_size = min_size
        self.cross_size = cross_size
        self.handle_radius = handle_radius
        self.width = width
        self.dash = dash
        self.rect_color = rect_color
        self.cross_color = cross_color
        self.handle_color = handle_color

        self.mode = None
        self.selected_handle = None
        self.drag_data = {"x": 0, "y": 0}
        self._create_start = None
        self._create_callback = None
        self._is_creating = False

        # ROI 개체 생성
        self.rect = self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            outline=self.rect_color,
            width=self.width,
            dash=self.dash,
            tags=("roi_bound", "roi"),
        )

        self.cross_h = self.canvas.create_line(
            0, 0, 0, 0, fill=self.cross_color, width=self.width, tags=("roi_core", "roi")
        )
        self.cross_v = self.canvas.create_line(
            0, 0, 0, 0, fill=self.cross_color, width=self.width, tags=("roi_core", "roi")
        )

        self.handles = []
        handle_tags = [
            "nw",
            "n",
            "ne",
            "w",
            "e",
            "sw",
            "s",
            "se",
        ]
        for tag in handle_tags:
            handle = self.canvas.create_oval(
                0,
                0,
                0,
                0,
                fill=self.handle_color,
                outline="black",
                width=self.width,
                tags=("roi_handle", tag, "roi"),
            )
            self.handles.append(handle)

        self.update_geometry(x1, y1, x2, y2)
        self._bind_interaction_handlers()
        self.set_mode(mode, suppress_callback=True)

    def _bind_interaction_handlers(self):
        self.canvas.tag_bind("roi_bound", "<ButtonPress-1>", self.on_rect_press)
        self.canvas.tag_bind("roi_bound", "<B1-Motion>", self.on_rect_drag)
        self.canvas.tag_bind("roi_bound", "<ButtonRelease-1>", self.on_release)

        self.canvas.tag_bind("roi_core", "<ButtonPress-1>", self.on_rect_press)
        self.canvas.tag_bind("roi_core", "<B1-Motion>", self.on_rect_drag)
        self.canvas.tag_bind("roi_core", "<ButtonRelease-1>", self.on_release)

        self.canvas.tag_bind("roi_bound", "<Enter>", lambda e: self.canvas.config(cursor="fleur"))
        self.canvas.tag_bind("roi_bound", "<Leave>", lambda e: self.canvas.config(cursor=""))
        self.canvas.tag_bind("roi_core", "<Enter>", lambda e: self.canvas.config(cursor="fleur"))
        self.canvas.tag_bind("roi_core", "<Leave>", lambda e: self.canvas.config(cursor=""))

        self.canvas.tag_bind("roi_handle", "<ButtonPress-1>", self.on_handle_press)
        self.canvas.tag_bind("roi_handle", "<B1-Motion>", self.on_handle_drag)
        self.canvas.tag_bind("roi_handle", "<ButtonRelease-1>", self.on_release)

        cursors = {
            "nw": "top_left_corner",
            "n": "top_side",
            "ne": "top_right_corner",
            "w": "left_side",
            "e": "right_side",
            "sw": "bottom_left_corner",
            "s": "bottom_side",
            "se": "bottom_right_corner",
        }
        for tag, cursor in cursors.items():
            self.canvas.tag_bind(tag, "<Enter>", lambda e, c=cursor: self.canvas.config(cursor=c))

        self.canvas.tag_bind("roi_handle", "<Leave>", lambda e: self.canvas.config(cursor=""))
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_press, add="+")
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag, add="+")
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release, add="+")

    def get_coords(self):
        return self.canvas.coords(self.rect)

    def update_geometry(self, x1, y1, x2, y2):
        self.canvas.coords(self.rect, x1, y1, x2, y2)

        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        r = self.handle_radius

        self.canvas.coords(self.cross_h, cx - self.cross_size, cy, cx + self.cross_size, cy)
        self.canvas.coords(self.cross_v, cx, cy - self.cross_size, cx, cy + self.cross_size)
        
        # 3. 8개 핸들(현광 녹색 원) 위치 업데이트
        positions = [
            (x1, y1), (cx, y1), (x2, y1), # Top row
            (x1, cy),           (x2, cy), # Middle row
            (x1, y2), (cx, y2), (x2, y2)  # Bottom row
        ]
        for handle, (hx, hy) in zip(self.handles, positions):
            self.canvas.coords(handle, hx - r, hy - r, hx + r, hy + r)

    def set_mode(self, mode, *, suppress_callback=False):
        if mode not in self.VALID_MODES:
            raise ValueError(f"Invalid ROI mode: {mode}")

        if self.mode == self.MODE_DELETE and mode != self.MODE_DELETE:
            raise RuntimeError("Cannot change mode after ROI has been deleted.")

        self.mode = mode
        if mode == self.MODE_DELETE:
            self.delete()
            return

        self._is_creating = False
        self._set_active_state(mode)

        if mode == self.MODE_CREATE:
            self._prepare_for_creation()
        elif mode == self.MODE_EDIT:
            self._show_edit_handles(True)
            self._show_cross(True)
            self._set_style(outline=self.rect_color, dash=self.dash)
        elif mode == self.MODE_VIEW:
            self._show_edit_handles(False)
            self._show_cross(True)
            self._set_style(outline=self.rect_color, dash=self.dash)

        if not suppress_callback and mode == self.MODE_CREATE and self._create_callback:
            self._create_callback(self)

    def _set_active_state(self, mode):
        state = "normal" if mode != self.MODE_DELETE else "hidden"
        self.canvas.itemconfigure(self.rect, state=state)
        self.canvas.itemconfigure(self.cross_h, state=state)
        self.canvas.itemconfigure(self.cross_v, state=state)
        for handle in self.handles:
            self.canvas.itemconfigure(handle, state=state)

    def _set_style(self, *, outline=None, dash=None):
        if outline is not None:
            self.canvas.itemconfigure(self.rect, outline=outline)
        if dash is not None:
            self.canvas.itemconfigure(self.rect, dash=dash)

    def _show_edit_handles(self, visible):
        state = "normal" if visible else "hidden"
        for handle in self.handles:
            self.canvas.itemconfigure(handle, state=state)

    def _show_cross(self, visible):
        state = "normal" if visible else "hidden"
        self.canvas.itemconfigure(self.cross_h, state=state)
        self.canvas.itemconfigure(self.cross_v, state=state)

    def _prepare_for_creation(self):
        self._show_edit_handles(False)
        self._show_cross(False)
        self._set_style(outline="cyan", dash=(4, 4))
        self._is_creating = False
        self._create_start = None

    def _on_canvas_press(self, event):
        if self.mode != self.MODE_CREATE:
            return

        self._create_start = (event.x, event.y)
        self._is_creating = True
        self.update_geometry(event.x, event.y, event.x, event.y)
        self._show_edit_handles(False)
        self._show_cross(False)
        self.canvas.config(cursor="crosshair")

    def _on_canvas_drag(self, event):
        if self.mode != self.MODE_CREATE or not self._is_creating:
            return

        x0, y0 = self._create_start
        self.update_geometry(x0, y0, event.x, event.y)

    def _on_canvas_release(self, event):
        if self.mode != self.MODE_CREATE or not self._is_creating:
            return

        self._is_creating = False
        self.canvas.config(cursor="")

        x0, y0 = self._create_start
        x1, y1 = min(x0, event.x), min(y0, event.y)
        x2, y2 = max(x0, event.x), max(y0, event.y)
        if abs(x2 - x1) < self.min_size or abs(y2 - y1) < self.min_size:
            self.update_geometry(x1, y1, x1 + self.min_size, y1 + self.min_size)

        self.update_geometry(x1, y1, x2, y2)
        self.set_mode(self.MODE_EDIT)

        if self._create_callback:
            self._create_callback(self)

    def on_rect_press(self, event):
        if self.mode != self.MODE_EDIT or self.selected_handle:
            return

        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.canvas.config(cursor="fleur")

    def on_rect_drag(self, event):
        if self.mode != self.MODE_EDIT or self.selected_handle:
            return

        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        x1, y1, x2, y2 = self.get_coords()
        self.update_geometry(x1 + dx, y1 + dy, x2 + dx, y2 + dy)
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_handle_press(self, event):
        if self.mode != self.MODE_EDIT:
            return

        item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))[0]
        tags = self.canvas.gettags(item)
        for tag in tags:
            if tag in ["nw", "n", "ne", "w", "e", "sw", "s", "se"]:
                self.selected_handle = tag
                break
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_handle_drag(self, event):
        if self.mode != self.MODE_EDIT or not self.selected_handle:
            return

        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        x1, y1, x2, y2 = self.get_coords()
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

        self.update_geometry(x1, y1, x2, y2)
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_release(self, event):
        if self.mode != self.MODE_EDIT:
            return

        self.selected_handle = None
        self.canvas.config(cursor="")

    def start_creation(self, on_complete=None):
        """새로운 ROI 생성을 시작합니다. 기존 ROI는 삭제됩니다."""
        if self.mode != self.MODE_DELETE:
            self.delete()
        # 새로운 ROI 생성은 외부에서 호출해야 합니다.
        raise NotImplementedError("Use create_new_roi function instead")

    def delete(self):
        self.mode = self.MODE_DELETE
        self.canvas.delete(self.rect)
        self.canvas.delete(self.cross_h)
        self.canvas.delete(self.cross_v)
        for handle in self.handles:
            self.canvas.delete(handle)



if __name__ == "__main__":
    import os
    from tkinter import filedialog
    from PIL import Image, ImageTk

    scale: float = 1.0
    canvas: tk.Canvas = None
    img: Image = None
    my_roi: Roi = None

    def open_image_file() -> Image:
        try:
            file_path = filedialog.askopenfilename( title="Select a image file", initialdir=os.getcwd(), filetypes=[("Image files", "*.bmp *.jpg *.png")])
            if file_path:
                return Image.open(file_path)
        except Exception as e:
            print(e)
        return None
    
    def zoom(factor):
        global scale
        if my_roi:
            [x1, y1, x2, y2] = my_roi.get_coords()
            rx1, ry1, rx2, ry2 = (x1 / scale), (y1 / scale), (x2 / scale), (y2 / scale)
        scale = factor
        if my_roi:
            my_roi.update_geometry(rx1*scale, ry1*scale, rx2*scale, ry2*scale)
        show_image()

    def show_image():
        global canvas, img, my_roi
        # 현재 배율에 맞춰 이미지 리사이즈
        print(canvas.xview(), canvas.yview())
        if my_roi:
            [x1, y1, x2, y2], mode = my_roi.get_coords(), my_roi.mode
        else:
            x1, y1, x2, y2, mode = 200, 150, 600, 450, Roi.MODE_VIEW

        width = int(img.width * scale)
        height = int(img.height * scale)
        resized = img.resize((width, height), Image.NEAREST)

        tk_img = ImageTk.PhotoImage(resized) # tk 이미지 객체로 변환
        canvas.image = tk_img # GC 방지
        canvas.delete("all") # 기존 모든 canvas Objects 제거
        canvas.create_image(0, 0, image=tk_img, anchor="nw")
        canvas.config(scrollregion=(0, 0, width, height))
        print(canvas.xview(), canvas.yview())
        
        my_roi = Roi(canvas, x1=x1, y1=y1, x2=x2, y2=y2, mode=mode)

    def update_roi():
        global my_roi
        x1, y1, x2, y2 = my_roi.get_coords()
        my_roi.update_geometry(x1, y1, x2, y2)


    def main():
        global img, canvas, my_roi
        root = tk.Tk()
        root.title("Tkinter ROI Class Example")

        frame = tk.Frame(root)
        frame.pack(fill=tk.BOTH, expand=True)

        canvas_width = 800
        canvas_height = 600
        canvas = tk.Canvas(frame, width=canvas_width, height=canvas_height, bg="#1f1f1b")
        hbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
        vbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        hbar.config(command=canvas.xview)
        vbar.config(command=canvas.yview)
        canvas.config(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

        img = open_image_file()
        if img is None:
            root.destroy()
        show_image()

        label = tk.Label(root, text="VIEW 모드: 클릭/드래그 불가, EDIT 모드로 전환하세요.", pady=10)
        label.pack()

        def print_coords():
            if my_roi and my_roi.mode != Roi.MODE_DELETE:
                print(f"현재 ROI 좌표: {my_roi.get_coords()}")
            else:
                print("ROI가 없습니다.")

        def create_new_roi():
            global my_roi
            if my_roi and my_roi.mode != Roi.MODE_DELETE:
                my_roi.set_mode(Roi.MODE_DELETE)
            my_roi = Roi(canvas, 0, 0, 0, 0, mode=Roi.MODE_CREATE)
            my_roi._create_callback = lambda roi: print(f"New ROI created at {roi.get_coords()}")

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="View", command=lambda: my_roi.set_mode(Roi.MODE_VIEW) if my_roi and my_roi.mode != Roi.MODE_DELETE else None).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Edit", command=lambda: my_roi.set_mode(Roi.MODE_EDIT) if my_roi and my_roi.mode != Roi.MODE_DELETE else None).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Create", command=create_new_roi).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Delete", command=lambda: my_roi.set_mode(Roi.MODE_DELETE) if my_roi and my_roi.mode != Roi.MODE_DELETE else None).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="좌표 출력", command=print_coords).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="+", command=lambda: zoom(min(scale / 0.8, 5.0))).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="-", command=lambda: zoom(max(1.0, scale * 0.8))).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="[]", command=lambda: zoom(1.0)).pack(side=tk.LEFT, padx=2)

        root.mainloop()

    main()
