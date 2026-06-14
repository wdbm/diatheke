# diatheke

Diatheke is a reusable Tk directory chooser for Python applications and it is dependent only on the Python standard libraries. It provides a dialogue window that returns a `pathlib.Path`.

## setup

```bash
python3 -m pip install .
```

## keyboard shortcuts

- `Enter` when focused on the path field: open the typed directory
- `Enter` when focused on the directory list: open the highlighted directory
- `Ctrl+Enter`: select the current directory and close the dialog
- `Ctrl+Up`: change to the parent directory
- `Escape`: cancel and close the dialog

## usage

```python
from diatheke import askdirectory

selected_directory = askdirectory(
    title="Choose a workspace",
    initialdir="~",
    allow_create_directory=True,
    show_hidden=False,
)

if selected_directory is not None:
    print(selected_directory)
```

For embedding in an existing Tk application, instantiate
`diatheke.DirectoryChooserDialog` directly and pass the parent window.
