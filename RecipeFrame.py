import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path

from ViewFrame import ViewFrame
from ParameManager import ParameterForm, ParameterManager
from UserManager import User

class RecipeFrame(ttk.Frame):
    def __init__(self, parent, view_frame: ViewFrame, current_user: User, yaml_path: str = "params_example.yaml"):
        super().__init__(parent)
        self.current_user = current_user
        self.yaml_path = yaml_path
        self.manager = None
        self.form = None
        self.view_frame = view_frame

        self._build_ui()

    def _build_ui(self):
        header = ttk.Label(self, text="Recipe", font=("", 12, "bold"))
        header.pack(anchor=tk.W, padx=10, pady=(10, 5))

        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        try:
            yaml_path = Path(__file__).resolve().parent / self.yaml_path
            self.manager = ParameterManager.load_yaml(str(yaml_path))
            self.form = ParameterForm(content_frame, self.view_frame, self.manager, current_user=self.current_user)
            self.form.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            error_label = ttk.Label(content_frame, text=f"설정 파일을 불러오는 중 오류가 발생했습니다:\n{e}",
                                   font=("", 10), justify=tk.LEFT)
            error_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            return

        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        apply_button = ttk.Button(button_frame, text="적용", command=self.apply_settings)
        apply_button.pack(side=tk.RIGHT, padx=5)

        save_button = ttk.Button(button_frame, text="저장", command=self.save_settings)
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