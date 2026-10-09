from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "Existing_and_Proposed_Architecture.pdf"
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
    page.header("Existing Architecture", "Implemented architecture evidenced in project documentation and source code.", 1)
    labels = [
        ("Python source", "file / GUI", 77),
        ("Parse + validate", "AST / checks", 91),
        ("AST + context", "features / graph", 96),
        ("Comment engines", "rules / ML / fusion", 113),
        ("Attach", "annotated output", 82),
    ]
    gap, x, y, h = 12, 44, 693, 46
    starts = []
    for i, (title, detail, width) in enumerate(labels):
        starts.append(x)
        page.box(x, y, width, h, title, detail, PALE if i in (2, 3) else BLUE, 7.6)
        if i:
            page.arrow(starts[i - 1] + labels[i - 1][2] + 1, y + h / 2, x - 1, y + h / 2)
        x += width + gap

    lower = [
        ("IR + CFG", "three-address IR / blocks", 112),
        ("Data-flow", "reaching defs / live vars", 112),
        ("Patterns", "quality findings", 112),
        ("Security scan", "static anti-pattern checks", 121),
    ]
    x, y2, h2, gap2 = 48, 620, 43, 11
    lower_starts = []
    for i, (title, detail, width) in enumerate(lower):
        lower_starts.append(x)
        page.box(x, y2, width, h2, title, detail, GOLD if i == 3 else BLUE, 7.8)
        if 0 < i < 3:
            page.arrow(lower_starts[i - 1] + lower[i - 1][2] + 1, y2 + h2 / 2, x - 1, y2 + h2 / 2)
        x += width + gap2
    page.arrow(starts[2] + labels[2][2] / 2, y - 1, starts[2] + labels[2][2] / 2, y2 + h2 + 2, dash=True)
    page.text(50, 603, "Pipeline logs and PyQt6 workspaces display generation, analysis, and security results.", 7, color=MUTED)

    page.text(44, 580, "Current implementation", 12, True, TEAL)
    paragraph = (
        "The application is a sequential Python source-analysis pipeline. The CLI and PyQt6 GUI pass source code to the parser and validator; AST features and context then feed the selected comment engine. Generated comments are attached to source. The pipeline also builds an intermediate representation, runs control-flow and data-flow analysis, detects code patterns, and produces a security report."
    )
    page.wrapped(44, 563, paragraph, max_chars=111, size=8.1, leading=11)

    rows = [
        ("Input and front end", "main.py, parser_module.py, validator.py: CLI orchestration, source parsing, AST checks. gui/: desktop interface and workspaces."),
        ("Program understanding", "ast_extractor.py, ast_body_extractor.py, context_analyzer.py: AST features, function details, complexity, variables, and call graph."),
        ("Comment generation", "comment_generator.py and ml/: rule-based and T5 AST+NLP generation. neurosymbolic/: confidence-gated ML, symbolic fallback, consistency checks."),
        ("Static analysis", "ir/ and analysis/: intermediate representation, CFG, reaching-definitions/live-variable DFA, and pattern findings."),
        ("Security and reporting", "security_analyzer.py: AST/context-based anti-pattern scan and remediation report. logger.py and GUI workspaces present results."),
    ]
    end = page.table(44, 506, [126, 381], ["Layer", "Implemented modules / responsibility"], rows, 7.2, 9.1, 5)
    page.text(44, end - 14, "Security is already implemented and surfaced in CLI/GUI results. It is static, pattern-based analysis, not a complete security audit.", 7.2, color=MUTED)
    return page


def proposed_page():
    page = Page()
    page.header("Proposed Architecture", "Add coordinated, bounded agents across existing modules with explicit security controls.", 2)
    page.box(242, 719, 111, 31, "User: CLI or GUI", "source + requested task", BLUE, 8)
    page.arrow(297, 718, 297, 703)
    page.box(224, 667, 147, 35, "Agent Coordinator", "plan / route / shared run state", PALE, 9)

    agents = [
        ("AST / Context", "parser, extractor, context", BLUE),
        ("Security", "scanner, security policy", GOLD),
        ("Generation", "rules, T5, neurosymbolic", PALE),
        ("Static Analysis", "IR, CFG, DFA, patterns", BLUE),
    ]
    agent_w, gap, x, agent_y, agent_h = 120, 9, 44, 595, 43
    centers = []
    for title, detail, fill in agents:
        page.box(x, agent_y, agent_w, agent_h, title, detail, fill, 7.8)
        centers.append(x + agent_w / 2)
        page.arrow(297, 666, x + agent_w / 2, agent_y + agent_h + 2, dash=True)
        x += agent_w + gap
    page.box(207, 532, 180, 39, "Security + Validation Gate", "evidence / syntax / safe output / approval", GOLD, 8.5)
    for center in centers:
        page.arrow(center, agent_y - 1, 297, 573, dash=True)
    page.text(55, 515, "Approved results return to comment attachment, reports, logs, and the GUI.", 7, color=MUTED)

    page.text(44, 490, "Proposed agentic operating model", 12, True, TEAL)
    paragraph = (
        "A coordinator receives a user task, creates a bounded plan, and invokes specialist agents through allow-listed project tools. Agents reuse the current parser, analyzers, generation engines, and report builders. Results and source evidence are collected in shared run state, then pass security and validation gates before comments or files are changed. Decisions are logged for review."
    )
    page.wrapped(44, 473, paragraph, max_chars=111, size=8.1, leading=11)

    rows = [
        ("Coordinator", "Plan tasks, route work, track state, handle failures, and produce a traceable run summary.", "Bounded plan; no unrestricted shell or network."),
        ("AST / context agent", "Call parser, validator, feature extraction, and context analysis; return structured evidence.", "Read-only source access."),
        ("Security agent", "Run current scanner, prioritize findings, recommend fixes; later add dependency/config checks.", "No automatic fix without validation and approval."),
        ("Generation agent", "Select rule, ML, or neurosymbolic engine; draft comments from verified AST facts.", "Sanitize output; never execute generated code."),
        ("Static analysis agent", "Use IR, CFG, DFA, and pattern detection; summarize quality findings.", "Structured tools with time/resource limits."),
        ("Validation / review gate", "Check syntax, placement, consistency, security, and requested scope before export.", "Approval for source changes; auditable logs."),
    ]
    end = page.table(44, 418, [112, 219, 176], ["Proposed agent", "Reuse / responsibility", "Control"], rows, 6.8, 8.4, 4)
    page.text(44, end - 13, "Agent planning/orchestration is proposed, not currently implemented. Existing security, ML, and neurosymbolic modules are implemented capabilities.", 7, color=MUTED)
    return page


def build_pdf():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pages = [existing_page(), proposed_page()]
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
