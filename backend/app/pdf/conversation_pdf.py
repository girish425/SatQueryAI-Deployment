import os
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)


def generate_conversation_pdf(conversation: Dict[str, Any], static_evidence_dir: str = "./evidence") -> io.BytesIO:
    """
    Generate a professional, publication-quality satellite analysis report PDF using ReportLab.
    Includes metadata, chronological Q&A flow, natural-language answers, key findings, and embedded evidence images.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold',
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=12
    )
    section_heading = ParagraphStyle(
        'SecHead',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0284c7'),
        fontName='Helvetica-Bold',
        spaceBefore=10,
        spaceAfter=6
    )
    user_bubble = ParagraphStyle(
        'UserText',
        parent=styles['Normal'],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold'
    )
    answer_text = ParagraphStyle(
        'AnswerText',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e293b')
    )
    finding_item = ParagraphStyle(
        'FindingItem',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155'),
        leftIndent=12
    )
    meta_tag = ParagraphStyle(
        'MetaTag',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#475569')
    )

    elements = []

    # Header Banner
    header_data = [
        [
            Paragraph("<b>SATQUERY AI</b><br/><font size=8 color='#64748b'>Multimodal Remote Sensing Vision-Language Assistant</font>", title_style),
            Paragraph(f"<b>Session ID:</b> {conversation.get('session_id', 'N/A')[:8]}...<br/><b>Export Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", meta_tag)
        ]
    ]
    header_table = Table(header_data, colWidths=[380, 160])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=14))

    # Conversation Title
    elements.append(Paragraph(f"<b>Conversation:</b> {conversation.get('title', 'Satellite Analysis Session')}", subtitle_style))
    elements.append(Spacer(1, 8))

    messages: List[Dict[str, Any]] = conversation.get("messages", [])

    if not messages:
        elements.append(Paragraph("<i>No messages recorded in this session.</i>", styles['Normal']))
    else:
        turn_num = 1
        for msg in messages:
            role = msg.get("role", "user")

            if role == "user":
                # User Question Box
                u_text = msg.get("message", "")
                images = msg.get("image_ids", [])
                img_str = f" [Attached: {', '.join(images)}]" if images else ""
                
                u_content = [
                    [Paragraph(f"<b>User Query #{turn_num}:</b> {u_text}{img_str}", user_bubble)]
                ]
                u_table = Table(u_content, colWidths=[540])
                u_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                    ('PADDING', (0, 0), (-1, -1), 8),
                    ('ROUNDEDCORNERS', [4, 4, 4, 4]),
                ]))
                elements.append(KeepTogether([u_table, Spacer(1, 8)]))

            elif role == "assistant":
                turn_num += 1
                asst_elements = []

                intent = msg.get("intent", "Analysis")
                model = msg.get("model_used", "RS Model")
                confidence = msg.get("confidence") or (msg.get("technical_details", {}).get("intent_confidence", 0.85))
                conf_str = f"{int(confidence * 100)}%" if isinstance(confidence, (int, float)) else str(confidence)
                proc_time = msg.get("processing_time") or msg.get("technical_details", {}).get("processing_time_sec", 0.0)

                # AI Badges banner
                badge_text = (
                    f"<b>Model:</b> {model} | <b>Intent:</b> {intent} | "
                    f"<b>Confidence:</b> {conf_str} | <b>Time:</b> {proc_time}s"
                )
                asst_elements.append(Paragraph(badge_text, meta_tag))
                asst_elements.append(Spacer(1, 4))

                # Answer Summary
                ans_obj = msg.get("answer")
                if isinstance(ans_obj, dict):
                    summary = ans_obj.get("summary", "")
                    findings = ans_obj.get("key_findings", [])
                    explanation = ans_obj.get("explanation", "")
                else:
                    summary = msg.get("message", "")
                    findings = []
                    explanation = ""

                asst_elements.append(Paragraph(f"<b>Answer:</b> {summary}", answer_text))
                asst_elements.append(Spacer(1, 4))

                if findings:
                    asst_elements.append(Paragraph("<b>Key Findings:</b>", styles['Normal']))
                    for f in findings:
                        asst_elements.append(Paragraph(f"• {f}", finding_item))
                    asst_elements.append(Spacer(1, 4))

                if explanation:
                    asst_elements.append(Paragraph(f"<i>Technical Context:</i> {explanation}", styles['Italic']))
                    asst_elements.append(Spacer(1, 6))

                # Embed Evidence Images if available
                evidence = msg.get("evidence", {})
                if evidence:
                    img_to_embed = evidence.get("difference_image") or evidence.get("overlay_image") or evidence.get("original_image")
                    if img_to_embed:
                        # Translate URL path to local disk path
                        local_path = img_to_embed.replace("/evidence/", "").replace("evidence/", "")
                        full_img_path = Path(static_evidence_dir) / local_path
                        if full_img_path.exists():
                            try:
                                rl_img = RLImage(str(full_img_path), width=240, height=180)
                                asst_elements.append(Spacer(1, 4))
                                asst_elements.append(Paragraph("<b>Visual Evidence:</b>", meta_tag))
                                asst_elements.append(rl_img)
                                asst_elements.append(Spacer(1, 6))
                            except Exception as e:
                                pass

                # Wrap assistant reply in nice box
                ai_table = Table([[asst_elements]], colWidths=[540])
                ai_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#0284c7')),
                    ('PADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(KeepTogether([ai_table, Spacer(1, 12)]))

    doc.build(elements)
    buffer.seek(0)
    return buffer
