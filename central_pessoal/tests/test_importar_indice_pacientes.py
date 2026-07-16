import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
import importar_indice_pacientes


TEXTO_INDICE = """
Pacientes — Sessões (por pessoa)
Conversas por paciente
PAC-001 - Maria José — Conversas
PAC-002 - Beatriz Jubilut — Conversas

Pacientes
Beatriz (Bia)
Beatriz Jubilut — Sessão 19/01/2026 (19/01/2026)
bia (25/02/2026)
Bruna
Bruna — Sessão realizada (20/01/2026)
Clara
Clara — Sessão 23/01/2026 (23/01/2026)
Claudia
Cláudia 22/04/26 (22/04/2026)
Fernando de Castro
fernando 23/01/26 (23/01/2026)
Felipe (Fê)
felipe zandona (13/02/2026)
Gabriel
gabriel (20/02/2026)
Larissa
Larissa online (14/05/2026)
Lívia
livia (20/02/2026)
Luigi (Luigi Caloi)
luigi (12/05/2026)
Luisa Cabalin
luisa (28/04/2026)
Luís Octavio Almeida
Luís Octavio Almeida (16/04/2026)
Márcia
Márcia (14/01/2026)
Maria José
maria jose (26/02/2026)
Monica / Monica Mattos
Monica Mattos (04/02/2026)
Rochele (Rô)
Rochelle (22/04/2026)
Sessões sem paciente identificado
sem identificação
Sthephanie
Stephanie (03/02/2026)
PAC-001 - Maria José — Conversas
"""


class ImportarIndicePacientesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.original_base = app.BASE_DIR
        app.BASE_DIR = self.base
        app.DB_PATH = self.base / "central.db"
        app.initialize()

    def tearDown(self):
        app.BASE_DIR = self.original_base
        self.temp.cleanup()

    def test_separates_index_lines_by_canonical_patient(self):
        sections = importar_indice_pacientes.separar_por_paciente(TEXTO_INDICE)
        self.assertEqual(
            sections["Beatriz Jubilut"],
            [
                "Beatriz Jubilut — Sessão 19/01/2026 (19/01/2026)",
                "bia (25/02/2026)",
            ],
        )
        self.assertEqual(sections["Sthephanie"], ["Stephanie (03/02/2026)"])
        self.assertEqual(sections["Gabrielli"], [])

    def test_imports_eighteen_records_without_duplicate_and_preserves_luigi(self):
        source = self.base / "indice.pdf"
        source.write_bytes(b"%PDF fake test fixture")
        with app.connect() as connection:
            connection.execute(
                "UPDATE pessoas SET nome='Luigi' WHERE nome='Paciente 01'"
            )
            luigi_id = connection.execute(
                "SELECT id FROM pessoas WHERE nome='Luigi'"
            ).fetchone()["id"]
            connection.execute(
                """INSERT INTO prontuarios
                   (paciente_id, data_registro, titulo, conteudo)
                   VALUES (?, '2026-05-19', 'Sessão anterior', 'Conteúdo preservado')""",
                (luigi_id,),
            )
            connection.commit()

        with patch.object(
            importar_indice_pacientes, "extrair_texto", return_value=TEXTO_INDICE
        ):
            first = importar_indice_pacientes.importar_indice(source)
            second = importar_indice_pacientes.importar_indice(source)

        self.assertEqual(first, second)
        self.assertEqual(len(first["pacientes"]), 18)
        self.assertTrue((self.base / first["arquivo"]).exists())
        with app.connect() as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM pessoas WHERE tipo='paciente'"
                ).fetchone()[0],
                20,
            )
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM prontuarios WHERE titulo='Índice consolidado de sessões'"
                ).fetchone()[0],
                18,
            )
            luigi = connection.execute(
                "SELECT id FROM pessoas WHERE nome='Luigi Caloi'"
            ).fetchone()
            self.assertEqual(luigi["id"], luigi_id)
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM prontuarios WHERE paciente_id=?",
                    (luigi_id,),
                ).fetchone()[0],
                2,
            )
            gabrielli = connection.execute(
                """SELECT r.conteudo FROM prontuarios r
                   JOIN pessoas p ON p.id=r.paciente_id
                   WHERE p.nome='Gabrielli'"""
            ).fetchone()
            self.assertIn("Nenhuma sessão detalhada", gabrielli["conteudo"])


if __name__ == "__main__":
    unittest.main()
