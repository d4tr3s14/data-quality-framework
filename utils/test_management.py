"""
Integración (opcional) con herramientas de gestión de pruebas.

En el pipeline original, al terminar cada escenario se publicaba el resultado
y se adjuntaba el PDF de evidencia en un ticket de ejecución (Jira + AgileTest).

Aquí esa integración está:
  - Desacoplada detrás de una interfaz simple (``publish_result``).
  - Desactivada por defecto -> ``NoOpTestManagementClient`` (no hace llamadas
    de red), de modo que el demo es autocontenido y reproducible.
  - Habilitable con ``TEST_MGMT_ENABLED=true`` y las credenciales en el ``.env``
    (ver ``JiraTestManagementClient``), parametrizada por variables de entorno;
    nunca con secretos hardcodeados.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod


class TestManagementClient(ABC):
    @abstractmethod
    def publish_result(self, test_case_key: str, status: str,
                       scenario_name: str, evidence_path: str | None) -> None:
        ...


class NoOpTestManagementClient(TestManagementClient):
    """Cliente por defecto: solo registra en consola, sin llamadas externas."""

    def publish_result(self, test_case_key, status, scenario_name, evidence_path):
        label = "PASSED" if status == "passed" else "FAILED"
        print(f"   [test-mgmt:noop] {test_case_key} -> {label} | evidencia: {evidence_path}")


class JiraTestManagementClient(TestManagementClient):
    """Publica el estado y adjunta el PDF de evidencia en un ticket de Jira.

    Todas las credenciales provienen de variables de entorno:
        JIRA_BASE_URL, JIRA_USER_EMAIL, JIRA_API_TOKEN, TEST_EXECUTION_TICKET
    """

    def __init__(self):
        import requests
        from requests.auth import HTTPBasicAuth

        self._requests = requests
        self.base_url = os.environ["JIRA_BASE_URL"].rstrip("/")
        self.auth = HTTPBasicAuth(os.environ["JIRA_USER_EMAIL"], os.environ["JIRA_API_TOKEN"])
        self.execution_ticket = os.getenv("TEST_EXECUTION_TICKET")

    def publish_result(self, test_case_key, status, scenario_name, evidence_path):
        icon = "PASSED" if status == "passed" else "FAILED"
        comment = (
            f"*Ejecucion automatizada BDD*\n*Estado:* {icon}\n"
            f"*Escenario:* {scenario_name}"
        )
        try:
            self._requests.post(
                f"{self.base_url}/rest/api/2/issue/{test_case_key}/comment",
                json={"body": comment},
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                auth=self.auth,
                timeout=30,
            ).raise_for_status()

            if evidence_path and self.execution_ticket:
                with open(evidence_path, "rb") as fh:
                    self._requests.post(
                        f"{self.base_url}/rest/api/2/issue/{self.execution_ticket}/attachments",
                        headers={"X-Atlassian-Token": "no-check"},
                        auth=self.auth,
                        files={"file": (os.path.basename(evidence_path), fh, "application/pdf")},
                        timeout=60,
                    ).raise_for_status()
            print(f"   [test-mgmt:jira] {test_case_key} actualizado en {self.base_url}")
        except Exception as exc:  # nunca romper la suite por un fallo de publicación
            print(f"   [test-mgmt:jira] advertencia: no se pudo publicar {test_case_key}: {exc}")


def get_test_management_client() -> TestManagementClient:
    if os.getenv("TEST_MGMT_ENABLED", "false").lower() == "true":
        return JiraTestManagementClient()
    return NoOpTestManagementClient()
