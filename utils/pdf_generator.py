"""
Generador de reportes PDF de evidencia (ReportLab).

Produce un PDF por escenario con: título, cada paso con su estado, la query
ejecutada, el resultado en tabla, muestras de error y DataFrames adjuntos.
Pensado para que un Product Owner entienda QUÉ se validó sin leer código.

NOTA: la maquinaria de layout (división de tablas anchas, saltos de página,
estilos) se mantiene tal cual la versión productiva por ser delicada. Solo se
removió código muerto y se corrigió el sombreado de la variable de ruta.
"""
import datetime
import os
import textwrap

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, Image, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

# --- Estilos ---
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='ScenarioTitle', parent=styles['h1'], fontSize=18, spaceAfter=12, textColor=colors.HexColor('#2A4365')))
styles.add(ParagraphStyle(name='StepTitle', parent=styles['h2'], fontSize=12, spaceAfter=8, textColor=colors.HexColor('#2A4365')))
styles.add(ParagraphStyle(name='H3_Custom', parent=styles['h3'], fontSize=10, spaceAfter=6, textColor=colors.HexColor('#4A5568')))
styles.add(ParagraphStyle(name='Code_Custom', parent=styles['Code'], fontName='Courier', fontSize=8, leading=10, borderPadding=8, backColor=colors.HexColor('#F7FAFC'), borderWidth=1, borderColor=colors.HexColor('#E2E8F0')))
styles.add(ParagraphStyle(name='Normal_Small', parent=styles['Normal'], fontSize=8, leading=10))
styles.add(ParagraphStyle(name='Status_Passed', parent=styles['Normal'], textColor=colors.HexColor('#38A169'), fontName='Helvetica-Bold'))
styles.add(ParagraphStyle(name='Status_Failed', parent=styles['Normal'], textColor=colors.HexColor('#E53E3E'), fontName='Helvetica-Bold'))
styles.add(ParagraphStyle(name='Error_Code', parent=styles['Code'], fontName='Courier', fontSize=7, leading=9, textColor=colors.HexColor('#C53030')))


def _header_footer(canvas, doc):
    """Encabezado y pie de página en cada hoja."""
    canvas.saveState()
    try:
        logo = Image("logo.png", width=1 * inch, height=0.5 * inch)
        logo.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - 0.5 * inch)
    except Exception:
        pass

    header_text = Paragraph("Reporte de Evidencia de Pruebas Automatizadas", styles['Normal'])
    header_text.wrap(doc.width, doc.topMargin)
    header_text.drawOn(canvas, doc.leftMargin + 1.2 * inch, doc.height + doc.topMargin - 0.4 * inch)

    canvas.setStrokeColorRGB(0.8, 0.8, 0.8)
    canvas.line(doc.leftMargin, doc.height + doc.topMargin - 0.6 * inch,
                doc.width + doc.leftMargin, doc.height + doc.topMargin - 0.6 * inch)

    footer = Paragraph(
        f"Generado el {datetime.date.today().strftime('%d-%m-%Y')} | "
        f"Data Quality Framework | Página {doc.page}",
        styles['Normal_Small'],
    )
    footer.wrap(doc.width, doc.bottomMargin)
    footer.drawOn(canvas, doc.leftMargin, 0.5 * inch)
    canvas.restoreState()


def _render_dataframe_as_table(df, frame_width):
    """Renderiza un DataFrame como tabla; divide los muy anchos en varias tablas.

    Devuelve siempre una LISTA de flowables (para evitar LayoutError).
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return [Paragraph("No hay datos para mostrar.", styles['Normal_Small'])]

    MAX_COLS = 15

    if df.shape[1] > MAX_COLS:
        tables = []
        num_chunks = (df.shape[1] + MAX_COLS - 1) // MAX_COLS
        for i in range(num_chunks):
            start_col = i * MAX_COLS
            end_col = min(start_col + MAX_COLS, df.shape[1])
            sub_df = df.iloc[:, start_col:end_col]
            tables.extend(_render_dataframe_as_table(sub_df, frame_width))
            tables.append(Spacer(1, 0.1 * inch))
        return tables

    wrapped_headers = []
    for col in df.columns:
        clean_col = str(col).replace('_', ' ')
        wrapped_text = '<br/>'.join(textwrap.wrap(clean_col, 15))
        wrapped_headers.append(Paragraph(f"<b>{wrapped_text}</b>", styles['Normal_Small']))

    data_values = [[Paragraph(str(cell), styles['Normal_Small']) for cell in row]
                   for row in df.values.tolist()]
    table_data = [wrapped_headers] + data_values
    col_widths = [frame_width / len(df.columns)] * len(df.columns)

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2A4365')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F7FAFC')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    return [tbl]


def generate_evidence_pdf(scenario_name, evidence_list, feature_filename):
    safe_name = "".join(x for x in scenario_name if x.isalnum() or x in " ._").rstrip()
    feature_folder = os.path.basename(feature_filename)
    pdf_path = os.path.join('reports', 'pdf', feature_folder, f'{safe_name}.pdf')
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    doc = BaseDocTemplate(pdf_path, pagesize=landscape(A4),
                          topMargin=1.5 * inch, bottomMargin=1 * inch)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    doc.addPageTemplates([PageTemplate(id='main', frames=frame, onPage=_header_footer)])

    story = [
        Paragraph(scenario_name, styles['ScenarioTitle']),
        HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2A4365')),
        Spacer(1, 0.3 * inch),
    ]

    for evidence in evidence_list:
        status_style = styles['Status_Passed'] if evidence['status'] == 'passed' else styles['Status_Failed']
        story.append(Paragraph(f"{evidence['keyword']} {evidence['name']}", styles['StepTitle']))
        story.append(Paragraph(f"Resultado: {evidence['status'].upper()}", status_style))
        story.append(Spacer(1, 0.2 * inch))

        if 'error_message' in evidence:
            story.append(Paragraph("Mensaje de Error:", styles['H3_Custom']))
            story.append(Paragraph(evidence['error_message'].replace('\n', '<br/>'), styles['Error_Code']))

        if 'query' in evidence:
            story.append(Paragraph("Query Ejecutada:", styles['H3_Custom']))
            story.append(Paragraph(evidence['query'], styles['Code_Custom']))

        if 'result_df' in evidence:
            story.append(Paragraph("Resultado de la Query:", styles['H3_Custom']))
            story.extend(_render_dataframe_as_table(evidence['result_df'], doc.width))

        if 'error_sample_df' in evidence:
            story.append(Paragraph("Muestra de Datos con Errores:", styles['H3_Custom']))
            story.extend(_render_dataframe_as_table(evidence['error_sample_df'], doc.width))

        if 'attached_dfs' in evidence:
            for title, df in evidence['attached_dfs']:
                story.append(Paragraph(title, styles['H3_Custom']))
                story.extend(_render_dataframe_as_table(df, doc.width))

        story.append(Spacer(1, 0.3 * inch))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#CBD5E0'),
                                spaceBefore=10, spaceAfter=10))
        story.append(Spacer(1, 0.3 * inch))

        if 'data_filepath' in evidence:
            data_link_path = evidence['data_filepath']
            link = (f'<a href="file:///{os.path.abspath(data_link_path)}" color="blue">'
                    f'<u>Descargar datos completos en CSV</u></a>')
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph(link, styles['Normal']))

    doc.build(story)
    print(f"PDF de evidencia generado en: {pdf_path}")
    return os.path.abspath(pdf_path)
