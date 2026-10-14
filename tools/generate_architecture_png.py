from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "architecture.png"
WIDTH, HEIGHT = 1980, 1390
COLORS = {
    "background": "#f7f9fc",
    "ink": "#19334a",
    "muted": "#536879",
    "line": "#94a5b2",
    "blue": "#e1edfb",
    "blue_accent": "#4a7fc1",
    "teal": "#def2ee",
    "teal_accent": "#258f82",
    "gold": "#fff1cd",
    "gold_accent": "#d99b24",
    "red": "#fde5e2",
    "red_accent": "#cf6b61",
    "green": "#e2f1e3",
    "green_accent": "#4e9562",
    "peach": "#fce9dd",
    "peach_accent": "#cb7950",
    "white": "#ffffff",
    "shadow": "#e3e9ef",
}


def get_font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def draw_box(draw, bounds, title, detail, fill, accent, title_font, body_font):
    left, top, right, bottom = bounds
    draw.rounded_rectangle(
        (left + 4, top + 5, right + 4, bottom + 5),
        radius=16,
        fill=COLORS["shadow"],
    )
    draw.rounded_rectangle(bounds, radius=16, fill=fill, outline="#d2dce5", width=2)
    draw.rounded_rectangle((left, top, left + 9, bottom), radius=5, fill=accent)
    draw.text((left + 24, top + 14), title, font=title_font, fill=COLORS["ink"])
    y = top + 52
    max_width = right - left - 42
    for line in detail.split("\n"):
        words = line.split()
        wrapped = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if current and draw.textbbox((0, 0), candidate, font=body_font)[2] > max_width:
                wrapped.append(current)
                current = word
            else:
                current = candidate
        if current:
            wrapped.append(current)
        for wrapped_line in wrapped:
            draw.text((left + 24, y), wrapped_line, font=body_font, fill=COLORS["muted"])
            y += 25


def connector(draw, points, dashed=False, color=None, arrow_end=True, width=3):
    color = color or COLORS["line"]
    for start, end in zip(points, points[1:]):
        x1, y1 = start
        x2, y2 = end
        if dashed:
            distance = max(abs(x2 - x1), abs(y2 - y1))
            for offset in range(0, distance, 18):
                end_offset = min(offset + 10, distance)
                scale_a = offset / max(distance, 1)
                scale_b = end_offset / max(distance, 1)
                draw.line(
                    (x1 + (x2 - x1) * scale_a, y1 + (y2 - y1) * scale_a,
                     x1 + (x2 - x1) * scale_b, y1 + (y2 - y1) * scale_b),
                    fill=color,
                    width=width,
                )
        else:
            draw.line((x1, y1, x2, y2), fill=color, width=width)

    if not arrow_end:
        return

    x1, y1 = points[-2]
    x2, y2 = points[-1]
    dx, dy = x2 - x1, y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux, uy = dx / length, dy / length
    size = 12
    left = (x2 - size * ux - size * uy * 0.6, y2 - size * uy + size * ux * 0.6)
    right = (x2 - size * ux + size * uy * 0.6, y2 - size * uy - size * ux * 0.6)
    draw.polygon(((x2, y2), left, right), fill=color)


def arrow(draw, start, end, dashed=False, color=None, width=3):
    connector(draw, [start, end], dashed=dashed, color=color, width=width)


def build_image():
    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["background"])
    draw = ImageDraw.Draw(image)
    title_font = get_font(38, True)
    subtitle_font = get_font(19)
    section_font = get_font(15, True)
    box_title = get_font(21, True)
    box_body = get_font(16)
    label_font = get_font(15, True)

    draw.text((70, 42), "Code Comment Generation using AST + NLP", font=title_font, fill=COLORS["ink"])
    draw.text((72, 100), "Architecture overview  /  rule-based, ML, neurosymbolic, and optional LLM review",
              font=subtitle_font, fill=COLORS["muted"])
    draw.rounded_rectangle((70, 140, 1910, 147), radius=3, fill=COLORS["teal_accent"])

    draw.text((80, 160), "SOURCE ANALYSIS", font=section_font, fill=COLORS["teal_accent"])
    top = [
        ((70, 190, 390, 315), "Input interfaces", "CLI: src.main\nGUI: PyQt6 generator", COLORS["blue"], COLORS["blue_accent"]),
        ((470, 190, 810, 315), "Parse and validate", "parser_module.py\nvalidator.py / Python AST", COLORS["blue"], COLORS["blue_accent"]),
        ((890, 190, 1250, 315), "Program understanding", "ast_extractor.py\ncontext_analyzer.py", COLORS["teal"], COLORS["teal_accent"]),
        ((1330, 190, 1680, 315), "Security analysis + gate", "security_analyzer.py\nsecurity_agent.py adapter", COLORS["gold"], COLORS["gold_accent"]),
    ]
    for bounds, heading, detail, fill, accent in top:
        draw_box(draw, bounds, heading, detail, fill, accent, box_title, box_body)
    for start, end in [((390, 252), (470, 252)), ((810, 252), (890, 252)), ((1250, 252), (1330, 252))]:
        arrow(draw, start, end, color=COLORS["line"])

    draw_box(draw, (1710, 203, 1910, 303), "Blocked", "Findings +\nremediation", COLORS["red"], COLORS["red_accent"], box_title, box_body)
    arrow(draw, (1680, 252), (1710, 252), color=COLORS["red_accent"])

    draw.text((160, 390), "GENERATE AND ATTACH", font=section_font, fill=COLORS["green_accent"])
    generation = (150, 440, 700, 605)
    review = (790, 440, 1210, 605)
    attach = (1300, 440, 1780, 605)
    draw_box(draw, generation, "Comment generation", "comment_generator.py: rule-based\nml/: T5 AST + NLP\nneurosymbolic/: fusion + validation",
             COLORS["green"], COLORS["green_accent"], box_title, box_body)
    draw_box(draw, review, "Optional LLM reviewer", "llm_review_agent.py\nGrounded in each source snippet\nRevises summary line only",
             COLORS["gold"], COLORS["gold_accent"], box_title, box_body)
    draw_box(draw, attach, "Attach comments", "comment_attacher.py\nProduces annotated Python source",
             COLORS["blue"], COLORS["blue_accent"], box_title, box_body)

    connector(draw, [(1505, 315), (1505, 365), (425, 365), (425, 440)], color=COLORS["teal_accent"])
    draw.text((1430, 333), "PASS", font=label_font, fill=COLORS["teal_accent"])
    arrow(draw, (700, 522), (790, 522), color=COLORS["line"])
    arrow(draw, (1210, 522), (1300, 522), color=COLORS["line"])
    connector(draw, [(660, 440), (660, 410), (1540, 410), (1540, 440)],
              dashed=True, color=COLORS["gold_accent"])
    draw.text((874, 382), "Bypass when LLM review is disabled", font=label_font, fill=COLORS["gold_accent"])
    draw.text((830, 622), "Opt-in: --agent-review or the GUI checkbox", font=label_font, fill=COLORS["gold_accent"])

    draw.text((80, 685), "MODEL AND ANALYSIS LAYERS", font=section_font, fill=COLORS["blue_accent"])
    training = (100, 720, 570, 865)
    ir = (740, 720, 1240, 865)
    outputs = (1390, 720, 1860, 865)
    draw_box(draw, training, "Training and evaluation", "ml/trainer.py + evaluator.py\nDataset builder, AST formatter, metrics",
             COLORS["peach"], COLORS["peach_accent"], box_title, box_body)
    draw_box(draw, ir, "Intermediate representation", "ir/ builder, nodes, serializer\nStructured functions and basic blocks",
             COLORS["blue"], COLORS["blue_accent"], box_title, box_body)
    draw_box(draw, outputs, "Outputs and observability", "Annotated source, JSON reports, logs\nGUI: training, insights, security, logs",
             COLORS["green"], COLORS["green_accent"], box_title, box_body)
    arrow(draw, (335, 720), (335, 605), dashed=True, color=COLORS["peach_accent"])
    connector(draw, [(1540, 605), (1540, 665), (990, 665), (990, 720)], color=COLORS["line"])
    connector(draw, [(1780, 560), (1835, 560), (1835, 720)], dashed=True, color=COLORS["green_accent"])

    draw.text((130, 930), "STATIC ANALYSIS", font=section_font, fill=COLORS["teal_accent"])
    analysis_boxes = [
        ((80, 970, 620, 1115), "Control-flow analysis", "analysis/cfg_builder.py\nBasic blocks and control-flow graph"),
        ((720, 970, 1260, 1115), "Data-flow analysis", "analysis/dfa_engine.py\nReaching definitions and liveness"),
        ((1360, 970, 1900, 1115), "Pattern analysis", "analysis/pattern_detector.py\nCode-quality findings"),
    ]
    for bounds, heading, detail in analysis_boxes:
        draw_box(draw, bounds, heading, detail, COLORS["teal"], COLORS["teal_accent"], box_title, box_body)
    connector(draw, [(990, 865), (990, 915)], color=COLORS["line"], arrow_end=False)
    connector(draw, [(350, 915), (1630, 915)], color=COLORS["line"], arrow_end=False)
    for center in (350, 990, 1630):
        arrow(draw, (center, 915), (center, 970), color=COLORS["line"])

    connector(draw, [(990, 1115), (990, 1190)], color=COLORS["green_accent"])
    draw.rounded_rectangle((260, 1205, 1720, 1320), radius=18, fill=COLORS["green"], outline="#cbdccb", width=2)
    draw.rounded_rectangle((260, 1205, 270, 1320), radius=5, fill=COLORS["green_accent"])
    draw.text((292, 1225), "Reports and artifacts", font=box_title, fill=COLORS["ink"])
    draw.text((292, 1272), "Annotated .py  |  Security and pattern findings  |  Pipeline logs  |  Evaluation metrics",
              font=box_body, fill=COLORS["muted"])

    draw.text((70, 1350), "Security checks run before generation. Source snippets are sent to an LLM only when review is enabled.",
              font=subtitle_font, fill=COLORS["muted"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, format="PNG", optimize=True)
    return OUTPUT


if __name__ == "__main__":
    print(build_image())