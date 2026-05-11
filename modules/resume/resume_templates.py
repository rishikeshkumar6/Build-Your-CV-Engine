from .resume_schema import Ai_ResumeData as ResumeData
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.platypus import KeepTogether
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    KeepTogether,
    FrameBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ── Color palette ──────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────
# Dummy palette (replace with your actual one)
# ─────────────────────────────────────────────────────────────
class Palette:
    NAVY = colors.HexColor("#0f172a")
    WHITE = colors.white
    BLUE = colors.HexColor("#2563eb")
    BLUE_LIGHT = colors.HexColor("#dbeafe")
    BLUE_BORDER = colors.HexColor("#93c5fd")
    SLATE_50 = colors.HexColor("#f8fafc")
    SLATE_200 = colors.HexColor("#e2e8f0")
    SLATE_400 = colors.HexColor("#94a3b8")
    SLATE_600 = colors.HexColor("#475569")
    SLATE_800 = colors.HexColor("#1e293b")


# ─────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────
def _style(name, **kwargs):
    return ParagraphStyle(name=name, **kwargs)


def _contact_str(d):
    return f"{d.email} | {d.phone} | {d.location}"


# ─────────────────────────────────────────────────────────────
# Main Function
# ─────────────────────────────────────────────────────────────
def build_classic_pdf(d) -> bytes:
    buf = io.BytesIO()
    W, H = A4

    HEADER_H = 90
    SIDEBAR_W = 185
    MARGIN = 18
    BODY_H = H - HEADER_H - MARGIN * 2

    # ── Header ───────────────────────────────────────────────
    def draw_header(c, doc):
        c.saveState()

        # Header background
        c.setFillColor(Palette.NAVY)
        c.rect(0, H - HEADER_H, W, HEADER_H, fill=1, stroke=0)

        # Name
        c.setFillColor(Palette.WHITE)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(28, H - 32, d.name)

        # Role
        c.setFillColor(colors.HexColor("#93c5fd"))
        c.setFont("Helvetica", 10)
        c.drawString(28, H - 48, "Software Developer")

        # Contact
        c.setFillColor(colors.HexColor("#cbd5e1"))
        c.setFont("Helvetica", 9)
        c.drawString(28, H - 64, _contact_str(d))

        # Sidebar background
        c.setFillColor(Palette.SLATE_50)
        c.rect(0, 0, SIDEBAR_W, H - HEADER_H, fill=1, stroke=0)

        # Divider line
        c.setStrokeColor(Palette.SLATE_200)
        c.setLineWidth(0.5)
        c.line(SIDEBAR_W, 0, SIDEBAR_W, H - HEADER_H)

        c.restoreState()

    # ── Styles ───────────────────────────────────────────────
    sec = _style("sec", fontName="Helvetica-Bold", fontSize=8, textColor=Palette.NAVY)
    sec_main = _style(
        "sec_main", fontName="Helvetica-Bold", fontSize=8, textColor=Palette.BLUE
    )

    name_s = _style(
        "name_s", fontName="Helvetica-Bold", fontSize=11, textColor=Palette.SLATE_800
    )
    sub_s = _style("sub_s", fontSize=9, textColor=Palette.BLUE)
    meta_s = _style("meta_s", fontSize=8, textColor=Palette.SLATE_400)
    body_s = _style("body_s", fontSize=9, textColor=Palette.SLATE_600)

    chip_s = _style(
        "chip_s",
        fontSize=8,
        textColor=Palette.BLUE,
        backColor=Palette.BLUE_LIGHT,
        borderColor=Palette.BLUE_BORDER,
        borderWidth=0.5,
        borderPadding=3,
        borderRadius=6,
    )

    # ── Sidebar Content ──────────────────────────────────────
    sidebar_story = []

    sidebar_story.append(Paragraph("SKILLS", sec))
    sidebar_story.append(HRFlowable(width="100%", thickness=1.2, color=Palette.NAVY))
    sidebar_story.append(Spacer(1, 6))

    for skill in d.skills:
        sidebar_story.append(Paragraph(skill, chip_s))
        sidebar_story.append(Spacer(1, 4))

    sidebar_story.append(Spacer(1, 10))
    sidebar_story.append(Paragraph("EDUCATION", sec))
    sidebar_story.append(HRFlowable(width="100%", thickness=1.2, color=Palette.NAVY))
    sidebar_story.append(Spacer(1, 6))

    for e in d.education:
        sidebar_story.append(Paragraph(e.degree, name_s))
        sidebar_story.append(Paragraph(e.institution, body_s))
        sidebar_story.append(Paragraph(e.year, meta_s))
        sidebar_story.append(Spacer(1, 8))

    # ── Main Content ─────────────────────────────────────────
    main_story = []

    main_story.append(Paragraph("PROFILE", sec_main))
    main_story.append(HRFlowable(width="100%", thickness=1.2, color=Palette.BLUE))
    main_story.append(Spacer(1, 6))
    main_story.append(Paragraph(d.summary, body_s))
    main_story.append(Spacer(1, 10))

    main_story.append(Paragraph("EXPERIENCE", sec_main))
    main_story.append(HRFlowable(width="100%", thickness=1.2, color=Palette.BLUE))
    main_story.append(Spacer(1, 6))

    for ex in d.experience:
        block = [
            Paragraph(ex.title, name_s),
            Paragraph(ex.company, sub_s),
            Paragraph(ex.duration, meta_s),
            Spacer(1, 4),
            Paragraph(ex.description, body_s),
            Spacer(1, 8),
        ]
        main_story.append(KeepTogether(block))

    main_story.append(Paragraph("PROJECTS", sec_main))
    main_story.append(HRFlowable(width="100%", thickness=1.2, color=Palette.BLUE))
    main_story.append(Spacer(1, 6))

    for p in d.projects:
        techs = ", ".join(t.strip() for t in p.technologies.split(",") if t.strip())
        block = [
            Paragraph(p.name, name_s),
            Paragraph(p.description, body_s),
            Paragraph(f"<font color='#2563eb'>{techs}</font>", body_s),
            Spacer(1, 8),
        ]
        main_story.append(KeepTogether(block))

    # ── Frames ───────────────────────────────────────────────
    sidebar_frame = Frame(
        MARGIN,
        MARGIN,
        SIDEBAR_W - MARGIN * 2,
        BODY_H,
        id="sidebar",
    )

    main_frame = Frame(
        SIDEBAR_W + MARGIN,
        MARGIN,
        W - SIDEBAR_W - MARGIN * 2,
        BODY_H,
        id="main",
    )

    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=0,
        rightMargin=0,
        topMargin=HEADER_H,
        bottomMargin=MARGIN,
    )

    doc.addPageTemplates(
        [
            PageTemplate(
                id="two_col", frames=[sidebar_frame, main_frame], onPage=draw_header
            )
        ]
    )

    # ── Build Story ──────────────────────────────────────────
    story = []
    story.extend(sidebar_story)
    story.append(FrameBreak())  # switch to main column
    story.extend(main_story)

    doc.build(story)

    return buf.getvalue()


def _build_classic_simple(d: ResumeData, buf: io.BytesIO):
    """Single-pass ReportLab build — reliable two-column via Table."""
    from reportlab.platypus import SimpleDocTemplate

    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0
    )

    W, H = A4
    SIDEBAR_W = 185
    MAIN_W = W - SIDEBAR_W

    # Styles
    s_sec = _style(
        "s_sec",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=Palette.NAVY,
        spaceBefore=8,
        spaceAfter=3,
    )
    s_sec_m = _style(
        "s_sec_m",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=Palette.BLUE,
        spaceBefore=8,
        spaceAfter=3,
    )
    s_name = _style(
        "s_name",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=Palette.SLATE_800,
        leading=14,
    )
    s_sub = _style("s_sub", fontSize=9, textColor=Palette.BLUE, leading=12)
    s_meta = _style("s_meta", fontSize=8, textColor=Palette.SLATE_400, leading=11)
    s_body = _style("s_body", fontSize=9, textColor=Palette.SLATE_600, leading=13)
    s_skill = _style(
        "s_skill",
        fontSize=8,
        textColor=Palette.BLUE,
        leading=13,
        leftIndent=4,
        rightIndent=4,
    )

    # ── Sidebar ────────────────────────────────────────────────────────────────
    sidebar = []
    sidebar.append(Paragraph("SKILLS", s_sec))
    sidebar.append(
        HRFlowable(width="100%", thickness=1.5, color=Palette.NAVY, spaceAfter=5)
    )
    for sk in d.skills:
        sidebar.append(Paragraph(f"• {sk}", s_skill))
    sidebar.append(Spacer(1, 10))
    sidebar.append(Paragraph("EDUCATION", s_sec))
    sidebar.append(
        HRFlowable(width="100%", thickness=1.5, color=Palette.NAVY, spaceAfter=5)
    )
    for e in d.education:
        sidebar.append(Paragraph(e.degree, s_name))
        sidebar.append(Paragraph(e.institution, s_body))
        sidebar.append(Paragraph(e.year, s_meta))
        sidebar.append(Spacer(1, 7))

    # ── Main ───────────────────────────────────────────────────────────────────
    main = []
    main.append(Paragraph("PROFILE", s_sec_m))
    main.append(
        HRFlowable(width="100%", thickness=1.5, color=Palette.BLUE, spaceAfter=5)
    )
    main.append(Paragraph(d.summary, s_body))
    main.append(Spacer(1, 10))

    main.append(Paragraph("EXPERIENCE", s_sec_m))
    main.append(
        HRFlowable(width="100%", thickness=1.5, color=Palette.BLUE, spaceAfter=5)
    )
    for ex in d.experience:
        main.append(Paragraph(ex.title, s_name))
        main.append(Paragraph(ex.company, s_sub))
        main.append(Paragraph(ex.duration, s_meta))
        main.append(Spacer(1, 2))
        main.append(Paragraph(ex.description, s_body))
        main.append(Spacer(1, 8))

    main.append(Paragraph("PROJECTS", s_sec_m))
    main.append(
        HRFlowable(width="100%", thickness=1.5, color=Palette.BLUE, spaceAfter=5)
    )
    for p in d.projects:
        techs = ", ".join(t.strip() for t in p.technologies.split(",") if t.strip())
        main.append(Paragraph(p.name, s_name))
        main.append(Paragraph(p.description, s_body))
        main.append(
            Paragraph(
                techs, _style("tp", fontSize=8, textColor=Palette.BLUE, leading=11)
            )
        )
        main.append(Spacer(1, 8))

    # ── Header row ─────────────────────────────────────────────────────────────
    contact = _contact_str(d)
    header_content = [
        Paragraph(
            f'<font color="#ffffff" size="20"><b>{d.name}</b></font>',
            _style("hn", fontSize=20, fontName="Helvetica-Bold", leading=24),
        ),
        Paragraph(
            '<font color="#93c5fd" size="10">Software Developer</font>',
            _style("hr2", fontSize=10, leading=14),
        ),
        Paragraph(
            f'<font color="#cbd5e1" size="9">{contact}</font>',
            _style("hr3", fontSize=9, leading=13),
        ),
    ]

    header_table = Table([[header_content]], colWidths=[W])
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), Palette.NAVY),
                ("LEFTPADDING", (0, 0), (-1, -1), 24),
                ("RIGHTPADDING", (0, 0), (-1, -1), 24),
                ("TOPPADDING", (0, 0), (-1, -1), 18),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    # ── Body two-column table ──────────────────────────────────────────────────
    body_table = Table([[sidebar, main]], colWidths=[SIDEBAR_W, MAIN_W])
    body_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), Palette.SLATE_50),
                ("LINEAFTER", (0, 0), (0, -1), 0.5, Palette.SLATE_200),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 16),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    doc.build([header_table, body_table])


# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE B — Modern Split  (Amber accents, skill bars)
# ══════════════════════════════════════════════════════════════════════════════


def build_modern_pdf(d: ResumeData) -> bytes:
    buf = io.BytesIO()
    W, H = A4
    MAIN_W = W - 190
    RIGHT_W = 190

    s_sec = _style(
        "ms",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=Palette.AMBER,
        spaceBefore=8,
        spaceAfter=3,
    )
    s_name = _style(
        "mn",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=Palette.GRAY_800,
        leading=14,
    )
    s_sub = _style("msu", fontSize=9, textColor=Palette.GRAY_500, leading=12)
    s_dur = _style("md", fontSize=8, textColor=Palette.AMBER, leading=11)
    s_body = _style("mb", fontSize=9, textColor=colors.HexColor("#4b5563"), leading=13)
    s_skill = _style("msk", fontSize=8, textColor=Palette.GRAY_700, leading=12)
    s_other = _style("mo", fontSize=8, textColor=Palette.GRAY_700, leading=11)

    SKILL_BARS = {
        "React.js": 92,
        "Redux Toolkit": 88,
        "RTK Query": 85,
        "Node.js": 80,
        "FastAPI": 78,
        "PostgreSQL": 75,
        "Tailwind CSS": 88,
        "MongoDB": 70,
        "Git/GitHub": 88,
    }

    def skill_bar_row(name, pct):
        bar_w = 110
        filled = int(bar_w * pct / 100)
        bar = Table(
            [[""]],
            colWidths=[filled],
            rowHeights=[3],
        )
        bar.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), Palette.AMBER),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        bg = Table([[bar, ""]], colWidths=[filled, bar_w - filled], rowHeights=[3])
        bg.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (1, 0), (-1, -1), Palette.GRAY_100),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        row = Table([[Paragraph(name, s_skill), bg]], colWidths=[68, bar_w])
        row.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        return row

    # Right column
    right = []
    right.append(Paragraph("TECH SKILLS", s_sec))
    right.append(
        HRFlowable(width="100%", thickness=1.5, color=Palette.AMBER, spaceAfter=5)
    )
    for sk, pct in SKILL_BARS.items():
        right.append(skill_bar_row(sk, pct))
    right.append(Spacer(1, 4))
    for sk in d.skills:
        if sk not in SKILL_BARS:
            right.append(Paragraph(f"• {sk}", s_other))
    right.append(Spacer(1, 12))
    right.append(Paragraph("EDUCATION", s_sec))
    right.append(
        HRFlowable(width="100%", thickness=1.5, color=Palette.AMBER, spaceAfter=5)
    )
    for e in d.education:
        right.append(Paragraph(e.degree, s_name))
        right.append(Paragraph(e.institution, s_sub))
        right.append(Paragraph(e.year, s_dur))
        right.append(Spacer(1, 7))

    # Left column
    left = []
    left.append(Paragraph("EXPERIENCE", s_sec))
    left.append(
        HRFlowable(width="100%", thickness=1.5, color=Palette.AMBER, spaceAfter=5)
    )
    for ex in d.experience:
        left.append(Paragraph(ex.title, s_name))
        left.append(Paragraph(ex.company, s_sub))
        left.append(Paragraph(ex.duration, s_dur))
        left.append(Spacer(1, 2))
        left.append(Paragraph(ex.description, s_body))
        left.append(Spacer(1, 8))
    left.append(Paragraph("PROJECTS", s_sec))
    left.append(
        HRFlowable(width="100%", thickness=1.5, color=Palette.AMBER, spaceAfter=5)
    )
    for p in d.projects:
        techs = ", ".join(t.strip() for t in p.technologies.split(",") if t.strip())
        left.append(Paragraph(p.name, s_name))
        left.append(Paragraph(p.description, s_body))
        left.append(
            Paragraph(
                techs, _style("tp2", fontSize=8, textColor=Palette.AMBER, leading=11)
            )
        )
        left.append(Spacer(1, 8))

    # Header
    contact_parts = [x for x in [d.email, d.phone, d.location] if x]
    contact_right = "\n".join(contact_parts)
    hdr = Table(
        [
            [
                [
                    Paragraph(
                        f'<font color="#111827"><b>{d.name}</b></font>',
                        _style(
                            "mhn", fontName="Helvetica-Bold", fontSize=20, leading=26
                        ),
                    ),
                    Paragraph(
                        '<font color="#f59e0b"><b>Software Developer · 2.2 Years Experience</b></font>',
                        _style("mht", fontSize=10, leading=14),
                    ),
                ],
                Paragraph(
                    f'<font color="#6b7280">{contact_right}</font>',
                    _style("mhc", fontSize=9, leading=14, alignment=TA_RIGHT),
                ),
            ]
        ],
        colWidths=[W * 0.62, W * 0.38],
    )
    hdr.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 24),
                ("RIGHTPADDING", (0, 0), (-1, -1), 24),
                ("TOPPADDING", (0, 0), (-1, -1), 20),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("LINEBELOW", (0, 0), (-1, -1), 3, Palette.AMBER),
            ]
        )
    )

    summary_block = Table(
        [
            [
                Paragraph(
                    d.summary,
                    _style(
                        "ms2",
                        fontSize=9,
                        textColor=colors.HexColor("#4b5563"),
                        leading=14,
                    ),
                )
            ]
        ],
        colWidths=[W],
    )
    summary_block.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 24),
                ("RIGHTPADDING", (0, 0), (-1, -1), 24),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, Palette.GRAY_100),
            ]
        )
    )

    body = Table([[left, right]], colWidths=[MAIN_W, RIGHT_W])
    body.setStyle(
        TableStyle(
            [
                ("LINEBEFORE", (1, 0), (-1, -1), 0.5, Palette.GRAY_100),
                ("LEFTPADDING", (0, 0), (-1, -1), 20),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                ("TOPPADDING", (0, 0), (-1, -1), 16),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0
    )
    doc.build([hdr, summary_block, body])
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE C — Minimal Line  (Emerald accents, clean lines)
# ══════════════════════════════════════════════════════════════════════════════


def build_minimal_pdf(d: ResumeData) -> bytes:
    buf = io.BytesIO()
    W, H = A4
    MAIN_W = W - 175
    RIGHT_W = 175

    s_sec = _style(
        "cs",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=Palette.EMERALD,
        spaceBefore=8,
        spaceAfter=3,
    )
    s_name = _style(
        "cn",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=Palette.GRAY_800,
        leading=14,
    )
    s_sub = _style("csu", fontSize=9, textColor=Palette.EMERALD, leading=12)
    s_meta = _style("cm", fontSize=8, textColor=colors.HexColor("#9ca3af"), leading=11)
    s_body = _style("cb", fontSize=9, textColor=colors.HexColor("#4b5563"), leading=13)
    s_skill = _style(
        "csk", fontSize=9, textColor=colors.HexColor("#334155"), leading=14
    )

    # Right column
    right = []
    right.append(Paragraph("SKILLS", s_sec))
    right.append(
        HRFlowable(width="100%", thickness=1.5, color=Palette.EMERALD, spaceAfter=5)
    )
    for sk in d.skills:
        right.append(Paragraph(sk, s_skill))
        right.append(
            HRFlowable(
                width="100%", thickness=0.3, color=Palette.SLATE_100, spaceAfter=1
            )
        )
    right.append(Spacer(1, 12))
    right.append(Paragraph("EDUCATION", s_sec))
    right.append(
        HRFlowable(width="100%", thickness=1.5, color=Palette.EMERALD, spaceAfter=5)
    )
    for e in d.education:
        right.append(Paragraph(e.degree, s_name))
        right.append(Paragraph(e.institution, s_body))
        right.append(
            Paragraph(
                e.year, _style("cy", fontSize=8, textColor=Palette.EMERALD, leading=11)
            )
        )
        right.append(Spacer(1, 7))

    # Left column — experience with left border accent via Table
    def accented_block(items):
        inner = Table([[items]], colWidths=[MAIN_W - 50])
        inner.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("LINEBEFORE", (0, 0), (-1, -1), 2, Palette.EMERALD_LIGHT),
                ]
            )
        )
        return inner

    left = []
    left.append(Paragraph("EXPERIENCE", s_sec))
    left.append(
        HRFlowable(width="100%", thickness=1.5, color=Palette.EMERALD, spaceAfter=5)
    )
    for ex in d.experience:
        block = [
            Paragraph(ex.title, s_name),
            Paragraph(ex.company, s_sub),
            Paragraph(ex.duration, s_meta),
            Spacer(1, 3),
            Paragraph(ex.description, s_body),
            Spacer(1, 6),
        ]
        left.append(accented_block(block))
        left.append(Spacer(1, 4))

    left.append(Paragraph("PROJECTS", s_sec))
    left.append(
        HRFlowable(width="100%", thickness=1.5, color=Palette.EMERALD, spaceAfter=5)
    )
    for p in d.projects:
        block = [
            Paragraph(p.name, s_name),
            Paragraph(p.description, s_body),
            Paragraph(
                p.technologies,
                _style("pt", fontSize=8, textColor=Palette.EMERALD, leading=11),
            ),
            Spacer(1, 6),
        ]
        left.append(accented_block(block))
        left.append(Spacer(1, 4))

    # Header
    contact = _contact_str(d)
    hdr_inner = [
        Paragraph(
            f'<font size="28"><b>{d.name}</b></font>',
            _style(
                "chn",
                fontName="Helvetica",
                fontSize=28,
                leading=34,
                textColor=Palette.GRAY_800,
            ),
        ),
        Spacer(1, 6),
        HRFlowable(width=50, thickness=3, color=Palette.EMERALD, spaceAfter=8),
        Paragraph(
            f'<font color="#6b7280">{contact}</font>   '
            f'<font color="#10b981"><b>Software Developer</b></font>',
            _style("chc", fontSize=9, leading=13),
        ),
    ]

    hdr = Table([[hdr_inner]], colWidths=[W])
    hdr.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 36),
                ("RIGHTPADDING", (0, 0), (-1, -1), 36),
                ("TOPPADDING", (0, 0), (-1, -1), 28),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    summary_block = Table(
        [
            [
                Paragraph(
                    d.summary,
                    _style(
                        "cs2",
                        fontSize=9,
                        textColor=colors.HexColor("#4b5563"),
                        leading=14,
                    ),
                )
            ]
        ],
        colWidths=[W],
    )
    summary_block.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 36),
                ("RIGHTPADDING", (0, 0), (-1, -1), 36),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, Palette.SLATE_100),
            ]
        )
    )

    body = Table([[left, right]], colWidths=[MAIN_W, RIGHT_W])
    body.setStyle(
        TableStyle(
            [
                ("LINEBEFORE", (1, 0), (-1, -1), 0.5, Palette.SLATE_100),
                ("LEFTPADDING", (0, 0), (-1, -1), 28),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                ("TOPPADDING", (0, 0), (-1, -1), 16),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0
    )
    doc.build([hdr, summary_block, body])
    return buf.getvalue()


# ── Template map ───────────────────────────────────────────────────────────────

TEMPLATE_BUILDERS = {
    "classic": build_classic_pdf,
    "modern": build_modern_pdf,
    "minimal": build_minimal_pdf,
}
