"""Setup script for building the Frame Capture Application executable."""

import sys
import os
from setuptools import setup

if sys.platform == 'win32':
    import pyInstaller

# PyInstaller configuration
setup(
    name="FrameCaptureTool",
    version="1.0.0",
    description="A Windows GUI application for capturing and browsing screen frames",
    author="edgaranarossi",
    author_email="edgaranarossi@gmail.com",
    packages=["src"],
    package_data={
        "src": ["resources/*"],
    },
    entry_points={
        "gui_scripts": [
            "frame-capture-tool = src.main:main",
        ],
    },
    install_requires=[
        "pyqt5>=5.15.9",
        "opencv-python>=4.8.0",
        "pillow>=10.0.0",
        "numpy>=1.24.0",
        "mss>=6.1.0",
    ],
    options={
        "build_exe": {
            "packages": ["PyQt5", "numpy", "PIL", "mss"],
            "include_files": [
                ("src/resources", "resources"),
            ],
            "excludes": ["tkinter", "test"],
            "optimize": 2,
        },
    },
)