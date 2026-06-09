from flask import Flask, make_response
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone
import io
import os

app = Flask(__name__)

# Zieldatum: 11. Juni 2026, 21:00 Uhr MESZ = 19:00 UTC
TARGET = datetime(2026, 6, 11, 19, 0, 0, tzinfo=timezone.utc)

# Farben (Tipwin CI)
RED   = (220, 13, 21)
DARK  = (87, 87, 86)
WHITE = (255, 255, 255)

def get_font(size, bold=False):
    paths = [
        # Windows
        r'C:\Windows\Fonts\arialbd.ttf' if bold else r'C:\Windows\Fonts\arial.ttf',
        r'C:\Windows\Fonts\verdanab.ttf' if bold else r'C:\Windows\Fonts\verdana.ttf',
        r'C:\Windows\Fonts\calibrib.ttf' if bold else r'C:\Windows\Fonts\calibri.ttf',
        # Linux
        f'/usr/share/fonts/truetype/dejavu/DejaVuSans{"-Bold" if bold else ""}.ttf',
        f'/usr/share/fonts/truetype/liberation/LiberationSans-{"Bold" if bold else "Regular"}.ttf',
    ]
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def generate_image():
    now  = datetime.now(timezone.utc)
    diff = TARGET - now

    if diff.total_seconds() <= 0:
        days = hours = minutes = seconds = 0
    else:
        total = int(diff.total_seconds())
        days    = diff.days
        hours   = (total % 86400) // 3600
        minutes = (total % 3600)  // 60
        seconds = total % 60

    W, H   = 530, 140
    radius = 70
    img    = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw   = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (W - 1, H - 1)], radius=radius, fill=(*RED, 255))

    font_num   = get_font(56, bold=True)
    font_label = get_font(16)

    units     = [(str(days).zfill(2), 'TAGE'),
                 (str(hours).zfill(2), 'STUNDEN'),
                 (str(minutes).zfill(2), 'MINUTEN'),
                 (str(seconds).zfill(2), 'SEKUNDEN')]
    col_w = W // 4

    num_ref_bbox   = draw.textbbox((0, 0), '00', font=font_num)
    num_h          = num_ref_bbox[3] - num_ref_bbox[1]
    label_ref_bbox = draw.textbbox((0, 0), 'SEKUNDEN', font=font_label)
    label_h        = label_ref_bbox[3] - label_ref_bbox[1]
    gap            = 24
    total_h        = num_h + gap + label_h
    num_y          = (H - total_h) // 2

    content_w = 470
    x_offset  = (W - content_w) // 2
    col_w     = content_w // 4

    for i, (number, label) in enumerate(units):
        cx = x_offset + i * col_w + col_w // 2

        # Zahl
        bbox = draw.textbbox((0, 0), number, font=font_num)
        tw   = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, num_y), number, fill=WHITE, font=font_num)

        # Label
        bbox2 = draw.textbbox((0, 0), label, font=font_label)
        lw    = bbox2[2] - bbox2[0]
        draw.text((cx - lw // 2, num_y + num_h + gap), label, fill=WHITE, font=font_label)

        # Trennpunkt – horizontal und vertikal zentriert zwischen den Spalten
        if i < 3:
            colon_bbox = draw.textbbox((0, 0), ':', font=font_num)
            colon_w    = colon_bbox[2] - colon_bbox[0]
            colon_h    = colon_bbox[3] - colon_bbox[1]
            colon_x    = x_offset + (i + 1) * col_w - colon_w // 2
            colon_y    = num_y + num_ref_bbox[1] + (num_h - colon_h) // 2 - colon_bbox[1]
            draw.text((colon_x, colon_y), ':', fill=WHITE, font=font_num)

    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    buf.seek(0)
    return buf

@app.route('/countdown.png')
def countdown():
    buf      = generate_image()
    response = make_response(buf.read())
    response.headers['Content-Type']  = 'image/png'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma']        = 'no-cache'
    response.headers['Expires']       = '0'
    return response

@app.route('/')
def preview():
    return '''
    <html><body style="background:#f0f0f0;display:flex;align-items:center;justify-content:center;height:100vh;">
    <img src="/countdown.png" style="border:1px solid #ddd;" />
    </body></html>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
