from pathlib import Path

from setuptools import setup

from diatheke import __version__


ROOT = Path(__file__).parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


setup(
    name="diatheke",
    version=__version__,
    description="Reusable Tk directory chooser dialogue for desktop Python applications.",
    long_description=README,
    long_description_content_type="text/markdown",
    author="William Breaden Madden",
    license="GPL-3.0-or-later",
    packages=["diatheke"],
    include_package_data=True,
    python_requires=">=3.10",
    keywords=["tkinter", "tk", "dialog", "directory", "gui"],
)
