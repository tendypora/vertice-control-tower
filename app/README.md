# Vértice Control Tower · Aplicação Web (Databricks Apps + Lakebase)

Aplicação Full-Stack (**React + TypeScript + Express + Lakebase PostgreSQL**) construída sobre o **Databricks AppKit** para gestão interativa de portfólio, simulação de realocação de especialistas (SRE/Engenharia), consulta conversacional via Genie e registro auditável de decisões executivas.

```text
app/
├── config/queries/                   Consultas parametrizadas no SQL Warehouse (tipadas via typegen)
│   ├── kpis.sql · projetos_risco.sql · pessoas_ociosas.sql
├── server/
│   ├── server.ts                     Configuração dos plugins analytics, genie, lakebase e rotas REST
│   ├── routes/score.ts               Integração com o score preditivo (gold.score_estouro_30d)
│   ├── routes/decisoes.ts             Persistência transacional no Lakebase Postgres (schema torre.decisoes)
│   └── decisoes.test.ts              Testes automatizados de contrato e validação (Vitest + Zod)
├── client/src/pages/                 Interfaces: Projetos em Risco · Simulador · Decisões · Assistente Genie
├── scripts/
│   ├── conceder-acesso.sh            Concessão de privilégios (GRANTs) no Unity Catalog ao Service Principal
│   ├── subir-tudo.sh                 Provisionamento automatizado (Lakebase + Genie Space ID + App Deploy)
│   └── ver_decisoes.py               Auditoria direta dos registros persistidos no PostgreSQL Serverless
├── databricks.yml                    Definição do Databricks Asset Bundle da aplicação
└── app.yaml                          Especificação de runtime e variáveis de ambiente do Databricks App
```

## Deploy Automatizado

```bash
databricks apps list --profile vertice
bash app/scripts/subir-tudo.sh vertice
```

## Desenvolvimento e Testes Locais

```bash
cd app
npm test
databricks apps validate --profile vertice
databricks apps deploy   --profile vertice
```
