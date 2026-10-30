"""LeSunshine 顧問 App 圖示：從 tools/icon.svg 產生各尺寸 PNG。

用法（在 web/ 底下）：~/.local/bin/uv run python tools/make_icon.py
用 Mac 的 Chrome 把 SVG 畫成 1024×1024，再用 Pillow 縮成 apple-touch-icon(180)、icon-192、icon-512、
icon-maskable-512、favicon-32。改了圖示記得把 sw.js 的 VERSION 加一（圖示是快取優先）。
"""
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "icons"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

with tempfile.TemporaryDirectory() as tmp:
    shot = Path(tmp) / "icon.png"
    subprocess.run([CHROME, "--headless=new", "--hide-scrollbars", "--force-device-scale-factor=1",
                    "--window-size=1024,1024", f"--screenshot={shot}", (HERE / "icon.svg").as_uri()],
                   check=True, capture_output=True)
    big = Image.open(shot).convert("RGB").crop((0, 0, 1024, 1024))

for name, size in [("apple-touch-icon.png", 180), ("icon-192.png", 192), ("icon-512.png", 512),
                   ("icon-maskable-512.png", 512), ("favicon-32.png", 32)]:
    big.resize((size, size), Image.LANCZOS).save(OUT / name, optimize=True)
    print("✅", name)
