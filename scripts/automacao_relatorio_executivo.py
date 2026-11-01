#!/usr/bin/env python3
"""Automação de Análise de Dados e Geração de Relatórios Executivos (Excel & PDF).

Uso:
    python scripts/automacao_relatorio_executivo.py

Este script demonstra a automação ponta a ponta de um fluxo analítico em Python:
  1. Garante a geração dos dados brutos multi-formato (Excel, ClickUp JSON, MS Project XML e CSV).
  2. Unifica e limpa automaticamente os cronogramas das 3 ferramentas (removendo linhas de TOTAL,
     tarefas-resumo do XML e padronizando datas e números decimais com vírgula).
  3. Calcula indicadores executivos de Valor Agregado (SPI, CPI, EAC, Estouro Previsto) e
     identifica assimetrias de governança ("Projetos Melancia": Farol Verde com SPI < 0,90).
  4. Exporta automaticamente dois entregáveis para a diretoria:
     - Planilha Gerencial em Excel (.xlsx)
     - Relatório Executivo em PDF (.pdf)
"""
from __future__ import annotations

import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "data_generator"))

import gerar_dataset  # noqa: E402
import validar_padroes  # noqa: E402
from pdf_simples import escrever_pdf  # noqa: E402
from xlsx_simples import escrever_xlsx  # noqa: E402


def executar_automacao(pasta_dados: pathlib.Path, pasta_saida: pathlib.Path) -> dict:
    if not (pasta_dados / "pmo" / "projetos.csv").exists():
        gerar_dataset.gerar(pasta_dados, seed=42)

    proj = {p["projeto_id"]: p for p in validar_padroes.ler(pasta_dados, "pmo/projetos.csv")}
    tarefas = validar_padroes.centralizar(pasta_dados, proj)

    custos_por_proj: dict[str, float] = {}
    for c in validar_padroes.ler(pasta_dados, "financeiro/custos.csv"):
        if validar_padroes.data(c["data"]) <= validar_padroes.HOJE:
            pid = c["projeto_id"]
            custos_por_proj[pid] = custos_por_proj.get(pid, 0.0) + float(c["valor"].replace(",", "."))

    farol_atual: dict[str, str] = {}
    for s in validar_padroes.ler(pasta_dados, "pmo/status_semanal.csv"):
        if s["data_status"] == "2026-10-16":
            farol_atual[s["projeto_id"]] = s["farol"].lower()

    linhas_excel = [[
        "ID Projeto", "Nome do Projeto", "Cliente / Área", "Segmento", "Ferramenta",
        "SPI (Prazo)", "CPI (Custo)", "Farol Gerente", "Situação Real",
        "Melancia?", "Orçamento (R$)", "EAC Projetado (R$)", "Estouro Previsto (R$)"
    ]]

    ativos = []
    estouro_total = 0.0
    criticos, atencao, melancias = 0, 0, []

    for pid, p in sorted(proj.items()):
        if p["status"] != "em_andamento":
            continue
        ts = tarefas[pid]
        h_tot = sum(t["horas"] for t in ts)
        h_ag = sum(t["horas"] * t["pct"] / 100.0 for t in ts)
        h_pl = sum(
            t["horas"] * max(0.0, min(1.0, (validar_padroes.HOJE - t["ini_b"]).days / max(1, (t["fim_b"] - t["ini_b"]).days)))
            for t in ts
        )
        orc = float(p["orcamento_custo"])
        ac = custos_por_proj.get(pid, 0.0)
        ev = orc * (h_ag / h_tot)
        spi = round(h_ag / h_pl, 2) if h_pl else 1.0
        cpi = round(ev / ac, 2) if ac else 1.0
        eac = round(orc / (ev / ac), 2) if ev > 0 and ac > 0 else orc
        estouro = max(0.0, round(eac - orc, 2))
        estouro_total += estouro

        menor = min(h_ag / h_pl, ev / ac)
        situacao = "CRÍTICO" if menor < 0.8 else ("ATENÇÃO" if menor < 0.9 else "OK")
        if situacao == "CRÍTICO":
            criticos += 1
        elif situacao == "ATENÇÃO":
            atencao += 1

        farol = farol_atual.get(pid, "verde")
        eh_melancia = farol == "verde" and (h_ag / h_pl) < 0.9
        if eh_melancia:
            melancias.append(pid)

        ativos.append((menor, pid, p["nome_projeto"], p["cliente"], spi, cpi, farol, situacao, estouro))
        linhas_excel.append([
            pid, p["nome_projeto"], p["cliente"], p["segmento"], p["ferramenta"],
            spi, cpi, farol.upper(), situacao, "SIM" if eh_melancia else "NÃO",
            round(orc, 2), eac, estouro
        ])

    ativos.sort(key=lambda x: x[0])
    pasta_saida.mkdir(parents=True, exist_ok=True)
    caminho_xlsx = pasta_saida / "relatorio_executivo_portfolio.xlsx"
    escrever_xlsx(caminho_xlsx, linhas_excel)

    blocos_pdf = [
        ("titulo", "Relatorio Executivo Automatizado - Governanca de Portfolio e Custos"),
        ("subtitulo", "Data-base: 16/10/2026 | Gerado automaticamente via Python Analytics Pipeline"),
        ("espaco", ""),
        ("subtitulo", "1. RESUMO EXECUTIVO DA CARTEIRA ATIVA"),
        ("normal", f"Total de projetos em andamento analisados: {len(ativos)} projetos (unificados de Excel, ClickUp e MS Project)."),
        ("normal", f"Projetos em estado CRITICO (SPI ou CPI < 0,80): {criticos} projetos."),
        ("normal", f"Projetos em estado de ATENCAO (indice entre 0,80 e 0,90): {atencao} projetos."),
        ("normal", f"Estouro orcamentario total projetado (EAC - Orcamento): R$ {estouro_total / 1e6:.2f} milhoes."),
        ("normal", f"Projetos 'Melancia' (Farol Verde reportado com SPI < 0,90): {len(melancias)} ({', '.join(melancias)})."),
        ("espaco", ""),
        ("subtitulo", "2. TOP 10 PROJETOS MAIS CRITICOS PARA ACAO IMEDIATA"),
    ]
    for _, pid, nome, cli, spi, cpi, farol, sit, est in ativos[:10]:
        blocos_pdf.append((
            "normal",
            f"{pid} ({cli}) | SPI: {spi:.2f} | CPI: {cpi:.2f} | Farol: {farol.upper()} | {sit} | Estouro: R$ {est / 1e6:.2f} mi"
        ))

    caminho_pdf = pasta_saida / "relatorio_executivo_diretoria.pdf"
    escrever_pdf(caminho_pdf, blocos_pdf)
    return {
        "projetos_ativos": len(ativos),
        "criticos": criticos,
        "atencao": atencao,
        "melancias": len(melancias),
        "estouro_milhoes": round(estouro_total / 1e6, 2),
        "xlsx": str(caminho_xlsx),
        "pdf": str(caminho_pdf),
    }


if __name__ == "__main__":
    res = executar_automacao(RAIZ / "dados", RAIZ / "relatorios_automatizados")
    print("Automação concluída com sucesso!")
    for k, v in res.items():
        print(f"  {k:<18}: {v}")
