import tkinter as tk
from tkinter import messagebox, ttk

from ViewFrame import ViewFrame
from UserManager import User, UserManager
from RecipeFrame import CameraSettingFrame, NozzleCenterFrame
from TreeConfig import TreeConfigFrame

class MainFrame:
    VERSION_INFO: str = "version 1.7.2"
    def __init__(self, root, require_login: bool = True):
        self.root = root
        self.require_login = require_login
        self.current_user = User()  # 기본 사용자 설정

        self._set_style()
        self._setup_ui()
    
    def _set_style(self):
        style = ttk.Style(self.root)
        style.theme_use("default")

        # --- One Dark Pro 컬러 팔레트 ---
        bg_dark = "#21252b"       # 가장 어두운 배경 (트리뷰, 상태바)
        bg_main = "#282c34"       # 메인 배경 (프레임, 캔버스 배경)
        bg_active = "#3e4452"     # 활성화/호버 배경 (선택된 항목)
        fg_main = "#abb2bf"       # 기본 텍스트 색상 (Grey)
        fg_light = "#ffffff"      # 강조 텍스트 (White)
        fg_disabled = "#5c6370"   # 비활성/주석 글자색 (Grey)
        fg_grey = "#5c6370"       # 스크롤바 바(thumb) 기본 색상
        accent_blue = "#61afef"   # 포인트 컬러 (Blue)
        accent_red = "#e06c75"  # 정지 상태를 위한 붉은 톤
        border_color = "#181a1f"  # 경계선 색상

        # --- 1. 기본 프레임 및 라벨 ---
        style.configure("TFrame", background=bg_main)
        style.configure("TLabel", background=bg_main, foreground=fg_main, font=("Segoe UI", 10))
        
        # --- 2. Notebook (탭 UI) ---
        style.configure("TNotebook", background=bg_dark, borderwidth=0)
        style.configure("TNotebook.Tab", background=bg_dark, foreground=fg_main, padding=[12, 4], borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", bg_main)], foreground=[("selected", accent_blue)])

        # --- 3. PanedWindow (분할창) ---
        style.configure("TPanedwindow", background=border_color)
        style.configure("Sash", background=border_color, sashthickness=4)

        # --- 4. Treeview (계층 구조) ---
        style.configure("Treeview", background=bg_dark, foreground=fg_main, fieldbackground=bg_dark, borderwidth=0, rowheight=25, font=("Segoe UI", 10))
        style.map("Treeview", background=[("selected", bg_active)], foreground=[("selected", accent_blue)])
        # 트리뷰 헤더 (필요시)
        style.configure("Treeview.Heading", background=bg_active, foreground=fg_main, borderwidth=1)

        # --- 5. LabelFrame (그룹 박스) ---
        style.configure("TLabelframe", background=bg_main, foreground=accent_blue, borderwidth=1, relief="ridge")
        style.configure("TLabelframe.Label", background=bg_main, foreground=accent_blue, font=("Segoe UI", 10, "bold"))

        # --- 6. 버튼 (TButton) ---
        style.configure("TButton", background=bg_active, foreground=fg_main, borderwidth=1, font=("Segoe UI", 9), focuscolor=accent_blue)
        style.map("TButton", background=[("active", accent_blue)], foreground=[("active", fg_light)])
        # --- Live 시작 / 정지 (TButton) ---
        style.configure("Live.TButton", background=accent_blue, foreground=fg_light)
        style.map("Live.TButton", background=[("active", "#528bff")])
        style.configure("Stop.TButton", background="#3e4452", foreground="#abb2bf")
        style.map("Stop.TButton", background=[("active", accent_red)], foreground=[("active", fg_light)])

        # --- 7. 엔트리 및 콤보박스 (입력창) ---
        # --- TEntry 스타일 설정 ---
        style.configure("TEntry", fieldbackground=bg_main, foreground=fg_main, insertcolor=fg_main, borderwidth=1, relief="flat")

        # 상태별(map) 스타일 정의
        style.map("TEntry", fieldbackground=[("disabled", bg_dark), ("readonly", bg_dark)], foreground=[("disabled", fg_disabled), ("readonly", fg_disabled)], lightcolor=[("focus", accent_blue)], darkcolor=[("focus", accent_blue)])

        # --- TCombobox 스타일도 Entry와 동일하게 맞춤 ---
        style.configure("TCombobox", fieldbackground=bg_main, foreground=fg_main, background=bg_dark)

        style.map("TCombobox", fieldbackground=[("disabled", bg_dark), ("readonly", bg_dark)], foreground=[("disabled", fg_disabled), ("readonly", fg_disabled)])

        # --- 8. 스크롤바 (TScrollbar) ---
        style.configure("TScrollbar", background=fg_grey, troughcolor=bg_dark, borderwidth=0, arrowcolor=bg_main, relief="flat")
        style.map("TScrollbar", background=[("active", accent_blue), ("pressed", "#528bff")], arrowcolor=[("active", "#ffffff")])
        
        # --- 9. 전역 루트 설정 ---
        self.root.configure(bg=bg_dark)
        
    def _setup_ui(self):
        self.root.title(f"VisInsp - (권한: {self.current_user.access_level} - {self.current_user.full_name})")
        self.root.geometry("1200x750")

        # 1. 메인 수직 PanedWindow 생성 (상하 분할) - 마우스 드래그로 크기 조절 가능
        pw_vertical = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        pw_vertical.pack(fill=tk.BOTH, expand=True)

        # 2. 상단 패널 (좌우 분할) - 마우스 드래그로 크기 조절 가능
        pw_horizontal = ttk.PanedWindow(pw_vertical, orient=tk.HORIZONTAL)
        pw_vertical.add(pw_horizontal, weight=4)

        # 상단 좌측 패널 - 이미지 캔버스
        frame_left = ttk.Frame(pw_horizontal, relief=tk.SUNKEN)
        pw_horizontal.add(frame_left, weight=4)
        self.create_left_panel(frame_left)

        # 상단 우측 패널 - 탭 패널
        frame_right = ttk.Frame(pw_horizontal, relief=tk.SUNKEN)
        pw_horizontal.add(frame_right, weight=1)
        self.create_right_panel(frame_right)

        # 3. 하단 패널 (전체 너비) - 로그 및 상태 정보
        frame_bottom = ttk.Frame(pw_vertical, relief=tk.SUNKEN, height=50)
        pw_vertical.add(frame_bottom, weight=1)
        self.create_bottom_frame(frame_bottom)

    def create_left_panel(self, frame_left: ttk.Frame):
        self.view_frame = ViewFrame(frame_left)

    def create_right_panel(self, frame_right: ttk.Frame):            
        self.notebook = ttk.Notebook(frame_right)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Setting 탭
        self.CameraSetting_frame = CameraSettingFrame(self.notebook, view_frame=self.view_frame, auth_level=self.current_user.auth_level)
        self.notebook.add(self.CameraSetting_frame, text="Camera Setting")
        # Recipe 탭
        self.NozzleCenter_frame = NozzleCenterFrame(self.notebook, view_frame=self.view_frame, auth_level=self.current_user.auth_level)
        self.notebook.add(self.NozzleCenter_frame, text="Nozzle Center")
        # System Config 탭
        self.SystemConfig_frame = TreeConfigFrame(self.notebook, view_frame=self.view_frame, auth_level=self.current_user.auth_level)
        self.notebook.add(self.SystemConfig_frame, text="System Config")

    # bottom frame 생성
    def create_bottom_frame(self, bottom_frame: ttk.Frame):
        # 1. 하단 패널에 로그 탭 추가
        notebook = ttk.Notebook(bottom_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Info Log 탭
        info_log_frame = ttk.Frame(notebook)
        notebook.add(info_log_frame, text="Info Log")
        
        # Warning Log 탭
        war_log_frame = ttk.Frame(notebook)
        notebook.add(war_log_frame, text="Warning Log")
        
        # Error Log 탭
        err_log_frame = ttk.Frame(notebook)
        notebook.add(err_log_frame, text="Error Log")

        # 2. 상태 label, 상태 메시지, 라이선스 버튼, 버전 정보 label 생성
        self.status_label = ttk.Label(bottom_frame, text="상태:")
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.status_message = ttk.Label(bottom_frame, text="준비 완료", anchor="w")
        self.status_message.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        self.version_label = ttk.Label(bottom_frame, text=self.VERSION_INFO)
        self.version_label.pack(side=tk.RIGHT, padx=10, pady=5)
        
        self.license_button = ttk.Button(bottom_frame, text="라이선스")
        self.license_button.pack(side=tk.RIGHT, padx=5, pady=3)
        self.license_button.config(command=self.show_license_info)
        
        self.login_button = ttk.Button(bottom_frame, text="Log In")
        self.login_button.pack(side=tk.RIGHT, padx=5, pady=3)
        self.login_button.config(command=self._show_login_dialog)

    def _show_login_dialog(self) -> None:
        """로그인 다이얼로그 표시"""
        login_window = tk.Toplevel(self.root)
        login_window.title("로그인")
        login_window.geometry("300x170")
        login_window.resizable(False, False)
        login_window.configure(bg="#21252b")
        
        ttk.Label(login_window, style="TLabel", text="사용자 ID:").pack(pady=5)
        username_var = tk.StringVar()
        username_var.set("admin")  # 기본값 설정 (선택 사항)
        username_entry = ttk.Entry(login_window, style="TEntry", textvariable=username_var, width=25)
        username_entry.pack(pady=5)
        
        ttk.Label(login_window, style="TLabel", text="비밀번호:").pack(pady=5)
        password_var = tk.StringVar()
        password_var.set("admin")  # 기본값 설정 (선택 사항)
        password_entry = ttk.Entry(login_window, style="TEntry", textvariable=password_var, width=25, show="*")
        password_entry.pack(pady=5)
        
        def on_login() -> None:
            username = username_var.get()
            password = password_var.get()
            user_manager = UserManager.load_or_create_from_yaml("user_info.yaml")
            if user_manager.authenticate(username, password):
                self.update_auth_level(user_manager.current_user.auth_level)
                login_window.destroy()
            else:
                messagebox.showerror("로그인 실패", "사용자 ID 또는 비밀번호를 다시 확인하세요.")
        
        login_button = ttk.Button(login_window, style="TButton", text="로그인", command=on_login)
        login_button.pack(pady=10)
        
        login_window.transient(self.root)
        login_window.grab_set()
        self.root.wait_window(login_window)
    
    def update_auth_level(self, auth_level: int) -> None:
        self.current_auth_level = auth_level
        self.CameraSetting_frame.update_auth_level(auth_level)
        self.NozzleCenter_frame.update_auth_level(auth_level)
        self.SystemConfig_frame.update_auth_level(auth_level)
        self.root.title(f"VisInsp - (권한: {auth_level})")

    def show_license_info(self):
        # 라이선스 정보 메시지 박스 표시
        # notice.txt 파일에서 라이선스 정보를 읽어와서 표시
        try:
            with open("notice.txt", "r") as f:
                license_info = f.read()
            messagebox.showinfo("라이선스 정보", license_info)
        except Exception as e:
            messagebox.showerror("오류", f"라이선스 정보를 불러오는 중 오류가 발생했습니다: {e}")




if __name__ == "__main__":
    root = tk.Tk()
    app = MainFrame(root)
    root.mainloop()

