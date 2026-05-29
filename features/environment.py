"""
Hooks de Behave que orquestan la recolección de evidencia.

Después de cada paso se capturan query, resultado, DataFrames adjuntos y
trazas de error. Al finalizar el escenario se genera un PDF de evidencia y,
opcionalmente, se publica el estado en una herramienta de gestión de pruebas.

La integración con gestión de pruebas (Jira/AgileTest, etc.) está
desacoplada en ``utils.test_management`` y desactivada por defecto: el demo
no realiza ninguna llamada de red. Se habilita con TEST_MGMT_ENABLED=true.
"""
import logging
import traceback

import allure
from dotenv import load_dotenv

from utils import pdf_generator
from utils.test_management import get_test_management_client

load_dotenv()


def before_all(context):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='execution.log',
        filemode='w',
    )
    logging.info("=" * 50)
    logging.info("      INICIO DE LA EJECUCIÓN DE PRUEBAS")
    logging.info("=" * 50)
    context.test_mgmt = get_test_management_client()


def before_scenario(context, scenario):
    context.evidence_list = []
    context.attach_df_list = []
    print(f"\nIniciando escenario: {scenario.name}")


def after_step(context, step):
    evidence = {
        'keyword': step.keyword,
        'name': step.name,
        'status': step.status.name,
    }

    if step.status.name == 'failed' and step.error_message:
        formatted = "".join(traceback.format_tb(step.exc_traceback))
        evidence['error_message'] = f"{step.error_message}\n\n--- Traceback ---\n{formatted}"
        allure.attach(evidence['error_message'], name="Error Traceback",
                      attachment_type=allure.attachment_type.TEXT)

    if hasattr(context, 'query') and hasattr(context, 'query_result_df'):
        evidence['query'] = context.query
        evidence['result_df'] = context.query_result_df
        if hasattr(context, 'query_result_str'):
            allure.attach(context.query, name="Query",
                          attachment_type=allure.attachment_type.TEXT)
            allure.attach(context.query_result_str, name="Resultado",
                          attachment_type=allure.attachment_type.TEXT)
            del context.query_result_str
        del context.query
        del context.query_result_df

    if hasattr(context, 'error_sample_df'):
        evidence['error_query'] = context.error_sample_query
        evidence['error_sample_df'] = context.error_sample_df
        if hasattr(context, 'error_sample_result'):
            allure.attach(context.error_sample_query, name="Query (muestra de error)",
                          attachment_type=allure.attachment_type.TEXT)
            allure.attach(context.error_sample_result, name="Resultado (muestra de error)",
                          attachment_type=allure.attachment_type.TEXT)
            del context.error_sample_result
        del context.error_sample_query
        del context.error_sample_df

    if getattr(context, 'attach_df_list', None):
        evidence['attached_dfs'] = list(context.attach_df_list)
        context.attach_df_list.clear()

    context.evidence_list.append(evidence)


def after_scenario(context, scenario):
    if scenario.status.name not in ('passed', 'failed'):
        print(f"Escenario omitido: {scenario.name}")
        return

    pdf_path = pdf_generator.generate_evidence_pdf(
        scenario.name, context.evidence_list, scenario.feature.filename
    )

    # Publicación opcional del estado en la herramienta de gestión de pruebas.
    jira_tags = [t for t in scenario.tags if t.startswith("TC-")]
    if jira_tags:
        context.test_mgmt.publish_result(
            test_case_key=jira_tags[0],
            status=scenario.status.name,
            scenario_name=scenario.name,
            evidence_path=pdf_path,
        )

    print(f"Finalizado escenario: {scenario.name} | estado: {scenario.status.name}")
