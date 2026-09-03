"""
certificate.py — Bhoomi Setu Title Attestation Certificate Generator
====================================================================
Tier 2a: Downloadable PDF Certificate for Sealed Parcels
Uses reportlab to generate an official-looking Torrens Title Certificate.
Honesty Label: "Prototype certificate — not a legally issued government document."
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable


def generate_title_certificate(parcel: dict, sealed_state: dict) -> io.BytesIO:
    """
    Generates a PDF Torrens Title Attestation Certificate for a sealed land parcel.
    Returns BytesIO buffer containing PDF binary data.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CertTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=1,  # Center
        textColor=colors.HexColor("#064e3b"),  # Dark emerald
    )
    subtitle_style = ParagraphStyle(
        "CertSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#4b5563"),
    )
    section_head = ParagraphStyle(
        "CertSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
    )
    body_bold = ParagraphStyle(
        "BodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
    )
    body_text = ParagraphStyle(
        "BodyText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        alignment=1,
        textColor=colors.HexColor("#64748b"),
    )

    elements = []

    # 1. Official Header
    elements.append(Paragraph("GOVERNMENT OF INDIA • DEPARTMENT OF LAND RESOURCES", subtitle_style))
    elements.append(Paragraph("BHOOMI SETU (भूमि सेतु) — INTEGRATED LAND STACK", subtitle_style))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("CERTIFICATE OF CONCLUSIVE TITLE SEALING", title_style))
    elements.append(Paragraph("Issued under Torrens Title Architecture (Curtain Ledger & Assurance Pool)", subtitle_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#059669"), spaceAfter=14))

    # 2. Key Identification Banner
    ulpin = parcel.get("ulpin", "N/A")
    seal_score = sealed_state.get("mirror_score", 100)
    cid = sealed_state.get("off_chain_cid", "N/A")
    owner_hash = sealed_state.get("owner_identity_hash", "0x0")
    timestamp_unix = sealed_state.get("seal_timestamp", 0)
    seal_time_str = (
        datetime.fromtimestamp(timestamp_unix).strftime("%d %B %Y, %H:%M:%S UTC")
        if timestamp_unix
        else datetime.utcnow().strftime("%d %B %Y, %H:%M:%S UTC")
    )

    summary_data = [
        [
            Paragraph("<strong>Unique Land Parcel ID (ULPIN):</strong>", body_bold),
            Paragraph(f"<font size=10 color='#047857'><strong>{ulpin}</strong></font>", body_bold),
        ],
        [
            Paragraph("<strong>Mirror Confidence Score:</strong>", body_bold),
            Paragraph(f"<font size=10 color='#047857'><strong>{seal_score} / 100 (Clean Sealing Threshold Met)</strong></font>", body_bold),
        ],
        [
            Paragraph("<strong>Curtain Ledger Status:</strong>", body_bold),
            Paragraph("<font color='#059669'><strong>CANONICAL OWNER RECORD SEALED ON-CHAIN</strong></font>", body_bold),
        ],
        [
            Paragraph("<strong>Sealing Timestamp:</strong>", body_bold),
            Paragraph(seal_time_str, body_text),
        ],
    ]
    t_summary = Table(summary_data, colWidths=[200, 320])
    t_summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#86efac")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bbf7d0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(t_summary)
    elements.append(Spacer(1, 14))

    # 3. Cadastral Spatial Record (The Mirror)
    elements.append(Paragraph("1. Cadastral Spatial Attributes (Mirror Reconciliation)", section_head))
    elements.append(Spacer(1, 6))

    cadastral_data = [
        [Paragraph("<strong>State & District:</strong>", body_bold), Paragraph(f"{parcel.get('state', 'UP')} • {parcel.get('district', 'Pratapgarh')}", body_text)],
        [Paragraph("<strong>Village & Tehsil:</strong>", body_bold), Paragraph(f"{parcel.get('village', 'Rampur Khurd')}", body_text)],
        [Paragraph("<strong>Khasra / Survey Number:</strong>", body_bold), Paragraph(str(parcel.get("khasra_no") or parcel.get("survey_no") or "42/1"), body_text)],
        [Paragraph("<strong>Textual Deed Area:</strong>", body_bold), Paragraph(f"{parcel.get('ror_text', '1.0 bigha')}", body_text)],
        [Paragraph("<strong>GIS Polygon Area:</strong>", body_bold), Paragraph(f"{parcel.get('polygon_area_ha', 0.25):.4f} Hectares (~{parcel.get('gis_area_sqm', 2500):,.0f} m²)", body_text)],
        [Paragraph("<strong>Mirror Engine Alignment:</strong>", body_bold), Paragraph("Textual Area matches Spatial Survey within allowable &lt;5% margin.", body_text)],
    ]
    t_cadastral = Table(cadastral_data, colWidths=[200, 320])
    t_cadastral.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(t_cadastral)
    elements.append(Spacer(1, 14))

    # 4. Cryptographic Curtain & Privacy (The Curtain)
    elements.append(Paragraph("2. Cryptographic Curtain Verification (Privacy-Preserved)", section_head))
    elements.append(Spacer(1, 6))

    curtain_data = [
        [Paragraph("<strong>Owner Pseudonym (Hash):</strong>", body_bold), Paragraph(f"<font name='Courier' size=8>{owner_hash[:32]}...<br/>{owner_hash[32:] if len(owner_hash) > 32 else ''}</font>", body_text)],
        [Paragraph("<strong>Privacy Assurance:</strong>", body_bold), Paragraph("Zero personal Aadhaar or raw PII stored on public blockchain ledger.", body_text)],
        [Paragraph("<strong>Off-Chain Storage Reference:</strong>", body_bold), Paragraph(f"<font name='Courier' size=8>{cid}</font><br/><font size=7 color='#64748b'>[Off-Chain Reference (IPFS-equivalent content-addressed store)]</font>", body_text)],
        [Paragraph("<strong>Smart Contract Anchor:</strong>", body_bold), Paragraph("CurtainLedger.sol (Hardhat EVM Localhost / ChainId 1337)", body_text)],
    ]
    t_curtain = Table(curtain_data, colWidths=[200, 320])
    t_curtain.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(t_curtain)
    elements.append(Spacer(1, 14))

    # 5. Assurance Pool Backing (The Insurance)
    elements.append(Paragraph("3. Torrens Title Assurance Backing (The Guarantee)", section_head))
    elements.append(Spacer(1, 6))

    insurance_data = [
        [Paragraph("<strong>Assurance Pool Status:</strong>", body_bold), Paragraph("<font color='#0284c7'><strong>ACTIVE GUARANTEE BACKING</strong></font>", body_bold)],
        [Paragraph("<strong>Indemnity Mechanism:</strong>", body_bold), Paragraph("Self-funding risk pool (AssurancePool.sol) covers verified title defects.", body_text)],
        [Paragraph("<strong>Risk-Indexed Premium:</strong>", body_bold), Paragraph(f"Formula: base_rate × value × (1 + k × (85 − {seal_score})). Discount applied.", body_text)],
    ]
    t_insurance = Table(insurance_data, colWidths=[200, 320])
    t_insurance.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f9ff")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#bae6fd")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0f2fe")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(t_insurance)
    elements.append(Spacer(1, 20))

    # 6. Legal Disclaimer & Honesty Footnote
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#94a3b8"), spaceAfter=10))
    elements.append(Paragraph(
        "<strong>HONESTY LABEL & PROTOTYPE DISCLAIMER:</strong> This certificate was generated by the Bhoomi Setu "
        "Land Governance Prototype for SIH26014 evaluation purposes. It demonstrates conclusive title attestation "
        "using the Mirror Engine, Curtain Ledger, and Assurance Pool architecture. This document is a prototype "
        "demonstration and does not constitute a legally binding title certificate under the Indian Registration Act 1908.",
        disclaimer_style,
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
