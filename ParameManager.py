from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional
import yaml

import tkinter as tk
from tkinter import ttk, filedialog

from UserManager import User, AccessLevel
from ViewFrame import ViewFrame
from Roi import Roi

_SUPPORTED_TYPES = {"string", "int", "float", "bool", "choice", "list", "roi", "img_path", "point"}

@dataclass
class ParameterDefinition:
    name: str
    label: str
    type: str = "string"
    value: Any = None
    min: Optional[float] = None
    max: Optional[float] = None
    options: Optional[List[Any]] = None
    section: Optional[str] = None
    group: Optional[str] = None
    feature: Optional[str] = None
    module: Optional[str] = None
    help_text: Optional[str] = None
    access_level: Optional[str] = None
    visibility: str = "visible"

    def __post_init__(self) -> None:
        self.type = self.type.lower()
        if self.type not in _SUPPORTED_TYPES:
            raise ValueError(f"Unsupported parameter type: {self.type}")

        if self.type == "choice" and not self.options:
            raise ValueError("Choice parameters require an options list")

    def validate(self, value: Any) -> Any:
        if self.type == "bool":
            return self._cast_bool(value)

        if self.type == "int":
            value = int(value)
            self._check_range(value)
            return value

        if self.type == "float":
            value = float(value)
            self._check_range(value)
            return value

        if self.type == "choice":
            if value not in self.options:
                raise ValueError(f"Value for '{self.name}' must be one of {self.options}. Got {value}.")
            return value

        if self.type in {"list", "roi", "point"}:
            return self._parse_list_value(value)

        return str(value)

    def _check_range(self, value: float) -> None:
        if self.min is not None and value < self.min:
            raise ValueError(
                f"Value for '{self.name}' must be >= {self.min}, got {value}."
            )
        if self.max is not None and value > self.max:
            raise ValueError(
                f"Value for '{self.name}' must be <= {self.max}, got {value}."
            )

    def _parse_list_value(self, value: Any) -> List[Any]:
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, str):
            if yaml is not None:
                try:
                    parsed = yaml.safe_load(value)
                except Exception as exc:
                    raise ValueError(
                        f"Cannot parse {value!r} as a list for '{self.name}'"
                    ) from exc
                if isinstance(parsed, (list, tuple)):
                    return list(parsed)
            raise ValueError(
                f"Value for '{self.name}' must be a list, point, or roi. Got {value!r}."
            )
        raise ValueError(
            f"Value for '{self.name}' must be a list, point, or roi. Got {value!r}."
        )

    @staticmethod
    def _cast_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on"}:
                return True
            if lowered in {"0", "false", "no", "off"}:
                return False
        raise ValueError(f"Cannot convert {value!r} to bool")

    def get_unique_id(self) -> str:
        """파라미터의 고유 ID 반환: module:feature:group:section:name"""
        module = self.module or "default"
        feature = self.feature or "default"
        group = self.group or "default"
        section = self.section or "default"
        return f"{module}:{feature}:{group}:{section}:{self.name}"

    def to_dict(self) -> Dict[str, Any]:
        output: Dict[str, Any] = {
            "name": self.name,
            "label": self.label,
            "type": self.type,
            "value": self.value,
        }
        if self.min is not None:
            output["min"] = self.min
        if self.max is not None:
            output["max"] = self.max
        if self.options is not None:
            output["options"] = self.options
        if self.group is not None:
            output["group"] = self.group
        if self.section is not None:
            output["section"] = self.section
        if self.feature is not None:
            output["feature"] = self.feature
        if self.module is not None:
            output["module"] = self.module
        if self.help_text is not None:
            output["help_text"] = self.help_text
        if self.access_level is not None:
            output["access_level"] = self.access_level
        if self.visibility != "visible":
            output["visibility"] = self.visibility
        return output

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParameterDefinition":
        return cls(
            name=data["name"],
            label=data.get("label", data["name"]),
            type=data.get("type", "string"),
            value=data.get("value"),
            min=data.get("min"),
            max=data.get("max"),
            section=data.get("section"),
            options=data.get("options"),
            group=data.get("group"),
            feature=data.get("feature"),
            module=data.get("module"),
            help_text=data.get("help_text"),
            access_level=data.get("access_level"),
            visibility=data.get("visibility", "visible"),
        )

class ParameterManager:
    def __init__(
        self,
        parameters: Optional[Iterable[ParameterDefinition]] = None,
        values: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.parameters: Dict[str, ParameterDefinition] = {}  # 고유 ID -> ParameterDefinition
        self.name_to_unique_id: Dict[str, List[str]] = {}  # name -> [고유 ID, ...]
        self.values: Dict[str, Any] = {}  # 고유 ID -> value

        if parameters is not None:
            for param in parameters:
                unique_id = param.get_unique_id()
                self.parameters[unique_id] = param
                self.values[unique_id] = param.value
                
                # name 기반 검색 매핑
                if param.name not in self.name_to_unique_id:
                    self.name_to_unique_id[param.name] = []
                self.name_to_unique_id[param.name].append(unique_id)

        if values is not None:
            self.update(values)

    def _resolve_id(self, name_or_id: str) -> Optional[str]:
        """name 또는 고유 ID를 고유 ID로 변환. 중복 name의 경우 첫 번째 반환"""
        if name_or_id in self.parameters:
            return name_or_id
        if name_or_id in self.name_to_unique_id:
            return self.name_to_unique_id[name_or_id][0]
        return None

    def get(self, name: str, value: Any = None) -> Any:
        """name 또는 고유 ID로 파라미터 값 조회"""
        unique_id = self._resolve_id(name)
        return self.values.get(unique_id, value) if unique_id else value

    def set(self, name: str, value: Any) -> None:
        """name 또는 고유 ID로 파라미터 값 설정"""
        unique_id = self._resolve_id(name)
        if unique_id is None:
            raise KeyError(f"Unknown parameter: {name}")
        self.values[unique_id] = self.parameters[unique_id].validate(value)

    def get_by_hierarchy(self, module: Optional[str], feature: Optional[str], group: Optional[str], name: str) -> Any:
        """계층 구조를 통해 파라미터 값 조회"""
        unique_id = f"{module or 'default'}:{feature or 'default'}:{group or 'default'}:{name}"
        return self.values.get(unique_id)

    def set_by_hierarchy(self, module: Optional[str], feature: Optional[str], group: Optional[str], name: str, value: Any) -> None:
        """계층 구조를 통해 파라미터 값 설정"""
        unique_id = f"{module or 'default'}:{feature or 'default'}:{group or 'default'}:{name}"
        if unique_id not in self.parameters:
            raise KeyError(f"Unknown parameter: {unique_id}")
        self.values[unique_id] = self.parameters[unique_id].validate(value)

    def get_parameter_by_hierarchy(self, module: Optional[str], feature: Optional[str], group: Optional[str], name: str) -> Optional[ParameterDefinition]:
        """계층 구조를 통해 파라미터 정의 조회"""
        unique_id = f"{module or 'default'}:{feature or 'default'}:{group or 'default'}:{name}"
        return self.parameters.get(unique_id)

    def update(self, values: Dict[str, Any]) -> None:
        """파라미터 값 업데이트"""
        for name, value in values.items():
            unique_id = self._resolve_id(name)
            if unique_id and unique_id in self.parameters:
                self.set(name, value)
            else:
                if name in self.parameters:
                    self.values[name] = value

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.values)

    def iter_definitions(self) -> Iterable[ParameterDefinition]:
        return self.parameters.values()

    def parameter_hierarchy(self) -> Dict[str, Dict[str, Dict[str, Dict[str, List[ParameterDefinition]]]]]:
        """모듈 > 기능 > 그룹 > 섹션 > 파라미터 계층 구조 반환"""
        hierarchy: Dict[str, Dict[str, Dict[str, Dict[str, List[ParameterDefinition]]]]] = {}
        
        for param in self.iter_definitions():
            module = param.module or "기본"
            feature = param.feature or "일반"
            group = param.group or "설정"
            section = param.section or "기본"
            
            if module not in hierarchy:
                hierarchy[module] = {}
            if feature not in hierarchy[module]:
                hierarchy[module][feature] = {}
            if group not in hierarchy[module][feature]:
                hierarchy[module][feature][group] = {}
            if section not in hierarchy[module][feature][group]:
                hierarchy[module][feature][group][section] = []
            
            hierarchy[module][feature][group][section].append(param)
        
        return hierarchy

    def parameter_groups(self) -> Dict[Optional[str], List[ParameterDefinition]]:
        groups: Dict[Optional[str], List[ParameterDefinition]] = {}
        for param in self.iter_definitions():
            groups.setdefault(param.group or "기본", []).append(param)
        return groups

    @staticmethod
    def _flatten_values(values_raw: Any, prefix: Optional[str] = None) -> Dict[str, Any]:
        flattened: Dict[str, Any] = {}
        if isinstance(values_raw, dict):
            for key, value in values_raw.items():
                full_key = f"{prefix}:{key}" if prefix else key
                if isinstance(value, dict):
                    flattened.update(ParameterManager._flatten_values(value, full_key))
                else:
                    flattened[full_key] = value
        return flattened

    def _nested_values(self) -> Dict[str, Any]:
        nested: Dict[str, Any] = {}
        for unique_id, value in self.to_dict().items():
            parts = unique_id.split(":")
            node = nested
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = value
        return nested

    @classmethod
    def load_yaml(cls, path: str) -> "ParameterManager":
        with open(path, "r", encoding="utf-8") as file:
            document = yaml.safe_load(file) or {}

        parameters = [
            ParameterDefinition.from_dict(item)
            for item in document.get("parameters", [])
        ]
        values_raw = document.get("values", {})
        manager = cls(parameters=parameters, values={})

        values_flat = cls._flatten_values(values_raw)
        if not values_flat:
            if isinstance(values_raw, dict):
                values_flat = {k: v for k, v in values_raw.items()}

        for key, value in values_flat.items():
            if key in manager.parameters:
                manager.values[key] = value
            else:
                if key in manager.name_to_unique_id and manager.name_to_unique_id[key]:
                    unique_id = manager.name_to_unique_id[key][0]
                    manager.values[unique_id] = value

        for unique_id, param in manager.parameters.items():
            if unique_id in manager.values and param.type in {"list", "roi", "point"}:
                raw_value = manager.values[unique_id]
                if isinstance(raw_value, str):
                    try:
                        parsed = yaml.safe_load(raw_value)
                    except Exception:
                        parsed = None
                    if isinstance(parsed, (list, tuple)):
                        manager.values[unique_id] = list(parsed)
        
        return manager

    def save_yaml(self, path: str, include_schema: bool = True) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        document: Dict[str, Any] = {}
        if include_schema:
            document["parameters"] = [param.to_dict() for param in self.iter_definitions()]
        document["values"] = self._nested_values()

        class FlowStyleDumper(yaml.SafeDumper):
            pass

        def represent_sequence(dumper, sequence):
            if any(isinstance(item, dict) for item in sequence):
                return dumper.represent_sequence('tag:yaml.org,2002:seq', sequence, flow_style=False)
            return dumper.represent_sequence('tag:yaml.org,2002:seq', sequence, flow_style=True)

        def represent_mapping(dumper, mapping):
            return dumper.represent_mapping('tag:yaml.org,2002:map', mapping, flow_style=False)

        FlowStyleDumper.add_representer(list, represent_sequence)
        FlowStyleDumper.add_representer(dict, represent_mapping)

        with open(path, "w", encoding="utf-8") as file:
            yaml.dump(document, file, sort_keys=False, allow_unicode=True, default_flow_style=False, Dumper=FlowStyleDumper,)

class ParameterForm:
    def __init__(self, master: tk.Misc, view_frame:ViewFrame, manager: ParameterManager, on_apply: Optional[callable] = None,
        use_hierarchy: bool = True, current_user: Optional["User"] = None, ) -> None:
        self.master = master
        self.view_frame = view_frame
        self.manager = manager
        self.on_apply = on_apply
        self.variables: Dict[str, tk.Variable] = {}
        self.use_hierarchy = use_hierarchy
        self.frame = ttk.Frame(self.master)
        self.widgets_info: Dict[str, Dict[str, Any]] = {}
        self.current_user = current_user
        
        self._build_form()

    def _build_form(self) -> None:
        if self.use_hierarchy and self._has_hierarchy():
            self._build_hierarchical_form()
        else:
            self._build_flat_form()
    
    def _has_hierarchy(self) -> bool:
        for param in self.manager.iter_definitions():
            if param.module or param.feature:
                return True
        return False

    def _build_hierarchical_form(self) -> None:
        hierarchy = self.manager.parameter_hierarchy()

        paned = ttk.PanedWindow(self.frame, orient="horizontal")
        paned.pack(fill="both", expand=True)

        tree_frame = ttk.Frame(paned)
        detail_frame = ttk.Frame(paned)
        paned.add(tree_frame, weight=1)
        paned.add(detail_frame, weight=4)

        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, side="left")
        tree_scrollbar.configure(command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)

        self.tree_paths: Dict[str, List[str]] = {}
        for module_name, features in hierarchy.items():
            module_id = self.tree.insert("", "end", text=module_name, open=True)
            self.tree_paths[module_id] = [module_name]
            for feature_name, groups in features.items():
                feature_id = self.tree.insert(module_id, "end", text=feature_name, open=True)
                self.tree_paths[feature_id] = [module_name, feature_name]
                for group_name, sections in groups.items():
                    group_id = self.tree.insert(feature_id, "end", text=group_name, open=True)
                    self.tree_paths[group_id] = [module_name, feature_name, group_name]
                    for section_name in sections.keys():
                        section_id = self.tree.insert(group_id, "end", text=section_name, open=True)
                        self.tree_paths[section_id] = [module_name, feature_name, group_name, section_name]

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        self.detail_canvas = tk.Canvas(detail_frame, borderwidth=0, highlightthickness=0, bg="#282c34")
        detail_hscrollbar = ttk.Scrollbar(detail_frame, orient="horizontal")
        detail_vscrollbar = ttk.Scrollbar(detail_frame, orient="vertical")
        detail_hscrollbar.pack(side="bottom", fill="x")
        detail_vscrollbar.pack(side="right", fill="y")
        self.detail_canvas.pack(side="left", fill="both", expand=True)
        detail_hscrollbar.configure(command=self.detail_canvas.xview)
        detail_vscrollbar.configure(command=self.detail_canvas.yview)
        self.detail_canvas.configure(xscrollcommand=detail_hscrollbar.set, yscrollcommand=detail_vscrollbar.set)

        self.detail_inner = ttk.Frame(self.detail_canvas)
        self.detail_canvas.create_window((0, 0), window=self.detail_inner, anchor="nw")
        self.detail_inner.bind("<Configure>", lambda event: self.detail_canvas.configure(scrollregion=self.detail_canvas.bbox("all")),)

        self.section_frames: Dict[str, ttk.Frame] = {}
        self.section_frame_keys: List[str] = []
        for module_name, features in hierarchy.items():
            for feature_name, groups in features.items():
                for group_name, sections in groups.items():
                    for section_name, params in sections.items():
                        section_key = ":".join([module_name, feature_name, group_name, section_name])
                        section_frame = ttk.LabelFrame(self.detail_inner, text=f"{module_name} / {feature_name} / {group_name} / {section_name}",)
                        self.section_frames[section_key] = section_frame
                        self.section_frame_keys.append(section_key)
                        for param in params:
                            self._add_parameter_row(section_frame, param)

        first_section = next((item_id for item_id, path in self.tree_paths.items() if len(path) == 4), None,)
        if first_section:
            self.tree.selection_set(first_section)
            self.tree.focus(first_section)
            self._show_frames_for_path(self.tree_paths[first_section])

    def _build_flat_form(self) -> None:
        for group_name, params in self.manager.parameter_groups().items():
            section = ttk.LabelFrame(self.frame, text=group_name)
            section.pack(fill="x", padx=10, pady=6, anchor="n")
            for param in params:
                self._add_parameter_row(section, param)

    def _on_tree_select(self, event: tk.Event) -> None:
        item_id = self.tree.focus()
        path = self.tree_paths.get(item_id)
        if not path:
            return

        self._show_frames_for_path(path)

    def _add_parameter_row(self, parent: ttk.Widget, param: ParameterDefinition) -> None:
        current_level = self._get_current_access_level()
        unique_id = param.get_unique_id()
        
        if param.visibility == "hidden":
            if not current_level or not current_level.has_access(param.access_level):
                return
        
        row = ttk.Frame(parent)
        row.pack(fill="x", padx=8, pady=4)

        label = ttk.Label(row, text=param.label, width=20, anchor="w")
        label.pack(side="left", padx=(0, 10))

        variable = self._create_variable(param)
        widget = self._create_widget(row, param, variable)
        widget.pack(side="left", fill="x", expand=True)

        self.variables[unique_id] = variable
        
        has_access = current_level and current_level.has_access(param.access_level)
        
        if not has_access:
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    child.config(state="disabled")
            else:
                widget.config(state="readonly" if hasattr(widget, "state") else "disabled")

        if param.help_text:
            help_label = ttk.Label(row, text=param.help_text, font=("", 8))
            help_label.pack(side="left", padx=(10, 0))

        self.widgets_info[unique_id] = {"widget": widget, "variable": variable, "has_access": has_access, "access_level": param.access_level,}

    def _show_frames_for_path(self, path: List[str]) -> None:
        for section_key in self.section_frame_keys:
            frame = self.section_frames.get(section_key)
            if frame is not None:
                frame.pack_forget()

        prefix = ":".join(path)
        matched = False
        for section_key in self.section_frame_keys:
            if section_key.startswith(prefix):
                frame = self.section_frames[section_key]
                frame.pack(fill="x", padx=10, pady=6, anchor="n")
                matched = True

        if matched:
            self.detail_canvas.update_idletasks()
            self.detail_canvas.yview_moveto(0)

    def _get_current_access_level(self) -> Optional[AccessLevel]:
        return AccessLevel.from_string(self.current_user.access_level)

    def _create_variable(self, param: ParameterDefinition) -> tk.Variable:
        value = self.manager.get(param.get_unique_id(), param.value)
        if param.type == "bool":
            return tk.BooleanVar(value=bool(value))
        if param.type == "int":
            return tk.IntVar(value=int(value) if value is not None else 0)
        if param.type == "float":
            return tk.DoubleVar(value=float(value) if value is not None else 0.0)
        return tk.StringVar(value="" if value is None else str(value))

    def _create_widget(self, parent: ttk.Widget, param: ParameterDefinition, variable: tk.Variable,) -> ttk.Widget:
        if param.type == "bool":
            return ttk.Checkbutton(parent, variable=variable)

        if param.type == "choice":
            combobox = ttk.Combobox(parent, textvariable=variable, values=param.options or [], state="readonly", width=20,)
            if param.value is not None:
                variable.set(param.value)
            return combobox

        if param.type in {"int", "float"} and param.min is not None and param.max is not None:
            increment = 1 if param.type == "int" else 0.1
            return ttk.Spinbox(parent, textvariable=variable, from_=param.min, to=param.max, increment=increment, width=15,)

        if param.type == "img_path":
            return self._create_img_file_widget(parent, param, variable)
        
        if param.type == "roi":
            return self._create_roi_widget(parent, param, variable)

        return ttk.Entry(parent, textvariable=variable, width=25)

    def _create_img_file_widget(self, parent: ttk.Widget, param: ParameterDefinition, variable: tk.Variable,) -> ttk.Frame:
        container = ttk.Frame(parent)
        entry = ttk.Entry(container, textvariable=variable, width=20)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        def on_browse() -> None:
            current_path = variable.get()
            initial_dir = str(os.path.dirname(current_path)) if current_path else "./"
            if not os.path.isdir(initial_dir):
                initial_dir = "./"

            file_types = self._parse_file_filters(param.options or [])
            file_path = filedialog.askopenfilename(
                initialdir=initial_dir,
                filetypes=file_types or [("All files", "*.*")],
            )
            if file_path:
                variable.set(file_path)
                on_open()
        
        def on_open() -> None:
            file_path = variable.get()
            if file_path:
                self.view_frame.open_image(file_path)

        def on_save() -> None:
            file_path = variable.get()
            if file_path:
                self.view_frame.save_image(file_path)

        button = ttk.Button(container, text="저장", command=on_save, width=8)
        button.pack(side="right")
        button = ttk.Button(container, text="열기", command=on_open, width=8)
        button.pack(side="right")
        button = ttk.Button(container, text="찾기", command=on_browse, width=8)
        button.pack(side="right")
        return container

    def _create_roi_widget(self, parent: ttk.Widget, param: ParameterDefinition, variable: tk.Variable,) -> ttk.Frame:
        container = ttk.Frame(parent)
        entry = ttk.Entry(container, textvariable=variable, width=20)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        def FocusIn(event=None) -> None:
            try:
                coords = eval(variable.get())
                self.view_frame.update_roi_coords(coords)
            except Exception as e:
                print(e)

        def FocusOut(event=None) -> None:
            try:
                self.view_frame.cur_roi.set_mode(Roi.MODE_IDLE)
            except Exception as e:
                print(e)

        def Return(event=None) -> None:
            try:
                coords = eval(variable.get())
                self.view_frame.update_roi_coords(coords)
            except Exception as e:
                print(e)

        def on_enter() -> None:
            try:
                coords = self.view_frame.get_roi_coords()
                variable.set(str(coords))
            except Exception as e:
                print(e)

        button = ttk.Button(container, text="입력", command=on_enter, width=8)
        button.pack(side="right")

        entry.bind("<FocusIn>", FocusIn)
        entry.bind("<FocusOut>", FocusOut)
        entry.bind("<Return>", Return)
        return container

    def update_user(self, user: User) -> None:
        self.current_user = user
        current_level = self._get_current_access_level()
        
        for unique_id, info in self.widgets_info.items():
            param = self.manager.parameters.get(unique_id)
            if not param:
                continue
            
            has_access = current_level and current_level.has_access(param.access_level)
            widget = info["widget"]
            
            if not has_access:
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        child.config(state="disabled")
                else:
                    widget.config(state="readonly" if hasattr(widget, "state") else "disabled")
            else:
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        child.config(state="normal")
                else:
                    widget.config(state="normal")

    @staticmethod
    def _parse_file_filters(options: List[Any]) -> List[tuple]:
        file_types = []
        for option in options:
            if isinstance(option, str):
                ext = option.strip().lstrip("*").upper()
                label = f"{ext} files" if ext else "All files"
                file_types.append((label, option))
        return file_types

    def apply(self) -> None:
        current_level = self._get_current_access_level()
        for unique_id, variable in self.variables.items():
            param = self.manager.parameters.get(unique_id)
            if param and current_level:
                has_access = current_level.has_access(param.access_level)
                if has_access:
                    value = variable.get()
                    self.manager.values[unique_id] = param.validate(value)
        if self.on_apply is not None:
            self.on_apply(self.manager)

    def pack(self, **kwargs: Any) -> None:
        self.frame.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        self.frame.grid(**kwargs)


if __name__ == "__main__":
    import pathlib
    from tkinter import messagebox
    
    root = tk.Tk()
    root.title("파라미터 매니저 예제 - 계층형 구조")
    root.geometry("600x500")

    current_user: Optional[User] = User.from_dict({"username": "admin", "password_hash": User._hash_password("admin"), "access_level": "developer", "full_name": "Administrator"})

    config_path = pathlib.Path(__file__).with_name("params_example.yaml")
    if not config_path.exists():
        print("params_example.yaml 파일이 없습니다.")
    else:
        manager = ParameterManager.load_yaml(str(config_path))
        form = ParameterForm(root, manager, use_hierarchy=True, current_user=current_user)
        form.pack(fill="both", expand=True, padx=10, pady=10)

        button_frame = ttk.Frame(root)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        def on_save() -> None:
            form.apply()
            save_path = pathlib.Path(__file__).with_name("params_example_saved.yaml")
            manager.save_yaml(str(save_path))
            messagebox.showinfo("저장 완료", f"파라미터를 {save_path.name}에 저장했습니다.")

        save_button = ttk.Button(button_frame, text="저장", command=on_save, width=15)
        save_button.pack(side="right")

    root.mainloop()

    