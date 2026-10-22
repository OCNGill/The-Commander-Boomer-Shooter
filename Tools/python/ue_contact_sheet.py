"""Build a combined contact sheet from the five in-engine enemy shots.

Reads CommandCenter/outputs/ue_verify/shots/XCOM_<Enemy>_ue.png and writes
CommandCenter/outputs/ue_verify/shots/contact_sheet.png - a 3+2 grid with a
label under each cell, on the same neutral grey as the renders.

Pure PIL, no engine. Fails loudly if a source shot is missing.
"""

import os
import sys

from PIL import Image, ImageDraw

REPO = r'C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter'
SHOTS = REPO + '/CommandCenter/outputs/ue_verify/shots'
OUT = os.path.join(SHOTS, 'contact_sheet.png')
ENEMIES = ['XCOM_Sectoid', 'XCOM_Viper', 'XCOM_Floater', 'XCOM_Muton',
           'XCOM_Chryssalid']

BG = (52, 54, 58)        # neutral grey, matches the render clear colour
FG = (232, 234, 238)
CELL_W = 520
CELL_H = 650
LABEL_H = 34
PAD = 16
COLS = 3
ROWS = 2


def main():
    missing = []
    for e in ENEMIES:
        p = os.path.join(SHOTS, '%s_ue.png' % e)
        if not os.path.isfile(p) or os.path.getsize(p) < 2000:
            missing.append(p)
    if missing:
        print('MISSING SHOTS:')
        for m in missing:
            print('  ' + m)
        sys.exit(1)

    sheet_w = COLS * CELL_W + PAD * (COLS + 1)
    sheet_h = ROWS * (CELL_H + LABEL_H) + PAD * (ROWS + 1)
    sheet = Image.new('RGB', (sheet_w, sheet_h), BG)
    draw = ImageDraw.Draw(sheet)

    for i, e in enumerate(ENEMIES):
        p = os.path.join(SHOTS, '%s_ue.png' % e)
        im = Image.open(p).convert('RGB')
        im.thumbnail((CELL_W, CELL_H), Image.LANCZOS)
        c, r = i % COLS, i // COLS
        x = PAD + c * (CELL_W + PAD)
        y = PAD + r * (CELL_H + LABEL_H + PAD)
        # centre the image in its cell
        ix = x + (CELL_W - im.width) // 2
        iy = y + (CELL_H - im.height) // 2
        sheet.paste(im, (ix, iy))
        draw.text((x + 4, y + CELL_H + 9), e, fill=FG)
        print('%s -> %dx%d placed at (%d,%d)'
              % (e, im.width, im.height, ix, iy))

    sheet.save(OUT)
    print('wrote %s (%dx%d, %d bytes)'
          % (OUT, sheet.width, sheet.height, os.path.getsize(OUT)))


main()
