"""
################################################################################
#                                                                              #
# diatheke                                                                     #
#                                                                              #
################################################################################
#                                                                              #
# LICENCE INFORMATION                                                          #
#                                                                              #
# This program provides a reusable Tk directory chooser dialogue for Python    #
# applications.                                                                #
#                                                                              #
# copyright (C) 2026 William Breaden Madden                                    #
#                                                                              #
# This software is released under the terms of the GNU General Public License  #
# version 3 (GPLv3).                                                           #
#                                                                              #
# This program is free software: you can redistribute it and/or modify it      #
# under the terms of the GNU General Public License as published by the Free   #
# Software Foundation, either version 3 of the License, or (at your option)    #
# any later version.                                                           #
#                                                                              #
# This program is distributed in the hope that it will be useful, but WITHOUT  #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or        #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for     #
# more details.                                                                #
#                                                                              #
# For a copy of the GNU General Public License, see                            #
# <http://www.gnu.org/licenses>.                                               #
#                                                                              #
################################################################################
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

__version__ = "2026-06-14T0147Z"
__all__     = ["__version__", "DirectoryChooserDialog", "askdirectory"]

DEFAULT_WIDTH      = 820
DEFAULT_HEIGHT     = 560
DEFAULT_MIN_WIDTH  = 720
DEFAULT_MIN_HEIGHT = 480

DEFAULT_LABELS = {
    "path_label": "Directory:",
    "go_button": "Go",
    "up_button": "Up",
    "home_button": "Home",
    "refresh_button": "Refresh",
    "new_folder_button": "New folder",
    "show_hidden_toggle": "Show hidden directories",
    "open_button": "Open",
    "select_highlighted_button": "Select highlighted",
    "select_current_button": "Select current",
    "cancel_button": "Cancel",
    "current_directory_label": "Current directory",
    "highlighted_directory_label": "Highlighted",
    "new_folder_dialog_title": "New folder",
    "new_folder_prompt": "Folder name:",
    "invalid_directory_name_title": "New folder",
    "invalid_directory_name_message": "Please provide a valid directory name.",
    "directory_exists_title": "New folder",
    "directory_exists_message": "Directory already exists:\n{path}",
    "directory_create_error_title": "New folder",
    "directory_create_error_message": "Unable to create directory:\n{path}\n\n{error}",
    "directory_not_found_title": "Directory chooser",
    "directory_not_found_message": "Directory does not exist:\n{path}",
    "not_a_directory_title": "Directory chooser",
    "not_a_directory_message": "Not a directory:\n{path}",
    "directory_open_error_title": "Directory chooser",
    "directory_open_error_message": "Unable to open directory:\n{path}\n\n{error}",
    "directory_no_access_title": "Directory chooser",
    "directory_no_access_message": "You do not have permission to access directory:\n{path}",
    "status_including_hidden": "{count} {directory_word} shown, including hidden",
    "status_excluding_hidden": "{count} {directory_word} shown, excluding hidden",
    "no_access_suffix": " [no access]",
}


def _nearest_existing_directory(path: str | Path | None) -> Path:
    if path is None:
        return Path.home()
    candidate = Path(path).expanduser()
    try:
        candidate = candidate.resolve(strict=False)
    except Exception:
        candidate = candidate.absolute()
    if candidate.is_dir():
        return candidate
    if candidate.exists():
        candidate = candidate.parent
    while not candidate.exists() or not candidate.is_dir():
        parent = candidate.parent
        if parent == candidate:
            return Path.home()
        candidate = parent
    return candidate


@dataclass(frozen=True)
class _DirectoryEntry:
    path: Path
    accessible: bool


class _NamePrompt(tk.Toplevel):
    def __init__(self, parent, title: str, prompt: str, create_label: str, cancel_label: str):
        super().__init__(parent)
        self.result: str | None = None
        self.title(title)
        self.transient(parent)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        outer = tk.Frame(self, padx=12, pady=12)
        outer.pack(fill="both", expand=True)

        tk.Label(outer, text=prompt, anchor="w").pack(fill="x")
        self.value_var = tk.StringVar()
        entry = tk.Entry(outer, textvariable=self.value_var, width=36)
        entry.pack(fill="x", pady=(8, 12))
        entry.bind("<Return>", self._accept, add="+")
        entry.bind("<Escape>", self._cancel, add="+")

        buttons = tk.Frame(outer)
        buttons.pack(fill="x")
        tk.Button(buttons, text=cancel_label, command=self._cancel).pack(side="right")
        tk.Button(buttons, text=create_label, command=self._accept).pack(side="right", padx=(0, 6))

        self.update_idletasks()
        self._centre_on_parent(parent)
        self.grab_set()
        entry.focus_set()

    def _centre_on_parent(self, parent):
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = max(1, parent.winfo_width())
        parent_height = max(1, parent.winfo_height())
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _accept(self, event=None):
        value = self.value_var.get().strip()
        if not value:
            return "break"
        self.result = value
        self.destroy()
        return "break"

    def _cancel(self, event=None):
        self.result = None
        self.destroy()
        return "break"


class DirectoryChooserDialog(tk.Toplevel):
    """
    Reusable modal directory chooser dialogue for Tk applications.

    The dialogue returns a `pathlib.Path` for the selected directory, or `None`
    when cancelled.
    """

    def __init__(
        self,
        parent=None,
        title: str = "Choose a directory",
        initialdir: str | Path | None = None,
        allow_create_directory: bool = True,
        show_hidden: bool = False,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        min_width: int = DEFAULT_MIN_WIDTH,
        min_height: int = DEFAULT_MIN_HEIGHT,
        labels: dict[str, str] | None = None,
    ):
        super().__init__(parent)
        self.result: Path | None = None
        self.current_directory = _nearest_existing_directory(initialdir)
        self.allow_create_directory = allow_create_directory
        self.directory_entries: list[_DirectoryEntry] = []
        self.labels = dict(DEFAULT_LABELS)
        if labels:
            self.labels.update(labels)

        self.title(title)
        if parent is not None and parent.winfo_viewable():
            self.transient(parent)
        self.minsize(max(1, int(min_width)), max(1, int(min_height)))
        self.geometry(f"{max(1, int(width))}x{max(1, int(height))}")
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        self.path_var = tk.StringVar()
        self.selection_var = tk.StringVar(value=self.labels["current_directory_label"])
        self.status_var = tk.StringVar()
        self.show_hidden_var = tk.BooleanVar(value=show_hidden)

        self._build_ui()
        self._centre_on_parent(parent)
        self._load_directory(self.current_directory)
        self.deiconify()
        self.lift()
        self.grab_set()
        self.path_entry.focus_set()

    def _show_error(self, title_key: str, message_key: str, **values):
        messagebox.showerror(
            self.labels[title_key],
            self.labels[message_key].format(**values),
            parent=self,
        )

    def _directory_from_input(self, raw_path: str) -> Path | None:
        candidate = Path(raw_path).expanduser()
        try:
            candidate = candidate.resolve(strict=False)
        except Exception:
            candidate = candidate.absolute()
        if not candidate.exists():
            self._show_error("directory_not_found_title", "directory_not_found_message", path=candidate)
            return None
        if not candidate.is_dir():
            self._show_error("not_a_directory_title", "not_a_directory_message", path=candidate)
            return None
        return candidate.resolve()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = tk.Frame(self, padx=12, pady=12)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(1, weight=1)

        tk.Label(top, text=self.labels["path_label"]).grid(row=0, column=0, sticky="w")
        self.path_entry = tk.Entry(top, textvariable=self.path_var)
        self.path_entry.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        self.path_entry.bind("<Return>", self._go_to_entered_directory, add="+")
        self.path_entry.bind("<Control-Return>", self._select_current_directory, add="+")
        self.path_entry.bind("<Control-Up>", self._go_up, add="+")
        self.path_entry.bind("<Escape>", self._cancel, add="+")

        tk.Button(top, text=self.labels["go_button"], command=self._go_to_entered_directory).grid(row=0, column=2, sticky="ew")

        actions = tk.Frame(top)
        actions.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        tk.Button(actions, text=self.labels["up_button"], command=self._go_up).pack(side="left")
        tk.Button(actions, text=self.labels["home_button"], command=self._go_home).pack(side="left", padx=(6, 0))
        tk.Button(actions, text=self.labels["refresh_button"], command=self._refresh).pack(side="left", padx=(6, 0))
        if self.allow_create_directory:
            tk.Button(actions, text=self.labels["new_folder_button"], command=self._create_directory).pack(side="left", padx=(6, 0))
        tk.Checkbutton(
            actions,
            text=self.labels["show_hidden_toggle"],
            variable=self.show_hidden_var,
            command=self._refresh,
        ).pack(side="right")

        centre = tk.Frame(self, padx=12)
        centre.grid(row=1, column=0, sticky="nsew")
        centre.grid_columnconfigure(0, weight=1)
        centre.grid_rowconfigure(0, weight=1)

        self.directory_list = tk.Listbox(centre, activestyle="none", exportselection=False)
        self.directory_list.grid(row=0, column=0, sticky="nsew")
        self.directory_list.bind("<<ListboxSelect>>", self._update_selection_label, add="+")
        self.directory_list.bind("<Double-Button-1>", self._open_selected_directory, add="+")
        self.directory_list.bind("<Return>", self._open_selected_directory, add="+")
        self.directory_list.bind("<Control-Return>", self._select_current_directory, add="+")
        self.directory_list.bind("<Control-Up>", self._go_up, add="+")
        self.directory_list.bind("<Escape>", self._cancel, add="+")

        scrollbar = tk.Scrollbar(centre, orient="vertical", command=self.directory_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.directory_list.configure(yscrollcommand=scrollbar.set)

        bottom = tk.Frame(self, padx=12, pady=12)
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)

        info = tk.Frame(bottom)
        info.grid(row=0, column=0, sticky="ew")
        info.grid_columnconfigure(0, weight=1)
        tk.Label(info, textvariable=self.selection_var, anchor="w").grid(row=0, column=0, sticky="ew")
        tk.Label(info, textvariable=self.status_var, anchor="w").grid(row=1, column=0, sticky="ew", pady=(4, 0))

        buttons = tk.Frame(bottom)
        buttons.grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 0))

        self.open_button = tk.Button(
            buttons,
            text=self.labels["open_button"],
            command=self._open_selected_directory,
            state="disabled",
        )
        self.open_button.pack(side="left")
        self.select_highlighted_button = tk.Button(
            buttons,
            text=self.labels["select_highlighted_button"],
            command=self._select_highlighted_directory,
            state="disabled",
        )
        self.select_highlighted_button.pack(side="left", padx=(6, 0))
        tk.Button(buttons, text=self.labels["select_current_button"], command=self._select_current_directory).pack(side="left", padx=(6, 0))
        tk.Button(buttons, text=self.labels["cancel_button"], command=self._cancel).pack(side="left", padx=(6, 0))

    def _centre_on_parent(self, parent):
        self.update_idletasks()
        if parent is None or not parent.winfo_exists():
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            width = self.winfo_width()
            height = self.winfo_height()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
        else:
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_width = max(1, parent.winfo_width())
            parent_height = max(1, parent.winfo_height())
            width = max(1, self.winfo_width())
            height = max(1, self.winfo_height())
            x = parent_x + (parent_width - width) // 2
            y = parent_y + (parent_height - height) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _visible_directory_entries(self, directory: Path) -> list[_DirectoryEntry]:
        entries: list[_DirectoryEntry] = []
        for entry in directory.iterdir():
            if not self.show_hidden_var.get() and entry.name.startswith("."):
                continue
            try:
                if not entry.is_dir():
                    continue
                entries.append(_DirectoryEntry(path=entry, accessible=True))
            except OSError:
                entries.append(_DirectoryEntry(path=entry, accessible=False))
        return sorted(entries, key=lambda item: item.path.name.casefold())

    def _load_directory(self, directory: Path):
        try:
            directory = directory.expanduser().resolve()
        except Exception:
            directory = _nearest_existing_directory(directory)
        try:
            entries = self._visible_directory_entries(directory)
        except OSError as error:
            self._show_error("directory_open_error_title", "directory_open_error_message", path=directory, error=error)
            return
        self.current_directory = directory
        self.directory_entries = entries
        self.path_var.set(str(directory))
        self.directory_list.delete(0, "end")
        for entry in entries:
            label = f"{entry.path.name}/"
            if not entry.accessible:
                label += self.labels["no_access_suffix"]
            self.directory_list.insert("end", label)
        if entries:
            self.directory_list.selection_set(0)
            self.directory_list.activate(0)
            self.directory_list.see(0)
        self._update_selection_label()
        directory_word = "directory" if len(entries) == 1 else "directories"
        status_key = "status_including_hidden" if self.show_hidden_var.get() else "status_excluding_hidden"
        self.status_var.set(self.labels[status_key].format(count=len(entries), directory_word=directory_word))

    def _selected_index(self) -> int | None:
        selection = self.directory_list.curselection()
        if not selection:
            return None
        index = int(selection[0])
        if 0 <= index < len(self.directory_entries):
            return index
        return None

    def _selected_directory_entry(self) -> _DirectoryEntry | None:
        index = self._selected_index()
        if index is None:
            return None
        return self.directory_entries[index]

    def _selected_directory(self) -> Path | None:
        selected_entry = self._selected_directory_entry()
        if selected_entry is None:
            return None
        return selected_entry.path

    def _update_selection_label(self, event=None):
        selected_entry = self._selected_directory_entry()
        if selected_entry is None:
            self.selection_var.set(f"{self.labels['current_directory_label']}: {self.current_directory}")
            self.open_button.config(state="disabled")
            self.select_highlighted_button.config(state="disabled")
        else:
            suffix = "" if selected_entry.accessible else self.labels["no_access_suffix"]
            self.selection_var.set(f"{self.labels['highlighted_directory_label']}: {selected_entry.path}{suffix}")
            state = "normal" if selected_entry.accessible else "disabled"
            self.open_button.config(state=state)
            self.select_highlighted_button.config(state=state)

    def _show_no_access_error(self, path: Path):
        self._show_error("directory_no_access_title", "directory_no_access_message", path=path)

    def _go_to_entered_directory(self, event=None):
        target = self._directory_from_input(self.path_var.get())
        if target is not None:
            self._load_directory(target)
        return "break"

    def _go_up(self, event=None):
        parent = self.current_directory.parent
        if parent != self.current_directory:
            self._load_directory(parent)
        return "break"

    def _go_home(self):
        self._load_directory(Path.home())

    def _refresh(self):
        self._load_directory(self.current_directory)

    def _open_selected_directory(self, event=None):
        selected_entry = self._selected_directory_entry()
        if selected_entry is not None:
            if not selected_entry.accessible:
                self._show_no_access_error(selected_entry.path)
                return "break"
            self._load_directory(selected_entry.path)
        return "break"

    def _select_highlighted_directory(self):
        selected_entry = self._selected_directory_entry()
        if selected_entry is None:
            return
        if not selected_entry.accessible:
            self._show_no_access_error(selected_entry.path)
            return
        self.result = selected_entry.path.resolve()
        self.destroy()

    def _select_current_directory(self, event=None):
        self.result = self.current_directory.resolve()
        self.destroy()
        return "break"

    def _create_directory(self):
        prompt = _NamePrompt(
            self,
            self.labels["new_folder_dialog_title"],
            self.labels["new_folder_prompt"],
            self.labels["new_folder_button"],
            self.labels["cancel_button"],
        )
        self.wait_window(prompt)
        name = prompt.result
        if name is None:
            return
        if "/" in name or name in {".", ".."}:
            self._show_error("invalid_directory_name_title", "invalid_directory_name_message")
            return
        target = self.current_directory / name
        try:
            target.mkdir()
        except FileExistsError:
            self._show_error("directory_exists_title", "directory_exists_message", path=target)
            return
        except OSError as error:
            self._show_error("directory_create_error_title", "directory_create_error_message", path=target, error=error)
            return
        self._load_directory(self.current_directory)
        try:
            index = next(index for index, entry in enumerate(self.directory_entries) if entry.path == target)
        except StopIteration:
            return
        self.directory_list.selection_clear(0, "end")
        self.directory_list.selection_set(index)
        self.directory_list.activate(index)
        self.directory_list.see(index)
        self._update_selection_label()

    def _cancel(self, event=None):
        self.result = None
        self.destroy()
        return "break"


def askdirectory(
    parent=None,
    title: str = "Choose a directory",
    initialdir: str | Path | None = None,
    allow_create_directory: bool = True,
    show_hidden: bool = False,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    min_width: int = DEFAULT_MIN_WIDTH,
    min_height: int = DEFAULT_MIN_HEIGHT,
    labels: dict[str, str] | None = None,
) -> Path | None:
    """
    Open a modal directory chooser dialogue and return the selected directory.

    Returns a resolved `pathlib.Path` when the user selects a directory, or
    `None` when the dialogue is cancelled.
    """
    owned_root = None
    if parent is None:
        owned_root = tk.Tk()
        owned_root.withdraw()
        parent = owned_root
    dialog = DirectoryChooserDialog(
        parent=parent,
        title=title,
        initialdir=initialdir,
        allow_create_directory=allow_create_directory,
        show_hidden=show_hidden,
        width=width,
        height=height,
        min_width=min_width,
        min_height=min_height,
        labels=labels,
    )
    try:
        dialog.wait_window()
        return dialog.result
    finally:
        if owned_root is not None and owned_root.winfo_exists():
            owned_root.destroy()
