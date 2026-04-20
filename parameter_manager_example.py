import pathlib
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from ParameManager import ParameterForm, ParameterManager, User, UserManager

def main() -> None:
    current_user: Optional[User] = User()

    root = tk.Tk()
    root.title(f"파라미터 매니저 예제 - (권한: {current_user.access_level} - {current_user.full_name})")

    base_dir = pathlib.Path(__file__).resolve().parent
    schema_path = base_dir / "params_example.yaml"
    save_path = base_dir / "params_example_saved.yaml"

    manager = ParameterManager.load_yaml(str(schema_path))

    form = ParameterForm(root, manager, current_user=current_user)
    form.pack(fill="x", padx=12, pady=12)

    button_frame = tk.Frame(root)
    button_frame.pack(fill="x", padx=12, pady=(0, 12))

    def on_apply() -> None:
        form.apply()
        manager.save_yaml(str(save_path))
        messagebox.showinfo("저장 완료", f"파라미터를 {save_path.name}에 저장했습니다.")

    save_button = tk.Button(button_frame, text="저장", command=on_apply)
    save_button.pack(side="right")

    def _show_login_dialog():
        """로그인 다이얼로그 표시"""
        login_window = tk.Toplevel(root)
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
        password_var.set("ekffur")  # 기본값 설정 (선택 사항)
        password_entry = ttk.Entry(login_window, textvariable=password_var, width=25, show="*")
        password_entry.pack(pady=5)

        def on_login() -> None:
            nonlocal username_var, password_var, login_window
            username = username_var.get()
            password = password_var.get()
            user_manager = UserManager.load_or_create_from_yaml("user_info.yaml")
            if user_manager.authenticate(username, password):
                set_user(user_manager.current_user)
                login_window.destroy()
            else:
                from tkinter import messagebox
                messagebox.showerror("로그인 실패", "사용자 ID 또는 비밀번호를 다시 확인하세요.")
        
        login_button = ttk.Button(login_window, text="로그인", command=on_login)
        login_button.pack(pady=10)
        
        login_window.transient(root)
        login_window.grab_set() 
        root.wait_window(login_window)

    def set_user(user: User) -> None:
        nonlocal current_user, root, form
        current_user = user
        form.update_user(current_user)
        root.title(f"파라미터 매니저 예제 - (권한: {current_user.access_level} - {current_user.full_name})")

    login_button = tk.Button(button_frame, text="로그인", command=_show_login_dialog)
    login_button.pack(side="right")

    root.mainloop()


if __name__ == "__main__":
    main()
    
