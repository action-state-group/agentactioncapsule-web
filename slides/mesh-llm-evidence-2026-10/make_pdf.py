#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# make_pdf.py <dir> : prints slide-1.html + slide-2.html (?static) to one 2-page 1920x1080 PDF
import sys, pathlib, io
from playwright.sync_api import sync_playwright
from pypdf import PdfWriter, PdfReader
d = pathlib.Path(sys.argv[1]).resolve(); w = PdfWriter()
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width':1920,'height':1080})
    for n in (1, 2):
        pg.goto((d / f'slide-{n}.html').as_uri() + '?static'); pg.wait_for_timeout(1500)
        pg.add_style_tag(content='@page{size:1920px 1080px;margin:0} html,body{margin:0;overflow:hidden}')
        pdf = pg.pdf(width='1920px', height='1080px', print_background=True, page_ranges='1')
        for page in PdfReader(io.BytesIO(pdf)).pages: w.add_page(page)
    b.close()
w.add_metadata({'/Title': 'Mesh-LLM evidence layer: two slides'})
with open(d / 'mesh-llm-evidence.pdf', 'wb') as f: w.write(f)
