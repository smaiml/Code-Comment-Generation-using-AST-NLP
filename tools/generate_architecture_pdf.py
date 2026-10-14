from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "Updated_Existing_and_Implemented_Architecture.pdf"
PAGE_W, PAGE_H = 595, 842
INK = (0.09, 0.14, 0.18)
TEAL = (0.09, 0.42, 0.40)
MUTED = (0.32, 0.39, 0.43)
LINE = (0.78, 0.83, 0.84)
PALE = (0.91, 0.95, 0.94)
BLUE = (0.92, 0.94, 0.96)
GOLD = (0.97, 0.94, 0.86)
WHITE = (1, 1, 1)
CONTENT_W = 507


def pdf_escape(text):
    text = text.encode("ascii", "replace").decode("ascii")
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class Page:
    def __init__(self):
        self.commands = []

    @staticmethod
    def _rgb(color):
        return "%.3f %.3f %.3f" % color

    def text(self, x, y, text, size=9, bold=False, color=INK):
        font = "F2" if bold else "F1"
        self.commands.append(
            f"BT /{font} {size} Tf {self._rgb(color)} rg 1 0 0 1 {x:.1f} {y:.1f} Tm ({pdf_escape(text)}) Tj ET"
        )

    def line(self, x1, y1, x2, y2, color=LINE, width=0.7, dash=False):
        d = "[3 2] 0 d" if dash else "[] 0 d"
        self.commands.append(
            f"q {self._rgb(color)} RG {width} w {d} {x1:.1f} {y1:.1f} m {x2:.1f} {y2:.1f} l S Q"
        )

    def rect(self, x, y, w, h, fill, stroke=LINE, radius=4):
        self.commands.append(
            f"q {self._rgb(fill)} rg {self._rgb(stroke)} RG 0.8 w {x:.1f} {y:.1f} {w:.1f} {h:.1f} re B Q"
        )

    def box(self, x, y, w, h, title, detail="", fill=PALE, title_size=8):
        self.rect(x, y, w, h, fill, TEAL if fill == PALE else LINE)
        self.text(x + 5, y + h - 14, title, title_size, True)
        for i, line in enumerate(detail.split("\n")):
            if line:
                self.text(x + 5, y + h - 26 - i * 9, line, 6.6, color=MUTED)

    def arrow(self, x1, y1, x2, y2, dash=False):
        self.line(x1, y1, x2, y2, color=MUTED, width=0.9, dash=dash)
        if abs(y2 - y1) < 2:
            self.line(x2 - 5, y2 + 2, x2, y2, color=MUTED, width=0.9)
            self.line(x2 - 5, y2 - 2, x2, y2, color=MUTED, width=0.9)
        else:
            sign = 1 if y2 > y1 else -1
            self.line(x2 - 2.5, y2 - sign * 5, x2, y2, color=MUTED, width=0.9)
            self.line(x2 + 2.5, y2 - sign * 5, x2, y2, color=MUTED, width=0.9)

    def wrapped(self, x, y, text, max_chars=104, size=8.4, leading=11.5, color=INK):
        words = text.split()
        lines, current = [], ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) > max_chars and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        for i, line in enumerate(lines):
            self.text(x, y - i * leading, line, size, color=color)
        return y - len(lines) * leading

    def table(self, x, top, widths, headers, rows, font_size=7.2, leading=9.2, padding=5):
        header_h = 22
        self.rect(x, top - header_h, sum(widths), header_h, TEAL, TEAL, radius=0)
        xpos = x
        for i, header in enumerate(headers):
            self.text(xpos + padding, top - 15, header, font_size, True, WHITE)
            xpos += widths[i]
        y = top - header_h
        for row_index, row in enumerate(rows):
            cells = []
            max_lines = 1
            for i, text in enumerate(row):
                lines = self._wrap_words(text, max(12, int(widths[i] / (font_size * 0.53))))
                cells.append(lines)
                max_lines = max(max_lines, len(lines))
            row_h = max_lines * leading + padding * 2
            self.commands.append(f"q {self._rgb((0.94, 0.96, 0.96) if row_index % 2 == 0 else WHITE)} rg {x} {y-row_h} {sum(widths)} {row_h} re f Q")
            self.commands.append(f"q {self._rgb(LINE)} RG 0.45 w {x} {y-row_h} {sum(widths)} {row_h} re S Q")
            xpos = x
            for i, lines in enumerate(cells):
                cy = y - padding - font_size
                for line in lines:
                    self.text(xpos + padding, cy, line, font_size, color=INK)
                    cy -= leading
                if i:
                    self.line(xpos, y, xpos, y - row_h, LINE, 0.45)
                xpos += widths[i]
            y -= row_h
        return y

    @staticmethod
    def _wrap_words(text, max_chars):
        words = text.split()
        lines, current = [], ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) > max_chars and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines

    def header(self, title, subtitle, page_num):
        self.text(44, 798, title, 21, True)
        self.text(44, 779, subtitle, 8.5, color=MUTED)
        self.line(44, 25, PAGE_W - 44, 25, LINE, 0.6)
        self.text(44, 14, "Code Comment Generation using AST + NLP", 7, color=MUTED)
        self.text(PAGE_W - 111, 14, f"Architecture brief  |  {page_num}", 7, color=MUTED)


def existing_page():
    page = Page()
    page.header("Previously Existing Architecture", "Project pipeline before the security-gate enhancement.", 1)
    labels = [
        ("Python source", "CLI / GUI", 72),
        ("Parse + validate", "AST / rules", 91),
        ("AST + context", "features / graph", 100),
        ("Comment engines", "rules / ML / fusion", 110),
        ("Attach", "annotated source", 74),
    ]
    gap, x, y, h = 9, 44, 694, 45
    for i, (title, detail, width) in enumerate(labels):
        page.box(x, y, width, h, title, detail, PALE if i in (2, 3) else BLUE, 7.4)
        if i:
            page.arrow(x - gap + 1, y + h / 2, x - 1, y + h / 2)
        x += width + gap

    lower = [
        ("IR + CFG", "three-address IR", 103),
        ("Data-flow", "reaching defs / live vars", 112),
        ("Patterns", "quality findings", 103),
        ("Security scan", "anti-pattern report", 119),
    ]
    x, y2, h2, gap2 = 52, 610, 43, 13
    lower_centers = []
    for i, (title, detail, width) in enumerate(lower):
        page.box(x, y2, width, h2, title, detail, GOLD if i == 3 else BLUE, 7.8)
        lower_centers.append(x + width / 2)
        if i:
            page.arrow(x - gap2 + 1, y2 + h2 / 2, x - 1, y2 + h2 / 2)
        x += width + gap2
    page.arrow(44 + sum(item[2] for item in labels[:4]) + 3 * gap - 5, y - 1,
               lower_centers[0], y2 + h2 + 2, dash=True)
    page.text(52, 592, "Security analysis existed, but it ran after comment generation and attachment.", 7.2, color=MUTED)

    page.text(44, 566, "Previously implemented modules", 12, True, TEAL)
    paragraph = (
        "The original system already parsed and validated Python, extracted AST and context features, generated comments using rule-based, ML, or neurosymbolic modes, attached comments, and ran IR/CFG/DFA/pattern analysis. It also had a static security analyzer and GUI security report. Before the recent changes, the pipeline did not abort on a security finding before generating comments."
    )
    page.wrapped(44, 549, paragraph, max_chars=111, size=8.0, leading=10.8)

    rows = [
        ("Front end", "main.py, parser_module.py, validator.py, gui/: CLI/GUI input, parsing, validation, and display."),
        ("Program analysis", "ast_extractor.py, context_analyzer.py, ir/, analysis/: AST/context, IR, CFG, DFA, and quality patterns."),
        ("Comment engines", "comment_generator.py, ml/, neurosymbolic/: rule-based, T5 AST+NLP, and confidence-gated fusion."),
        ("Existing security", "security_analyzer.py and security GUI: pre-existing static anti-pattern findings and remediation display."),
    ]
    end = page.table(44, 485, [117, 390], ["Area", "Already in the project before this enhancement"], rows, 7.0, 8.8, 4)
    page.text(44, end - 13, "The modules above are existing project work; they are not claimed as newly implemented here.", 7.0, color=MUTED)
    return page


def implementation_page():
    page = Page()
    page.header("Updated Implemented Architecture", "Actual flow after adding AST malware scanning and fail-closed enforcement.", 2)

    first_row = [
        ("Python source", "CLI / GUI", 72),
        ("Parse + validate", "AST / rules", 91),
        ("AST + context", "features / graph", 100),
        ("Security scan", "AST indicators + score", 132),
    ]
    x, y, gap, h = 44, 699, 13, 47
    security_center = 0
    for i, (title, detail, width) in enumerate(first_row):
        page.box(x, y, width, h, title, detail, GOLD if i == 3 else BLUE, 7.7)
        if i:
            page.arrow(x - gap + 1, y + h / 2, x - 1, y + h / 2)
        if i == 3:
            security_center = x + width / 2
        x += width + gap

    page.arrow(security_center, y - 1, security_center, 637)
    gate_x, gate_y, gate_w, gate_h = 190, 591, 212, 44
    page.box(gate_x, gate_y, gate_w, gate_h, "Security Enforcement Gate",
             "critical finding OR module safety score < 80", GOLD, 8.4)
    page.arrow(gate_x + gate_w, gate_y + gate_h / 2, 442, gate_y + gate_h / 2)
    page.box(442, 591, 109, 44, "BLOCK", "SecurityError\nJSON findings", GOLD, 8)
    page.arrow(gate_x + gate_w / 2, gate_y - 1, gate_x + gate_w / 2, 558)

    second_row = [
        ("Comment engines", "rules / ML / fusion", 132),
        ("Attach", "annotated source", 112),
        ("IR + analysis", "CFG / DFA / patterns", 147),
    ]
    x, y2, gap2, h2 = 62, 507, 23, 46
    for i, (title, detail, width) in enumerate(second_row):
        page.box(x, y2, width, h2, title, detail, PALE if i == 0 else BLUE, 7.8)
        if i:
            page.arrow(x - gap2 + 1, y2 + h2 / 2, x - 1, y2 + h2 / 2)
        x += width + gap2
    page.arrow(gate_x + gate_w / 2, 557, 128, y2 + h2 + 2)
    page.text(55, 486, "Accepted runs continue to normal generation and analysis; rejected runs never reach comment processing.", 7.0, color=MUTED)

    page.text(44, 457, "What changed in this implementation", 12, True, TEAL)
    paragraph = (
        "The security analyzer now inspects Python AST calls and assignments for dynamic code execution, shell/system commands, unsafe deserialization, hardcoded credentials/tokens, suspicious network IP endpoints, and combined network/process behavior. It calculates a 0-100 module score. main.py invokes the centralized enforcement gate immediately after AST/context analysis and before comment generation. Rejected CLI runs print a detailed findings report and exit."
    )
    page.wrapped(44, 440, paragraph, max_chars=111, size=7.8, leading=10.2)

    rows = [
        ("security_analyzer.py", "Expanded AST indicators; severity/risk scoring; SecurityError and centralized 80-point/critical-finding gate."),
        ("main.py", "Runs security checks before comment generation; aborts on failure and prints structured findings; supports direct script execution."),
        ("Not implemented", "No agent coordinator or specialist-agent orchestration was added. Security analysis remains static and pattern-based."),
    ]
    page.table(44, 380, [130, 377], ["Changed area", "Implemented behavior / boundary"], rows, 6.8, 8.5, 4)
    return page


def build_pdf():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pages = [existing_page(), implementation_page()]
    objects = [None] * (4 + 2 * len(pages))
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    page_refs = [f"{5 + i * 2} 0 R" for i in range(len(pages))]
    objects[1] = ("<< /Type /Pages /Kids [" + " ".join(page_refs) + "] /Count " + str(len(pages)) + " >>").encode("ascii")
    objects[2] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    objects[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"
    for i, page in enumerate(pages):
        page_id = 5 + i * 2
        stream_id = page_id + 1
        stream = "\n".join(page.commands).encode("ascii")
        objects[page_id - 1] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {stream_id} 0 R >>"
        ).encode("ascii")
        objects[stream_id - 1] = f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream"

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_id, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_id} 0 obj\n".encode("ascii"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    OUTPUT.write_bytes(pdf)
    return OUTPUT


if __name__ == "__main__":
    print(build_pdf())
