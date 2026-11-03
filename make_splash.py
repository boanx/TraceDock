"""Render the bundled startup card at build time."""
from pathlib import Path
import os
import sys

from PIL import Image, ImageDraw, ImageFont

destination = Path(sys.argv[1])
destination.parent.mkdir(parents=True, exist_ok=True)
fonts = Path(os.environ.get('WINDIR', r'C:\Windows')) / 'Fonts'
canvas = Image.new('RGB', (480, 200), '#e8eff5')
draw = ImageDraw.Draw(canvas)
with Image.open(Path(__file__).with_name('tracedock.ico')) as source:
    icon = source.ico.getimage(max(source.ico.sizes())).convert('RGBA')
    icon.thumbnail((68, 68), Image.Resampling.LANCZOS)
    canvas.paste(icon, (34, 54), icon)
draw.text((123, 50), 'TraceDock', font=ImageFont.truetype(str(fonts / 'segoeuib.ttf'), 34), fill='#007f85')
draw.text((125, 101), 'Yükleniyor…', font=ImageFont.truetype(str(fonts / 'segoeui.ttf'), 21), fill='#40596f')
draw.rounded_rectangle((34, 151, 446, 157), radius=3, fill='#cbdbe7')
canvas.save(destination)
