# Pasta de prontuários

Organize os PDFs assim:

```
documentos/prontuarios/
├── PAC-001/
│   ├── anamnese.pdf
│   ├── 2026-07-08-evolucao.pdf
│   └── 2026-07-15-evolucao.pdf
├── PAC-002/
│   └── ...
└── PAC-020/
```

**Nomes de arquivo recomendados:** `YYYY-MM-DD-tipo.pdf` (ex.: `2026-07-08-evolucao.pdf`)

**Importar:**

```bash
python3 importar_prontuarios.py pasta documentos/prontuarios
python3 gerar_dashboard.py
```

O script lê o texto do PDF, vincula ao paciente pelo código da pasta e cadastra na tabela `prontuarios`.
