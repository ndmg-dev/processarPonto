from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from app.models.schemas import PointStatus

# Paleta alinhada ao tema do sistema (dourado + status success/warning/error).
GOLD = colors.HexColor('#d4a843')
GOLD_LIGHT = colors.HexColor('#faf3e2')
SUCCESS = colors.HexColor('#22c55e')
SUCCESS_LIGHT = colors.HexColor('#e8f9ee')
WARNING = colors.HexColor('#f59e0b')
WARNING_LIGHT = colors.HexColor('#fef3dd')
ERROR = colors.HexColor('#ef4444')
ERROR_LIGHT = colors.HexColor('#fde8e8')
TEXT_DARK = colors.HexColor('#1a1a1a')
TEXT_MUTED = colors.HexColor('#6b6b6b')
BORDER = colors.HexColor('#d9d9d9')

STATUS_ROW_COLOR = {
    PointStatus.INCONSISTENCIA: WARNING_LIGHT,
    PointStatus.FALTA: ERROR_LIGHT,
    PointStatus.TRABALHADO: SUCCESS_LIGHT,
    PointStatus.TRABALHADO_PARCIAL: SUCCESS_LIGHT,
    PointStatus.TRABALHADO_COM_OCORRENCIA: GOLD_LIGHT,
}

def _night_additional_to_minutes(value: str) -> int:
    value = value or '00:00'
    h, m = value.split(':')
    return int(h) * 60 + int(m)

def _minutes_to_str(total_minutes: int) -> str:
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"

def _header_table_style(header_bg=GOLD, header_text=TEXT_DARK):
    return [
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('TEXTCOLOR', (0, 0), (-1, 0), header_text),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

def _summary_cards(summary: dict, total_records: int) -> Table:
    """
    Recria visualmente os cards de resumo mostrados na tela de detalhe do
    colaborador (Registros / Trabalhados / Inconsistências / Adicional Noturno).
    """
    cards = [
        ("REGISTROS", str(total_records), TEXT_DARK, colors.HexColor('#f2f2f2')),
        ("TRABALHADOS", str(summary.get('worked_days', 0)), SUCCESS, SUCCESS_LIGHT),
        ("INCONSISTÊNCIAS", str(summary.get('inconsistencies', 0)), WARNING, WARNING_LIGHT),
        ("ADICIONAL NOTURNO", summary.get('night_additional_total', '00:00'), colors.HexColor('#8a6d1f'), GOLD_LIGHT),
    ]

    styles = getSampleStyleSheet()
    label_style = ParagraphStyle('CardLabel', parent=styles['Normal'], fontSize=7.5, textColor=TEXT_MUTED, alignment=1, fontName='Helvetica-Bold')
    value_style_base = ParagraphStyle('CardValue', parent=styles['Normal'], fontSize=15, alignment=1, fontName='Helvetica-Bold')

    row_labels = []
    row_values = []
    for label, value, value_color, _bg in cards:
        row_labels.append(Paragraph(label, label_style))
        value_style = ParagraphStyle('CardValueColored', parent=value_style_base, textColor=value_color)
        row_values.append(Paragraph(value, value_style))

    table = Table([row_labels, row_values], colWidths=[4.25 * cm] * 4)
    style_cmds = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
    ]
    for i, (_label, _value, _color, bg) in enumerate(cards):
        style_cmds.append(('BACKGROUND', (i, 0), (i, 1), bg))
        style_cmds.append(('LINEAFTER', (i, 0), (i, 1), 0.5, colors.white))
    table.setStyle(TableStyle(style_cmds))
    return table

def generate_pdf_report(data: dict, output_path: str) -> str:
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], textColor=TEXT_DARK)
    heading1_style = ParagraphStyle('CustomHeading1', parent=styles['Heading1'], textColor=TEXT_DARK)
    normal_style = styles['Normal']

    custom_normal = ParagraphStyle(
        'CustomNormal',
        parent=normal_style,
        fontSize=9,
        textColor=TEXT_DARK
    )
    name_style = ParagraphStyle(
        'EmployeeName',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=TEXT_DARK,
        spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'EmployeeSubtitle',
        parent=normal_style,
        fontSize=10,
        textColor=TEXT_MUTED
    )

    story = []

    # 1. Capa
    story.append(Paragraph("Relatório de Processamento de Ponto", title_style))
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(f"<b>Arquivo:</b> {data.get('file_name', '')}", custom_normal))
    story.append(Paragraph(f"<b>Total de Colaboradores:</b> {data.get('total_employees', 0)}", custom_normal))
    story.append(Spacer(1, 4*cm))
    story.append(PageBreak())

    # 2. Resumo geral
    story.append(Paragraph("Resumo Geral", heading1_style))
    story.append(Spacer(1, 0.5*cm))

    total_records = 0
    total_folgas = 0
    total_ferias = 0
    total_atestados = 0
    total_faltas = 0
    total_inconsistencias = 0
    total_night_additional_minutes = 0

    for emp in data.get('employees', []):
        total_records += len(emp.get('records', []))
        summary = emp.get('summary', {})
        total_folgas += summary.get('days_off', 0)
        total_ferias += summary.get('vacation_days', 0)
        total_atestados += summary.get('medical_days', 0)
        total_faltas += summary.get('absence_days', 0)
        total_inconsistencias += summary.get('inconsistencies', 0)
        total_night_additional_minutes += _night_additional_to_minutes(summary.get('night_additional_total', '00:00'))

    total_night_additional_str = _minutes_to_str(total_night_additional_minutes)

    summary_data = [
        ["Métrica", "Quantidade"],
        ["Total de Colaboradores", data.get('total_employees', 0)],
        ["Total de Registros", total_records],
        ["Total de Folgas/Domingos", total_folgas],
        ["Total de Férias", total_ferias],
        ["Total de Atestados", total_atestados],
        ["Total de Faltas", total_faltas],
        ["Total de Inconsistências", total_inconsistencias],
        ["Total de Adicional Noturno", total_night_additional_str]
    ]

    t_summary = Table(summary_data, colWidths=[10*cm, 5*cm])
    t_summary.setStyle(TableStyle(_header_table_style() + [
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ]))
    story.append(t_summary)
    story.append(PageBreak())

    # 3. Lista de colaboradores
    story.append(Paragraph("Lista de Colaboradores", heading1_style))
    story.append(Spacer(1, 0.5*cm))

    emp_list_data = [["Nome", "CPF", "Cargo", "Registros", "Inconsistências"]]
    for emp in data.get('employees', []):
        emp_list_data.append([
            Paragraph(emp.get('name', ''), custom_normal),
            emp.get('cpf', ''),
            Paragraph(emp.get('role', ''), custom_normal),
            str(len(emp.get('records', []))),
            str(emp.get('summary', {}).get('inconsistencies', 0))
        ])

    t_emp_list = Table(emp_list_data, colWidths=[5*cm, 3*cm, 4*cm, 2*cm, 3*cm])
    t_emp_list.setStyle(TableStyle(_header_table_style() + [
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ]))
    story.append(t_emp_list)

    # 4. Detalhamento por colaborador — uma página por colaborador, no mesmo
    # formato apresentado na tela de detalhe (cabeçalho + cards + registros).
    employees = data.get('employees', [])
    for emp in employees:
        story.append(PageBreak())

        summary = emp.get('summary', {})
        records = emp.get('records', [])

        story.append(Paragraph(emp.get('name', ''), name_style))
        story.append(Paragraph(
            f"CPF: {emp.get('cpf', '')} &nbsp;&nbsp;|&nbsp;&nbsp; Cargo: {emp.get('role', '')}",
            subtitle_style
        ))
        story.append(Spacer(1, 0.4*cm))
        story.append(_summary_cards(summary, len(records)))
        story.append(Spacer(1, 0.6*cm))

        records_data = [["Data", "Ent1", "Sai1", "Ent2", "Sai2", "Oc", "Motivo", "Status"]]
        for rec in records:
            records_data.append([
                Paragraph(f"{rec.get('weekday', '')} {rec.get('date', '')}", custom_normal),
                rec.get('first_period_entry', ''),
                rec.get('first_period_exit', ''),
                rec.get('second_period_entry', ''),
                rec.get('second_period_exit', ''),
                rec.get('occurrence', ''),
                Paragraph(rec.get('reason', ''), custom_normal),
                Paragraph(rec.get('status', '').replace('_', ' '), custom_normal)
            ])

        t_records = Table(records_data, colWidths=[2.5*cm, 1.2*cm, 1.2*cm, 1.2*cm, 1.2*cm, 1*cm, 4.5*cm, 4*cm], repeatRows=1)

        style_cmds = _header_table_style()
        for i, rec in enumerate(records):
            row = i + 1
            row_color = STATUS_ROW_COLOR.get(rec.get('status'))
            if row_color:
                style_cmds.append(('BACKGROUND', (0, row), (-1, row), row_color))

        t_records.setStyle(TableStyle(style_cmds))
        story.append(t_records)

    # 5. Página final
    story.append(PageBreak())
    story.append(Paragraph("Observações", heading1_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("- A ausência do 2º período não foi considerada falta quando a jornada do dia era de apenas 1 período.", custom_normal))
    story.append(Paragraph("- Registros com falta de marcação foram classificados conforme a obrigatoriedade do horário esperado.", custom_normal))

    doc.build(story)
    return output_path
