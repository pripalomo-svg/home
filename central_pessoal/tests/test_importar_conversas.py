import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
import importar_conversas


class ImportarConversasTest(unittest.TestCase):
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

    def test_parse_portuguese_filename_and_remove_upload_suffix(self):
        conversa = importar_conversas.analisar_nome(
            Path("Luigi_19_de_maio_de_2026_1100_1637.pdf")
        )
        self.assertEqual(conversa.paciente, "Luigi")
        self.assertEqual(conversa.data_hora, datetime(2026, 5, 19, 11, 0))
        self.assertEqual(
            conversa.nome_arquivo, "Luigi_19_de_maio_de_2026_1100.pdf"
        )

    def test_import_is_complete_and_idempotent(self):
        source = self.base / "Luigi_19_de_maio_de_2026_1100_1637.pdf"
        source.write_bytes(b"%PDF fake test fixture")
        transcript = "Resumo da sessão.\n\nTranscrição completa da conversa."
        with patch.object(importar_conversas, "extrair_texto", return_value=transcript):
            first = importar_conversas.importar_arquivo(source)
            second = importar_conversas.importar_arquivo(source)

        self.assertEqual(first, second)
        self.assertEqual(first["paciente"], "Luigi")
        self.assertEqual(first["data_hora"], "2026-05-19T11:00")
        self.assertTrue((self.base / first["arquivo"]).exists())
        with app.connect() as connection:
            patient = connection.execute(
                "SELECT * FROM pessoas WHERE nome='Luigi'"
            ).fetchone()
            record = connection.execute(
                "SELECT * FROM prontuarios WHERE paciente_id=?", (patient["id"],)
            ).fetchone()
            appointment = connection.execute(
                "SELECT * FROM atendimentos WHERE paciente_id=?", (patient["id"],)
            ).fetchone()
            self.assertEqual(record["conteudo"], transcript)
            self.assertEqual(record["atendimento_id"], appointment["id"])
            self.assertEqual(appointment["status"], "realizado")
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM prontuarios").fetchone()[0],
                1,
            )
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM arquivos").fetchone()[0], 1
            )
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM pessoas WHERE tipo='paciente'"
                ).fetchone()[0],
                20,
            )

    def test_reject_filename_without_session_metadata(self):
        with self.assertRaisesRegex(ValueError, "Nome fora do padrão"):
            importar_conversas.analisar_nome(Path("conversa.pdf"))


if __name__ == "__main__":
    unittest.main()
