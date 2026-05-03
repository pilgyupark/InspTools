import tkinter as tk
from tkinter import messagebox, ttk
import yaml
import hashlib
from typing import Optional

# --- PyYAML Customization (중괄호 블록 포맷 유지) ---
class FlowDict(dict):
    """YAML 저장 시 { } 한 줄 형식을 강제하기 위한 클래스"""
    pass

def flow_dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data, flow_style=True)

yaml.add_representer(FlowDict, flow_dict_representer)

def prepare_data_for_save(data):
    """저장 전 params 항목들을 FlowDict로 변환"""
    if isinstance(data, dict):
        if 'id' in data and 'value' in data:
            return FlowDict({k: prepare_data_for_save(v) for k, v in data.items()})
        return {k: prepare_data_for_save(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [prepare_data_for_save(i) for i in data]
    return data

# --- 메인 애플리케이션 ---
class TreeConfigEditor(ttk.Frame):
    def __init__(self, parent, full_config: Optional[dict]=None, auth_level: int=4, config_path: str = "Setting/system_config.yaml"):
        super().__init__(parent)
        self.pack(expand=True, fill=tk.BOTH)
        
        self.full_config = full_config
        self.config_data = full_config['system_config'] if full_config else None
        self.current_auth_level = auth_level
        self.config_path = config_path
        self.data_map = {}
        if self.full_config is None:
            self.load_data()
        self.build_main_ui()

    def load_data(self):
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.full_config = yaml.load(f, Loader=yaml.FullLoader)
            self.config_data = self.full_config['system_config']

    def save_data(self):
        try:
            save_ready = prepare_data_for_save(self.full_config)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(save_ready, f, allow_unicode=True, sort_keys=False, 
                          default_flow_style=False, width=1000)
            messagebox.showinfo("저장 완료", "설정 파일이 성공적으로 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("저장 실패", f"오류 발생: {e}")

    def build_main_ui(self):
        # 상단 헤더
        header = ttk.Frame(self)
        header.pack(fill=tk.X)
        
        ttk.Label(header, text=f"Lv.{self.current_auth_level} 권한으로 접속 중").pack(side=tk.LEFT, padx=20)
        
        ttk.Button(header, text="전체 저장 (Save All)", command=self.save_data, 
                   style="Accent.TButton").pack(side=tk.RIGHT, padx=20)

        # 좌우 분할 (TreeView | Content)
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # 1. 왼쪽 TreeView 영역
        self.tree_frame = ttk.Frame(self.paned)
        self.paned.add(self.tree_frame, weight=1)
        
        self.tree = ttk.Treeview(self.tree_frame, selectmode="browse")
        self.tree.pack(expand=True, fill=tk.BOTH)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # 2. 오른쪽 편집 영역 (스크롤 가능하도록 구성)
        self.content_canvas = tk.Canvas(self.paned, bg="#282c34")
        self.v_scroll = ttk.Scrollbar(self.paned, orient="vertical", command=self.content_canvas.yview)
        self.edit_frame = ttk.Frame(self.content_canvas)
        
        self.edit_frame.bind("<Configure>", lambda e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all")))
        self.content_canvas.create_window((0, 0), window=self.edit_frame, anchor="nw")
        self.content_canvas.configure(yscrollcommand=self.v_scroll.set)
        
        self.paned.add(self.content_canvas, weight=4)
        
        self.populate_tree()

    def populate_tree(self):
        """데이터를 순회하며 트리를 구성합니다."""
        self.tree.delete(*self.tree.get_children())
        for section in self.config_data:
            if section.get('auth_level', 0) <= self.current_auth_level:
                # 섹션 노드 추가
                sec_node = self.tree.insert("", "end", text=section['label'], open=True)
                self.data_map[sec_node] = section
                self._add_sub_groups(sec_node, section)

    def _add_sub_groups(self, parent_node, data):
        """재귀적으로 하위 그룹을 트리에 추가합니다."""
        if 'groups' in data:
            for group in data['groups']:
                if group.get('auth_level', 0) <= self.current_auth_level:
                    group_node = self.tree.insert(parent_node, "end", text=group['label'])
                    self.data_map[group_node] = group
                    self._add_sub_groups(group_node, group)

    def on_tree_select(self, event):
        """트리 항목 선택 시 해당 항목의 파라미터와 기능을 렌더링"""
        selected_id = self.tree.focus()
        if not selected_id: return
        
        target_data = self.data_map.get(selected_id)
        
        # 기존 화면 초기화
        for widget in self.edit_frame.winfo_children():
            widget.destroy()

        if target_data:
            # 제목 표시
            title = ttk.Label(self.edit_frame, text=f"■ {target_data['label']}", 
                             font=("Malgun Gothic", 14, "bold"))
            title.pack(anchor="w", padx=10)
            
            # 하위 항목 렌더링 (파라미터 및 버튼)
            self.render_editor(self.edit_frame, target_data)

    def render_editor(self, parent, data):
        # 1. Functions 버튼들
        if 'functions' in data:
            btn_frame = ttk.LabelFrame(parent, text="Available Functions", padding=10)
            btn_frame.pack(fill=tk.X, padx=10, pady=5)
            for func in data['functions']:
                if func.get('auth_level', 0) <= self.current_auth_level:
                    # 람다 캡처 기법 사용
                    ttk.Button(btn_frame, text=f"▶ {func['label']}", 
                              command=lambda f=func: self.execute_function(f),
                              style="Accent.TButton").pack(side=tk.LEFT, padx=5)

        # 2. Parameters 위젯들
        if 'params' in data:
            param_frame = ttk.LabelFrame(parent, text="Parameters", padding=10)
            param_frame.pack(fill=tk.X, padx=10, pady=5)
            for p in data['params']:
                if p.get('auth_level', 0) <= self.current_auth_level:
                    if p.get('visibility') == 'hidden':
                        continue
                    self.create_param_widget(param_frame, p)

    def create_param_widget(self, parent, param):
        f = ttk.Frame(parent)
        f.pack(fill=tk.X, pady=3)
        
        lbl = ttk.Label(f, text=param['label'], width=30, anchor="w")
        lbl.pack(side=tk.LEFT)
        
        ptype = param.get('type')
        val = param.get('value')
        
        if ptype == "bool":
            var = tk.BooleanVar(value=val)
            ttk.Checkbutton(f, variable=var, command=lambda: param.update({'value': var.get()})).pack(side=tk.LEFT)
        elif ptype == "choice":
            w = ttk.Combobox(f, values=param.get('options', []))
            w.set(val)
            w.bind("<<ComboboxSelected>>", lambda e: param.update({'value': w.get()}))
            w.pack(side=tk.LEFT, fill=tk.X, expand=True)
        elif ptype in ["int", "float"]:
            w = ttk.Spinbox(f, from_=param.get('min', -9999), to=param.get('max', 9999))
            w.set(val)
            w.bind("<FocusOut>", lambda e: param.update({'value': float(w.get()) if ptype=="float" else int(w.get())}))
            w.pack(side=tk.LEFT, fill=tk.X, expand=True)
        else:
            w = ttk.Entry(f)
            w.insert(0, str(val))
            w.bind("<KeyRelease>", lambda e: param.update({'value': w.get()}))
            w.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def execute_function(self, func_data):
        # 현재 화면의 수정된 값들을 포함하여 파라미터 수집
        params = {p['id']: p['value'] for p in func_data.get('params', [])}
        messagebox.showinfo("Function Call", f"ID: {func_data['id']}\nType: {func_data['type']}\nParams: {params}")

    def update_auth_level(self, auth_level):
        self.current_auth_level = auth_level
        self.populate_tree()  # 트리 재구성


# --- 메인 애플리케이션 ---
class ConfigEditorApp:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.load_data()
        
        self.root = tk.Tk()
        self.root.title("InspTools System Config Manager")
        self.root.geometry("1200x800")
        
        self.current_user = "user1"
        self.current_auth_level = 1

        self.tree_editor: TreeConfigEditor = None

        self.build_main_ui()

    def load_data(self):
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.full_config = yaml.load(f, Loader=yaml.FullLoader)
            self.config_data = self.full_config['system_config']

    def build_main_ui(self):
        # 상단 헤더
        header = tk.Frame(self.root, bg="#2c3e50", pady=10)
        header.pack(fill=tk.X)
        
        tk.Label(header, text=f"접속자: {self.current_user} (Lv.{self.current_auth_level})", 
                 fg="white", bg="#2c3e50", font=("Malgun Gothic", 10, "bold")).pack(side=tk.LEFT, padx=20)
        
        tk.Button(header, text="사용자 로그인", command=self.show_login_screen, 
                  bg="#27ae60", fg="white", font=("Malgun Gothic", 10, "bold"), padx=15).pack(side=tk.RIGHT, padx=20)


    def show_login_screen(self):
        self.login_win = tk.Toplevel(self.root)
        self.login_win.title("보안 로그인")
        self.login_win.geometry("350x220")
        self.login_win.grab_set()
        
        tk.Label(self.login_win, text="사용자 ID").pack(pady=5)
        self.ent_id = tk.Entry(self.login_win)
        self.ent_id.insert(0, "admin") # 테스트 편의용
        self.ent_id.pack()
        
        tk.Label(self.login_win, text="비밀번호").pack(pady=5)
        self.ent_pw = tk.Entry(self.login_win, show="*")
        self.ent_pw.insert(0, "admin") # 테스트 편의용
        self.ent_pw.pack()
        
        tk.Button(self.login_win, text="로그인", command=self.attempt_login, 
                  bg="#34495e", fg="white", width=15).pack(pady=20)

    def attempt_login(self):
        uid, upw = self.ent_id.get(), self.ent_pw.get()
        u_hash = hashlib.sha256(upw.encode()).hexdigest()
        
        user_sec = next((s for s in self.config_data if s['id'] == 'user_info'), None)
        if user_sec:
            for g in user_sec.get('groups', []):
                p = {item['id']: item['value'] for item in g['params']}
                if (g['id'] == uid or p.get('full_name') == uid) and p.get('pw_hash') == u_hash:
                    self.current_auth_level = g['auth_level']
                    self.current_user = uid
                    self.login_win.destroy()
                    self.tree_editor = TreeConfigEditor(self.root, full_config=self.full_config, auth_level=self.current_auth_level, config_path=self.config_path)
                    return
        messagebox.showerror("실패", "인증 정보가 올바르지 않습니다.")


if __name__ == "__main__":
    app = ConfigEditorApp("Setting/system_config.yaml")
    app.root.mainloop()