#!/usr/bin/env python3
"""
Gera estrutura de conversas por paciente a partir do índice Notion.
Usado para importar sessões em páginas dedicadas (uma por paciente).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
MAP_FILE = BASE / "pacientes_map.json"
OUT_FILE = BASE / "conversas_por_paciente.json"

# Mapeamento: nome no índice Notion → nome canônico (pacientes.csv)
INDICE_PARA_CANONICO = {
    "Beatriz (Bia)": "Beatriz Jubilut",
    "Bruna": "Bruna Galon Paiva",
    "Clara": "Clara",
    "Claudia": "Claudia",
    "Fernando de Castro": "Fernando de Castro",
    "Felipe (Fê)": "Felipe Zandona Barbosa",
    "Gabriel": "Gabriel Gasparetto",
    "Larissa": "Larissa",
    "Lariassa Plausino": "Larissa",  # possível variação de nome
    "Lívia": "Lívia Padiar",
    "Luigi (Luigi Caloi)": "Luigi Caloi",
    "Luisa Cabalin": "Luisa Cabalin",
    "Luís Octavio Almeida": "Luís Octavio Almeida",
    "Márcia": "Márcia",
    "Maria José": "Maria José",
    "Monica / Monica Mattos": "Monica Mattos Fernandes",
    "Rochele (Rô)": "Rochele",
    "Sthephanie": "Sthephanie",
    "Sessões sem paciente identificado": None,
}

# Índice Notion — sessões por paciente (extraído de 943cbf9d-373d-43ef-ab0d-97db85284e73)
INDICE_SESSOES = {
    "Beatriz (Bia)": [
        ("2ee5e66b0dc18006952ffd31498e6e5b", "19/01/2026"),
        ("75f3a7aed65a47e5aeb48a9993e2a62a", None),
        ("3125e66b0dc180a7bfedc4215b7b1c0e", "25/02/2026"),
        ("2fc5e66b0dc180dea43ff2554f8c8ec3", "02/02/2026"),
        ("ce115e99ff29400f9fc9a8ba4133a24d", "19/01/2026"),
        ("2ee5e66b0dc1819db395d2c2872f639a", None),
        ("e99ca7ca8f42430b906a8cfe98d27e5c", None),
    ],
    "Bruna": [
        ("f161e209941c41eb91424153f40d77c3", "20/01/2026"),
        ("4289abbd5477482bb8dce01f7c319981", "13/01/2026"),
        ("6df2c0273bc04bbd84bfecc6f0960dc7", None),
        ("2ee5e66b0dc180dea924f1ace8dde4c4", "20/01/2026"),
        ("2fc5e66b0dc18061b299f4456d2b86ef", "03/02/2026"),
    ],
    "Clara": [
        ("2f15e66b0dc180538d47c196a602f984", None),
        ("39d4a14d2e08402cbae4b63785a149ad", "23/01/2026"),
        ("3125e66b0dc1801486dcdac8cb1946ab", "25/02/2026"),
    ],
    "Claudia": [
        ("fd7e780f9e734c7bbd721ed68af3075d", "16/12/2025"),
        ("2cb5e66b0dc180ea9471ed366f64494a", "16/12/2025"),
        ("2e95e66b0dc180ebac71d7988261033e", "15/01/2026"),
        ("3025e66b0dc180b0aff6cc94c2e0a75c", "09/02/2026"),
        ("34a5e66b0dc1809f9561df0cf933c3bd", "22/04/2026"),
    ],
    "Fernando de Castro": [
        ("4709ad62e43f4f02a5ef0f3d877267a9", "12/12/2025"),
        ("2f15e66b0dc1805584ebcd2d87f08ac7", "23/01/2026"),
        ("3685e66b0dc1800eb3b4d1427d0e80c7", "22/05/2026"),
        ("36f5e66b0dc1803cb097f759c9c2cb15", "29/05/2026"),
    ],
    "Felipe (Fê)": [
        ("7d66884e18294b2eb0fdcfbde2dfa50e", "16/12/2025"),
        ("2cb5e66b0dc180fba764d8f075f535de", None),
        ("3065e66b0dc18061915ad808eab209a8", "13/02/2026"),
    ],
    "Gabriel": [
        ("2c75e66b0dc1808285b7eef05eb98add", "12/12/2025"),
        ("30d5e66b0dc1808895b6d1faa7e36e22", "20/02/2026"),
        ("67182519941840bc9232a696157f7313", None),
        ("36d5e66b0dc1808aad2fcf096cae4901", "27/05/2026"),
    ],
    "Larissa": [
        ("3605e66b0dc18055bcf2d1c9d9db6762", "14/05/2026"),
        ("35e5e66b0dc180b7b6b3c8bd32b79633", "12/05/2026"),
        ("36e5e66b0dc180e88d59dddb08ada9a4", "28/05/2026"),
        ("36c5e66b0dc180a284bafd8561b3fae6", "26/05/2026"),
        ("3515e66b0dc1805090d0f0db61387cb1", "29/04/2026"),
        ("3495e66b0dc180d5a054dff3a0fcd35f", "21/04/2026"),
        ("34b5e66b0dc1806d9d46c649515abb79", "23/04/2026"),
    ],
    "Lariassa Plausino": [
        ("3675e66b0dc180929ecbd8ceaeedd7de", "21/05/2026"),
    ],
    "Lívia": [
        ("2994f817f03a47678fefc9e5f56021d9", "10/12/2025"),
        ("f55824dc9af542f5aca8b8930d286773", "19/01/2026"),
        ("e0ceacb074194e7e88f07c3a495e2385", None),
        ("2e85e66b0dc1813c9b2cee05a595296a", "14/01/2026"),
        ("2c55e66b0dc180608b2de39418f04bf3", "10/12/2025"),
        ("30d5e66b0dc180399e11c5f01c3a0b67", "20/02/2026"),
        ("3135e66b0dc18008bf05dcd55d0a15c1", "26/02/2026"),
        ("34b5e66b0dc18051a0e5c94b5d09e4cf", "23/04/2026"),
        ("d6affe478e62421393c831b1d0d21f6e", "19/01/2026"),
    ],
    "Luigi (Luigi Caloi)": [
        ("cc7d2678fc88407fb22c0f4164c6ee18", "20/01/2026"),
        ("8991b71549734bc69c97450a6607c43d", None),
        ("4b86bc33b8bd4e458f33a24eb845e83a", None),
        ("fe81ca04c0ab40539cd0e3501a537b6d", "20/01/2026"),
        ("3495e66b0dc18032b317ff0eafe8b80c", "21/04/2026"),
        ("35e5e66b0dc18000949efb2d609bee93", "12/05/2026"),
    ],
    "Luisa Cabalin": [
        ("2e75e66b0dc1813e8f6fe31759de9594", "13/01/2026"),
        ("76265cde8e4c499d9c50a419e6ef3fa2", "08/12/2025"),
        ("2c35e66b0dc180998e72e239607a83ca", "08/12/2025"),
        ("a7a00b9262c044b885b0ae05d242fe38", None),
        ("643cf9fde25f45779d37cacf8d95bf2e", None),
        ("3505e66b0dc180158318f9c3c778e350", "28/04/2026"),
    ],
    "Luís Octavio Almeida": [
        ("3445e66b0dc180e29159f40e4356ac24", "16/04/2026"),
        ("3605e66b0dc1802aa629e664253e1c15", "14/05/2026"),
    ],
    "Márcia": [
        ("84e0a2729263450ba41619d746afd456", "14/01/2026"),
        ("2e85e66b0dc18043a8d9d0001a8dc1c6", "14/01/2026"),
    ],
    "Maria José": [
        ("2c65e66b0dc1800b92fdd4e79dd472b2", None),
        ("2cb5e66b0dc180b7a621c8be81e76be4", "16/12/2025"),
        ("3135e66b0dc1806199adc306dd477205", "26/02/2026"),
        ("3eeecb6edf534836b510ec2ae48432dc", None),
    ],
    "Monica / Monica Mattos": [
        ("c96c9d47b8324d19b5cd09c6f779d767", "21/01/2026"),
        ("5266472e67124363b48703f5d8d85084", "11/12/2025"),
        ("9d3ff2269cfd45949f64f3b59401171f", "14/01/2026"),
        ("459783bbbb5148dc96317d1fa4e8d151", "04/02/2026"),
        ("8eab5ade239a4d4abfb6d20882aebc31", "04/02/2026"),
        ("3055e66b0dc180678822e7239b622389", "12/02/2026"),
    ],
    "Rochele (Rô)": [
        ("36e5e66b0dc18021a69ee11fec1d65b5", None),
        ("34a5e66b0dc180a6bfa2f6c086a0949f", "22/04/2026"),
        ("3515e66b0dc180dba490cdfad63fc8fa", "29/04/2026"),
    ],
    "Sthephanie": [
        ("ffe11942bc134458922a305f47619510", "16/12/2025"),
        ("5422b2623c0444a1ab9b8bdc2b2a32d2", "13/01/2026"),
        ("bc9f6d509acc417c889fc426afd2d915", "20/01/2026"),
        ("2fc5e66b0dc180c9ad95f336a58d3068", "03/02/2026"),
        ("2e75e66b0dc1814ba255fb95959fc483", "13/01/2026"),
        ("2cb5e66b0dc180a5a843ca54cb6dab6d", "16/12/2025"),
        ("35e5e66b0dc18051a7f0cb454825a872", "12/05/2026"),
        ("62984f1c45bf44e9bb05143c458c7311", None),
    ],
}

# Notas da agenda (extraídas da query SQL)
NOTAS_AGENDA = {
    "2ee5e66b0dc18006952ffd31498e6e5b": "Novo emprego (novembro). Estresse com carona (Regina). Dificuldade em aceitar ajuda financeira (Mi). Padrões familiares.",
    "4289abbd5477482bb8dce01f7c319981": "Desmotivação pós-provas (80 pts). Dificuldade com rotina. Comparação com Mar (EUA). Estratégias: Ritalina, novos ambientes.",
    "6df2c0273bc04bbd84bfecc6f0960dc7": "Apoio pós-exames. Autocrítica vs crescimento. Viagem com Mar. Metáfora da espiral (vida).",
    "f161e209941c41eb91424153f40d77c3": "Desânimo com provas, autocrítica. Retomada de treinos/social. Decisão de não ir à Disney. Mar passou no ABCG.",
    "cc7d2678fc88407fb22c0f4164c6ee18": "Entrevistas acadêmicas (Chicago, Insper). Novo relacionamento com Jasmine (fluido, seguro). Comparação com Gabi.",
    "f55824dc9af542f5aca8b8930d286773": "Vitória: Cinema (Avatar). Crise de pânico na casa de Léo (ansiedade separação). Gatilhos mãe/casa. Apoio de Léo.",
}

# Resumos da consolidação
RESUMOS_CONSOLIDACAO = {
    "Clara": "Ansiedade em entrevistas em dinamarquês. Conflitos de valores com o parceiro Sebastião (sustentabilidade vs. capitalismo/racismo).",
    "Bruna Galon Paiva": "Desmotivação após resultados de residência médica. Sente-se estagnada e com aversão aos estudos. Planeja prova para 20 de fevereiro.",
    "Luisa Cabalin": "Trabalhou no final de ano no banco BNP. Conflitos familiares envolvendo a irmã de seu parceiro Pedro durante o Natal.",
    "Luigi Caloi": "Anotação baseada em arquivo de vídeo de novembro de 2025. Paciente ativo com sessões semanais presenciais.",
}


def page_url(page_id: str) -> str:
    pid = page_id.replace("-", "")
    return f"https://app.notion.com/p/{pid}"


def codigo_paciente(nome: str, pmap: dict) -> str | None:
    return pmap.get(nome)


def gerar_conteudo_notion(nome: str, codigo: str, sessoes: list) -> str:
    lines = [
        '<callout icon="💬" color="blue_bg">',
        f"\tConversas e sessões consolidadas — **{codigo}**",
        "</callout>",
        f"**Paciente:** {nome}",
        f"**Código:** {codigo}",
        "",
        f"## Sessões ({len(sessoes)})",
        "",
    ]
    for i, (pid, data) in enumerate(sessoes, 1):
        url = page_url(pid)
        data_str = data or "data não informada"
        nota = NOTAS_AGENDA.get(pid, "")
        lines.append(f"<details>")
        lines.append(f"<summary>Sessão {i} — {data_str}</summary>")
        lines.append(f"\t- <mention-page url=\"{url}\"/>")
        if nota:
            lines.append(f"\t- **Notas:** {nota}")
        resumo = RESUMOS_CONSOLIDACAO.get(nome, "")
        if resumo and i == 1:
            lines.append(f"\t- **Resumo consolidado:** {resumo}")
        lines.append("</details>")
        lines.append("")
    return "\n".join(lines)


def main():
    pmap = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    # Inverter mapa: nome canônico → código
    nome_para_codigo: dict[str, str] = {}
    for alias, cod in pmap.items():
        if cod not in nome_para_codigo.values():
            pass
    # Usar CSV codes directly
    codigos = {
        "Maria José": "PAC-001",
        "Beatriz Jubilut": "PAC-002",
        "Luigi Caloi": "PAC-003",
        "Fernando de Castro": "PAC-004",
        "Felipe Zandona Barbosa": "PAC-005",
        "Monica Mattos Fernandes": "PAC-006",
        "Luís Octavio Almeida": "PAC-007",
        "Gabriel Gasparetto": "PAC-008",
        "Bruna Galon Paiva": "PAC-009",
        "Luisa Cabalin": "PAC-010",
        "Clara": "PAC-011",
        "Lívia Padiar": "PAC-012",
        "Sthephanie": "PAC-013",
        "Claudia": "PAC-014",
        "Márcia": "PAC-015",
        "Gabrielli": "PAC-016",
        "Larissa": "PAC-017",
        "Rochele": "PAC-018",
    }

    pacientes: dict[str, dict] = {}
    for indice_nome, sessoes in INDICE_SESSOES.items():
        canonico = INDICE_PARA_CANONICO.get(indice_nome)
        if not canonico:
            continue
        if canonico not in pacientes:
            pacientes[canonico] = {"sessoes": [], "codigo": codigos.get(canonico, "")}
        # deduplicate by page id
        existing_ids = {s[0] for s in pacientes[canonico]["sessoes"]}
        for s in sessoes:
            if s[0] not in existing_ids:
                pacientes[canonico]["sessoes"].append(s)
                existing_ids.add(s[0])

    # Gabrielli sem sessões no índice
    if "Gabrielli" not in pacientes:
        pacientes["Gabrielli"] = {"sessoes": [], "codigo": "PAC-016"}

    resultado = {}
    for nome, dados in sorted(pacientes.items()):
        conteudo = gerar_conteudo_notion(nome, dados["codigo"], dados["sessoes"])
        resultado[nome] = {
            "codigo": dados["codigo"],
            "total_sessoes": len(dados["sessoes"]),
            "sessoes": [{"id": s[0], "data": s[1], "url": page_url(s[0])} for s in dados["sessoes"]],
            "conteudo_notion": conteudo,
        }

    OUT_FILE.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ {len(resultado)} pacientes → {OUT_FILE}")
    for n, d in resultado.items():
        print(f"  {d['codigo']} {n}: {d['total_sessoes']} sessões")


if __name__ == "__main__":
    main()
