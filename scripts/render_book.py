"""Render the fixed original-book scans for GitHub Pages."""
from hashlib import file_digest
import json
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

config = json.loads(Path('data/book-pagination.json').read_text(encoding='utf-8'))
book, output = map(Path, sys.argv[1:])
with book.open('rb') as pdf:
    if file_digest(pdf, 'sha256').hexdigest() != config['source']['sha256']:
        raise SystemExit('Original PDF checksum mismatch')
if output.exists():
    shutil.rmtree(output)
output.mkdir(parents=True)
font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc', 30)
# Work in batches so compressed and uncompressed page images never fill the runner.
for first in range(1, config['scanCount'] + 1, 40):
    last = min(first + 39, config['scanCount'])
    prefix = book.parent / 'render-page'
    subprocess.run(['pdftoppm', '-f', str(first), '-l', str(last), '-r', '200',
                    '-png', str(book), str(prefix)], check=True)
    for number in range(first, last + 1):
        scan = prefix.with_name(f'{prefix.name}-{number:04d}.png')
        with Image.open(scan) as original:
            image = original.convert('RGB')
        color = (255, 255, 255) if number == 1 else (116, 47, 50)
        ImageDraw.Draw(image).text((26, 16), '冯氏族谱 · fengshizupu.com', font=font, fill=color)
        image.save(output / f'p{number:04d}.webp', 'WEBP', quality=80)
        scan.unlink()
