import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict
from pathlib import Path
import yaml
from ParameManager import ParameterForm, ParameterManager, User, UserManager

class MainFrame:
        VERSION_INFO: str = "version 1.7.2"
        def __init__(self, root, require_login: bool = True):
            self.root = root
            self.require_login = require_login
            self.current_user = User()  # 기본 사용자 설정

            self._setup_ui()
            
        def _setup_ui(self):
            self.root.title(f"VisInsp - (권한: {self.current_user.access_level} - {self.current_user.full_name})")
            self.root.geometry("1200x750")
            self.root.configure(bg="#1f2330")

            style = ttk.Style(self.root)
            style.theme_use("default")
            style.configure("TNotebook", background="#1f2330", borderwidth=0)
            style.configure("TNotebook.Tab", background="#252a3c", foreground="#d4d4d4", padding=[10, 6])
            style.map("TNotebook.Tab",
                      background=[("selected", "#0a84ff")],
                      foreground=[("selected", "#ffffff")])
            style.configure("TFrame", background="#1f2330")
            style.configure("TLabel", background="#1f2330", foreground="#d4d4d4")
            style.configure("TButton", background="#0a84ff", foreground="#ffffff")

            # 1. 메인 수직 PanedWindow 생성 (상하 분할) - 마우스 드래그로 크기 조절 가능
            pw_vertical = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
            pw_vertical.pack(fill=tk.BOTH, expand=True)

            # 2. 상단 패널 (좌우 분할) - 마우스 드래그로 크기 조절 가능
            pw_horizontal = ttk.PanedWindow(pw_vertical, orient=tk.HORIZONTAL)
            pw_vertical.add(pw_horizontal, weight=3)

            # 상단 좌측 패널 - 이미지 캔버스
            frame_left = tk.Frame(pw_horizontal, bg="#1f2330", relief=tk.SUNKEN, bd=1)
            pw_horizontal.add(frame_left, weight=3)
            self.create_left_panel(frame_left)

            # 상단 우측 패널 - 탭 패널
            frame_right = tk.Frame(pw_horizontal, bg="#1f2330", relief=tk.SUNKEN, bd=1)
            pw_horizontal.add(frame_right, weight=1)
            self.create_right_panel(frame_right)

            # 3. 하단 패널 (전체 너비) - 로그 및 상태 정보
            frame_bottom = tk.Frame(pw_vertical, bg="#181a24", relief=tk.SUNKEN, bd=1, height=50)
            pw_vertical.add(frame_bottom, weight=1)
            self.create_bottom_frame(frame_bottom)

        def create_left_panel(self, frame_left: tk.Frame):
            self.view_frame = ViewFrame(frame_left)

        def create_right_panel(self, frame_right: tk.Frame):            
            self.notebook = ttk.Notebook(frame_right)
            self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Setting 탭
            recipe_frame = RecipeFrame(self.notebook, current_user=self.current_user)
            self.notebook.add(recipe_frame, text="Recipe")
            
            # Recipe 탭
            setting_frame = tk.Frame(self.notebook, bg="#1f2330")
            self.notebook.add(setting_frame, text="Setting")
            tk.Label(setting_frame, text="Setting Area", bg="#1f2330", fg="#d4d4d4").pack(padx=10, pady=10)

        # bottom frame 생성
        def create_bottom_frame(self, bottom_frame: tk.Frame):
            # 1. 하단 패널에 로그 탭 추가
            notebook = ttk.Notebook(bottom_frame)
            notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Info Log 탭
            info_log_frame = tk.Frame(notebook, bg="#1f2330")
            notebook.add(info_log_frame, text="Info Log")
            
            # Warning Log 탭
            war_log_frame = tk.Frame(notebook, bg="#1f2330")
            notebook.add(war_log_frame, text="Warning Log")
            
            # Error Log 탭
            err_log_frame = tk.Frame(notebook, bg="#1f2330")
            notebook.add(err_log_frame, text="Error Log")

            # 2. 상태 label, 상태 메시지, 라이선스 버튼, 버전 정보 label 생성
            self.status_label = tk.Label(bottom_frame, text="상태:", bg="#181a24", fg="#d4d4d4", font=("Arial", 9))
            self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
            
            self.status_message = tk.Label(bottom_frame, text="준비 완료", bg="#181a24", fg="#d4d4d4", 
                                          font=("Arial", 9), anchor="w")
            self.status_message.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
            
            self.version_label = tk.Label(bottom_frame, text=self.VERSION_INFO, bg="#181a24", fg="#d4d4d4",
                                         font=("Arial", 9))
            self.version_label.pack(side=tk.RIGHT, padx=10, pady=5)
            
            self.license_button = tk.Button(bottom_frame, text="라이선스", bg="#0a84ff", fg="#ffffff",
                                           font=("Arial", 8), padx=5, pady=2, relief=tk.FLAT)
            self.license_button.pack(side=tk.RIGHT, padx=5, pady=3)
            self.license_button.config(command=self.show_license_info)
            
            self.login_button = tk.Button(bottom_frame, text="Log In", bg="#0a84ff", fg="#ffffff",
                                        font=("Arial", 8), padx=5, pady=2, relief=tk.FLAT)
            self.login_button.pack(side=tk.RIGHT, padx=5, pady=3)
            self.login_button.config(command=self._show_login_dialog)

        def _show_login_dialog(self) -> None:
            """로그인 다이얼로그 표시"""
            login_window = tk.Toplevel(self.root)
            login_window.title("로그인")
            login_window.geometry("300x170")
            login_window.resizable(False, False)
            
            ttk.Label(login_window, text="사용자 ID:").pack(pady=5)
            username_var = tk.StringVar()
            username_var.set("admin")  # 기본값 설정 (선택 사항)
            username_entry = ttk.Entry(login_window, textvariable=username_var, width=25)
            username_entry.pack(pady=5)
            
            ttk.Label(login_window, text="비밀번호:").pack(pady=5)
            password_var = tk.StringVar()
            password_var.set("admin")  # 기본값 설정 (선택 사항)
            password_entry = ttk.Entry(login_window, textvariable=password_var, width=25, show="*")
            password_entry.pack(pady=5)
            
            def on_login() -> None:
                username = username_var.get()
                password = password_var.get()
                user_manager = UserManager.load_or_create_from_yaml("user_info.yaml")
                if user_manager.authenticate(username, password):
                    self.update_user(user_manager.current_user)
                    login_window.destroy()
                else:
                    from tkinter import messagebox
                    messagebox.showerror("로그인 실패", "사용자 ID 또는 비밀번호를 다시 확인하세요.")
            
            login_button = ttk.Button(login_window, text="로그인", command=on_login)
            login_button.pack(pady=10)
            
            login_window.transient(self.root)
            login_window.grab_set()
            self.root.wait_window(login_window)
        
        def update_user(self, user: User) -> None:
            self.current_user = user
            self.root.title(f"VisInsp - (권한: {user.access_level} - {user.full_name})")

        def show_license_info(self):
            # 라이선스 정보 메시지 박스 표시
            # notice.txt 파일에서 라이선스 정보를 읽어와서 표시
            try:
                with open("notice.txt", "r") as f:
                    license_info = f.read()
                messagebox.showinfo("라이선스 정보", license_info)
            except Exception as e:
                messagebox.showerror("오류", f"라이선스 정보를 불러오는 중 오류가 발생했습니다: {e}")

class ViewFrame(tk.Frame):
    def __init__(self, parent, cameras: Dict[str, str] = None):
        super().__init__(parent, bg="#1f2330")
        self.pack(fill=tk.BOTH, expand=True)

        if cameras is not None:
            self.cameras = cameras
        else:
            self.load_cameras("cameras.yaml")  # cameras.yaml 파일에서 카메라 정보 로드

        # 1. top frame 생성 하고
        # 그 안에 Open Image, Save Image 버튼과 카메라 선택 콤보박스, Live 버튼 그리고 roi_btn_frame 생성, 이미지상에 마우스 픽셀 위치 및 픽셀값 표시하는 label 추가
        # 2. roi_btn_frame 안에 ROI 추가, ROI 삭제 버튼 생성
        # 3. 이미지 캔버스 생성

        top_frame = tk.Frame(self, bg="#1f2330")
        top_frame.pack(fill=tk.X, padx=5, pady=0)
        open_button = tk.Button(top_frame, text="Open Image", bg="#0a84ff", fg="#ffffff", font=("Arial", 9), padx=5, pady=0)
        open_button.pack(side=tk.LEFT, padx=5)
        save_button = tk.Button(top_frame, text="Save Image", bg="#0a84ff", fg="#ffffff", font=("Arial", 9), padx=5, pady=0)
        save_button.pack(side=tk.LEFT, padx=5)
        cameras_combo = ttk.Combobox(top_frame, values=list(self.cameras.keys()), state="readonly", font=("Arial", 9))
        cameras_combo.pack(side=tk.LEFT, padx=5)
        cameras_combo.current(0)
        live_button = tk.Button(top_frame, text="Live", bg="#0a84ff", fg="#ffffff", font=("Arial", 9), padx=5, pady=0)
        live_button.pack(side=tk.LEFT, padx=5)
        roi_btn_frame = tk.Frame(top_frame, bg="#1f2330")
        roi_btn_frame.pack(side=tk.LEFT, padx=20)
        self.create_roi_buttons(roi_btn_frame)

        self.canvas = tk.Canvas(self, bg="#000000")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

    def create_roi_buttons(self, frame: tk.Frame):
        # 1. top frame 생성, 그 안에 size, ↑, move 버튼 생성
        top_frame = tk.Frame(frame, bg="#1f2330")
        top_frame.pack(fill=tk.X)
        size_button = tk.Button(top_frame, text="Size", bg="#0a84ff", fg="#ffffff", font=("Arial", 9), padx=0, pady=0, width=4, height=1)
        size_button.pack(side=tk.LEFT, padx=0)
        up_button = tk.Button(top_frame, text="↑", bg="#0a84ff", fg="#ffffff", font=("Arial", 9), padx=0, pady=0, width=4, height=1)
        up_button.pack(side=tk.LEFT, padx=0)
        move_button = tk.Button(top_frame, text="Move", bg="#0a84ff", fg="#ffffff", font=("Arial", 9), padx=0, pady=0, width=4, height=1)
        move_button.pack(side=tk.LEFT, padx=0)
        # 2. bottom frame 생성, 그 안에 ↓, ←, → 버튼, 픽셀 정보 라벨 생성
        bottom_frame = tk.Frame(frame, bg="#1f2330")
        bottom_frame.pack(fill=tk.X, pady=0)
        left_button = tk.Button(bottom_frame, text="←", bg="#0a84ff", fg="#ffffff", font=("Arial", 9), padx=0, pady=0, width=4, height=1)
        left_button.pack(side=tk.LEFT, padx=0)
        down_button = tk.Button(bottom_frame, text="↓", bg="#0a84ff", fg="#ffffff", font=("Arial", 9), padx=0, pady=0, width=4, height=1)
        down_button.pack(side=tk.LEFT, padx=0)
        right_button = tk.Button(bottom_frame, text="→", bg="#0a84ff", fg="#ffffff", font=("Arial", 9), padx=0, pady=0, width=4, height=1)
        right_button.pack(side=tk.LEFT, padx=0)
        
        self.pixel_info_label = tk.Label(bottom_frame, text="픽셀 위치: (x, y) | 픽셀값: (R, G, B)", bg="#1f2330", fg="#d4d4d4", font=("Arial", 9))
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

class RecipeFrame(tk.Frame):
    def __init__(self, parent, current_user: User, yaml_path: str = "params_example.yaml"):
        super().__init__(parent, bg="#1f2330")
        self.current_user = current_user
        self.yaml_path = yaml_path
        self.manager = None
        self.form = None

        self._build_ui()

    def _build_ui(self):
        header = tk.Label(self, text="Recipe", bg="#1f2330", fg="#d4d4d4", font=("Arial", 12, "bold"))
        header.pack(anchor=tk.W, padx=10, pady=(10, 5))

        content_frame = tk.Frame(self, bg="#1f2330")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        try:
            yaml_path = Path(__file__).resolve().parent / self.yaml_path
            self.manager = ParameterManager.load_yaml(str(yaml_path))
            self.form = ParameterForm(content_frame, self.manager, current_user=self.current_user)
            self.form.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            error_label = tk.Label(content_frame, text=f"설정 파일을 불러오는 중 오류가 발생했습니다:\n{e}",
                                   bg="#1f2330", fg="#f28779", font=("Arial", 10), justify=tk.LEFT)
            error_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            return

        button_frame = tk.Frame(self, bg="#1f2330")
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        apply_button = tk.Button(button_frame, text="적용", bg="#0a84ff", fg="#ffffff", font=("Arial", 9), command=self.apply_settings)
        apply_button.pack(side=tk.RIGHT, padx=5)

        save_button = tk.Button(button_frame, text="저장", bg="#0a84ff", fg="#ffffff", font=("Arial", 9), command=self.save_settings)
        save_button.pack(side=tk.RIGHT)

    def apply_settings(self):
        if self.form is None:
            return
        try:
            self.form.apply()
            messagebox.showinfo("적용 완료", "설정이 적용되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"설정을 적용하는 중 오류가 발생했습니다: {e}")

    def save_settings(self):
        if self.form is None or self.manager is None:
            return
        try:
            self.form.apply()
            yaml_path = Path(__file__).resolve().parent / self.yaml_path
            self.manager.save_yaml(str(yaml_path))
            messagebox.showinfo("저장 완료", f"설정이 {self.yaml_path}에 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"설정을 저장하는 중 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MainFrame(root)
    root.mainloop()

