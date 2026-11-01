-- Setup do Unity Catalog · Vértice Control Tower
-- Provisiona o catálogo principal, os schemas da Arquitetura Medalhão (bronze, silver, gold) e o volume de arquivos brutos.
--
-- Execução via CLI:
--   python3 scripts/run_sql.py sql/00_setup_catalogo.sql --profile SEU-PERFIL

CREATE CATALOG IF NOT EXISTS lakehouse_vertice
  COMMENT 'Torre de Controle de Projetos e Operações de Engenharia — Vértice Tecnologia';

CREATE SCHEMA IF NOT EXISTS lakehouse_vertice.bronze
  COMMENT 'Camada Bronze: ingestão bruta (schema-on-read) de arquivos Excel, ClickUp JSON, MS Project XML e CSVs corporativos.';

CREATE SCHEMA IF NOT EXISTS lakehouse_vertice.silver
  COMMENT 'Camada Silver: dados limpos, deduplicados, tipados e unificados em modelo canônico com contratos de qualidade (EXPECT).';

CREATE SCHEMA IF NOT EXISTS lakehouse_vertice.gold
  COMMENT 'Camada Gold: tabelas analíticas, fatos semanais, KPIs executivos (SPI, CPI, EAC, Margem) e scores preditivos de risco.';

CREATE VOLUME IF NOT EXISTS lakehouse_vertice.bronze.raw
  COMMENT 'Landing zone de arquivos originais: planilhas Excel (.xlsx), JSON do ClickUp, XML do MS Project, CSVs transacionais e contratos em PDF.';
