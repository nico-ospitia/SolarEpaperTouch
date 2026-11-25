#!/usr/bin/env python3
"""Renders the schematic SVG to a one-page A3 PDF and a PNG preview.

Usage:
    python3 render_schematic.py SCHEMATIC.svg OUTPUT.pdf OUTPUT.png [PNG_SCALE]

Needs Playwright with Chromium (pip install playwright && playwright install chromium).
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

svg_path = pathlib.Path(sys.argv[1]).resolve()
pdf_path = pathlib.Path(sys.argv[2]).resolve()
png_path = pathlib.Path(sys.argv[3]).resolve()
scale = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0

svg = svg_path.read_text(encoding="utf-8")
page_html = (
    "<!doctype html><html><head><meta charset='utf-8'><style>"
    "@page{size:420mm 297mm;margin:0}html,body{margin:0;padding:0;background:#fff}"
    "svg{display:block;width:100%;height:auto}"
    "@media print{html,body{width:420mm;height:296mm;overflow:hidden}svg{width:420mm;height:296mm}}"
    "</style></head><body>" + svg + "</body></html>"
)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1800, "height": 1273}, device_scale_factor=scale)
    page.set_content(page_html)
    page.wait_for_timeout(200)
    page.screenshot(path=str(png_path), full_page=True)
    page.pdf(path=str(pdf_path), width="420mm", height="297mm", print_background=True,
             margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
    browser.close()
print("PDF:", pdf_path)
print("PNG:", png_path)
