import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from app.models.schemas import PointStatus

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
    title_style = styles['Title']
    heading1_style = styles['Heading1']
    heading2_style = styles['Heading2']
    normal_style = styles['Normal']
    
    custom_normal = ParagraphStyle(
        'CustomNormal',
        parent=normal_style,
        fontSize=10,
        textColor=colors.black
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
    
    for emp in data.get('employees', []):
        total_records += len(emp.get('records', []))
        summary = emp.get('summary', {})
        total_folgas += summary.get('days_off', 0)
        total_ferias += summary.get('vacation_days', 0)
        total_atestados += summary.get('medical_days', 0)
        total_faltas += summary.get('absence_days', 0)
        total_inconsistencias += summary.get('inconsistencies', 0)
        
    summary_data = [
        ["Métrica", "Quantidade"],
        ["Total de Colaboradores", data.get('total_employees', 0)],
        ["Total de Registros", total_records],
        ["Total de Folgas/Domingos", total_folgas],
        ["Total de Férias", total_ferias],
        ["Total de Atestados", total_atestados],
        ["Total de Faltas", total_faltas],
        ["Total de Inconsistências", total_inconsistencias]
    ]
    
    t_summary = Table(summary_data, colWidths=[10*cm, 5*cm])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
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
    t_emp_list.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(t_emp_list)
    story.append(PageBreak())
    
    # 4. Detalhamento por colaborador
    story.append(Paragraph("Detalhamento por Colaborador", heading1_style))
    story.append(Spacer(1, 0.5*cm))
    
    for emp in data.get('employees', []):
        story.append(Paragraph(f"<b>Nome:</b> {emp.get('name', '')}", custom_normal))
        story.append(Paragraph(f"<b>CPF:</b> {emp.get('cpf', '')}", custom_normal))
        story.append(Paragraph(f"<b>Cargo:</b> {emp.get('role', '')}", custom_normal))
        story.append(Spacer(1, 0.5*cm))
        
        records_data = [["Data", "Ent1", "Sai1", "Ent2", "Sai2", "Oc", "Motivo", "Status"]]
        for rec in emp.get('records', []):
            st = rec.get('status', '')
            status_text = st
            
            records_data.append([
                Paragraph(f"{rec.get('weekday', '')} {rec.get('date', '')}", custom_normal),
                rec.get('first_period_entry', ''),
                rec.get('first_period_exit', ''),
                rec.get('second_period_entry', ''),
                rec.get('second_period_exit', ''),
                rec.get('occurrence', ''),
                Paragraph(rec.get('reason', ''), custom_normal),
                Paragraph(status_text, custom_normal)
            ])
            
        t_records = Table(records_data, colWidths=[2.5*cm, 1.2*cm, 1.2*cm, 1.2*cm, 1.2*cm, 1*cm, 4.5*cm, 4*cm])
        
        # Colorir linhas dependendo do status
        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]
        
        for i, rec in enumerate(emp.get('records', [])):
            row = i + 1
            st = rec.get('status', '')
            if st == PointStatus.INCONSISTENCIA:
                style_cmds.append(('BACKGROUND', (0, row), (-1, row), colors.mistyrose))
            elif st == PointStatus.FALTA:
                style_cmds.append(('BACKGROUND', (0, row), (-1, row), colors.lightcoral))
            elif st == PointStatus.TRABALHADO or st == PointStatus.TRABALHADO_PARCIAL:
                style_cmds.append(('BACKGROUND', (0, row), (-1, row), colors.honeydew))
            elif 'OCORRENCIA' in st:
                style_cmds.append(('BACKGROUND', (0, row), (-1, row), colors.lightyellow))
                
        t_records.setStyle(TableStyle(style_cmds))
        story.append(t_records)
        story.append(Spacer(1, 1*cm))
        
    story.append(PageBreak())
    
    # 5. Página final
    story.append(Paragraph("Observações", heading1_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("- A ausência do 2º período não foi considerada falta quando a jornada do dia era de apenas 1 período.", custom_normal))
    story.append(Paragraph("- Registros com falta de marcação foram classificados conforme a obrigatoriedade do horário esperado.", custom_normal))
    
    doc.build(story)
    return output_path
