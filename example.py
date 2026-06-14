from __future__ import annotations

from diatheke import askdirectory


def main() -> None:
    print("Opening diatheke directory chooser dialogue...")

    selected_directory = askdirectory(
        title="Choose a directory",
        initialdir="~",
        allow_create_directory=True,
        show_hidden=False,
    )

    if selected_directory is None:
        print("No directory was selected.")
        return

    print("Directory selected.")
    print(f"Absolute path: {selected_directory}")
    print(f"Name: {selected_directory.name}")
    print(f"Parent: {selected_directory.parent}")
    print(f"Exists: {selected_directory.exists()}")
    print(f"Is directory: {selected_directory.is_dir()}")


if __name__ == "__main__":
    main()
