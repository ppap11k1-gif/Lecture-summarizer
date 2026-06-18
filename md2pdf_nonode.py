#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Node 없이 독학정리본 .md -> .pdf 변환.
lecture-pdf/template.html 의 CSS를 그대로 재사용하고, 수식은 MathJax CDN으로 렌더,
Chrome headless --print-to-pdf 로 출력. (make-pdf.sh 의 node 경로 대체)

사용법: py md2pdf_nonode.py <입력.md> <출력.pdf>
"""
import sys, os, re, html, subprocess, tempfile, pathlib

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")

MATHJAX = """<script>
MathJax = {
  tex: { inlineMath: [['$','$'],['\\\\(','\\\\)']], displayMath: [['$$','$$'],['\\\\[','\\\\]']], processEscapes: true },
  options: { skipHtmlTags: ['script','noscript','style','textarea','pre','code'] }
};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>"""

CHROME_CANDS = [
    r"C:/Program Files/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    r"C:/Program Files/Microsoft/Edge/Application/msedge.exe",
]

def find_chrome():
    for c in CHROME_CANDS:
        if os.path.exists(c):
            return c
    raise SystemExit("Chrome/Edge를 찾을 수 없습니다.")

def convert(md_path, pdf_path):
    import markdown
    md = pathlib.Path(md_path).read_text(encoding="utf-8")

    # 1) 수식 보호 (markdown 파싱 전에 placeholder로 치환)
    disp, inl = [], []
    def _disp(m):
        disp.append(m.group(1).strip()); return f"\x00D{len(disp)-1}\x00"
    def _inl(m):
        inl.append(m.group(1).strip()); return f"\x00I{len(inl)-1}\x00"
    md = re.sub(r"\$\$([\s\S]+?)\$\$", _disp, md)
    md = re.sub(r"\$([^\$\n]+?)\$", _inl, md)

    # 2) markdown -> HTML
    body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists", "attr_list"])

    # 3) 수식 복원 (HTML escape: < > & 가 태그로 오인되지 않게 -> 브라우저가 디코드 후 MathJax가 원문 인식)
    def esc(t): return html.escape(t, quote=False)
    body = re.sub(r"\x00D(\d+)\x00", lambda m: "$$" + esc(disp[int(m.group(1))]) + "$$", body)
    body = re.sub(r"\x00I(\d+)\x00", lambda m: "$" + esc(inl[int(m.group(1))]) + "$", body)

    # 4) 템플릿 적용
    tpl = pathlib.Path(TEMPLATE).read_text(encoding="utf-8")
    title_m = re.search(r"^#\s+(.+)$", pathlib.Path(md_path).read_text(encoding="utf-8"), re.M)
    title = title_m.group(1) if title_m else "강의 정리"
    final = tpl.replace("{{TITLE}}", title).replace("{{KATEX_CSS}}", MATHJAX).replace("{{CONTENT}}", body)

    # 5) 임시 HTML (ASCII 경로 — file:// URL 인코딩 이슈 회피)
    stem = re.sub(r"[^A-Za-z0-9]", "", pathlib.Path(pdf_path).stem) or "doc"
    tmp_html = os.path.join(tempfile.gettempdir(), f"econ_{stem}.html")
    pathlib.Path(tmp_html).write_text(final, encoding="utf-8")

    # 6) Chrome headless -> PDF
    chrome = find_chrome()
    url = "file:///" + tmp_html.replace("\\", "/")
    out = str(pathlib.Path(pdf_path))
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--no-pdf-header-footer", "--virtual-time-budget=30000",
           "--run-all-compositor-stages-before-draw",
           f"--print-to-pdf={out}", url]
    subprocess.run(cmd, capture_output=True, timeout=180)
    if os.path.exists(out) and os.path.getsize(out) > 0:
        print(f"OK  {out}  ({os.path.getsize(out)//1024} KB)")
        try: os.remove(tmp_html)
        except OSError: pass
        return True
    print(f"FAIL  {out}  (tmp html kept: {tmp_html})")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("사용법: py md2pdf_nonode.py <입력.md> <출력.pdf>")
    ok = convert(sys.argv[1], sys.argv[2])
    sys.exit(0 if ok else 1)
