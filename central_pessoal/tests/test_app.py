import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


class CentralPessoalTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        app.DB_PATH = Path(self.temp.name) / "test.db"
        app.initialize()
        self.server = app.ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, path, method="GET", payload=None):
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request) as response:
            return response.status, json.loads(response.read())

    def test_template_has_expected_private_organization_structure(self):
        status, dashboard = self.request("/api/dashboard")
        self.assertEqual(status, 200)
        self.assertEqual(dashboard["totals"]["pacientes"], 20)
        self.assertEqual(dashboard["totals"]["projetos"], 5)
        self.assertEqual(dashboard["totals"]["tarefas"], 4)
        self.assertEqual(len(dashboard["areas"]), 6)

    def test_create_and_search_project(self):
        areas = self.request("/api/areas")[1]
        area_id = next(area["id"] for area in areas if area["nome"] == "YouTube")
        status, created = self.request(
            "/api/projects",
            "POST",
            {
                "area_id": area_id,
                "nome": "Série sobre organização",
                "status": "planejado",
                "prioridade": "alta",
                "proxima_acao": "Escrever roteiro",
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(created["nome"], "Série sobre organização")
        results = self.request("/api/projects?q=roteiro")[1]
        self.assertEqual([item["id"] for item in results], [created["id"]])

    def test_patient_appointment_record_and_finance_flow(self):
        patient_id = self.request("/api/patients")[1][0]["id"]
        appointment = self.request(
            "/api/appointments",
            "POST",
            {
                "paciente_id": patient_id,
                "data_hora": "2030-08-15T14:30",
                "tipo": "consulta",
                "valor": 250,
            },
        )[1]
        record = self.request(
            "/api/records",
            "POST",
            {
                "paciente_id": patient_id,
                "atendimento_id": appointment["id"],
                "data_registro": "2030-08-15",
                "titulo": "Evolução",
                "conteudo": "Registro clínico de teste.",
            },
        )[1]
        finance = self.request(
            "/api/finances",
            "POST",
            {
                "data": "2030-08-15",
                "descricao": "Consulta",
                "tipo": "receita",
                "categoria": "Consultório",
                "valor": 250,
                "pessoa_id": patient_id,
            },
        )[1]
        self.assertEqual(record["atendimento_id"], appointment["id"])
        self.assertEqual(finance["valor"], 250)
        self.assertEqual(
            self.request("/api/records?q=" + quote("Evolução"))[1][0]["paciente_id"],
            patient_id,
        )

    def test_complete_task_and_validate_required_fields(self):
        task_id = self.request("/api/tasks")[1][0]["id"]
        updated = self.request("/api/tasks/" + str(task_id), "PATCH", {"status": "concluida"})[1]
        self.assertEqual(updated["status"], "concluida")
        with self.assertRaises(HTTPError) as context:
            self.request("/api/projects", "POST", {"nome": ""})
        self.assertEqual(context.exception.code, 400)
        patient_id = self.request("/api/patients")[1][0]["id"]
        with self.assertRaises(HTTPError) as context:
            self.request(
                "/api/appointments",
                "POST",
                {"paciente_id": patient_id, "data_hora": "72026-07-21T14:30"},
            )
        self.assertEqual(context.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
