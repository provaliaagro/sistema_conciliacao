##### CONCILIAÇÃO DE DADOS #####

# Importações
import streamlit as st
import pandas as pd
import sistema.ai_config as IA
import sistema.relatorio as r

import logging
import os
import time
from logging.handlers import RotatingFileHandler


def _set_progress(barra_progresso, valor):
    if barra_progresso is not None:
        try:
            barra_progresso.progress(valor)
        except Exception:
            pass

# Configuração de Log
_LOGGER = logging.getLogger("sistema.conciliacao")
if not _LOGGER.handlers:
    try:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        logs_dir = os.path.join(repo_root, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, 'conciliacao.log')
        handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding='utf-8')
        fmt = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
        handler.setFormatter(fmt)
        _LOGGER.addHandler(handler)
        level_name = os.getenv("CONCILIACAO_LOG_LEVEL", "DEBUG").upper()
        _LOGGER.setLevel(getattr(logging, level_name, logging.DEBUG))
    except Exception:
        # If logging setup fails, fall back to basicConfig
        logging.basicConfig(level=logging.INFO)


# CONCILIAÇÃO SIMPLES

# Contagem de movimentações
def contar_movimentacoes(df, coluna_valor='valor_convertido'):  
    """
    Conta movimentações, entradas e saídas excluindo linhas com descrição igual a 'SALDO' e derivadas disso
    
    Returns:
        tuple: (total_movimentacoes, soma_total)
    """
    
    df_movimentacoes = df

    # Conta totais
    total_movimentacoes = len(df_movimentacoes)
    
    # Conta entradas (valores positivos) e saídas (valores negativos)
    if coluna_valor in df_movimentacoes.columns:
        #entradas = len(df_movimentacoes[df_movimentacoes[coluna_valor] > 0])
        #saidas = len(df_movimentacoes[df_movimentacoes[coluna_valor] < 0])
        total_valor = df_movimentacoes[coluna_valor]

    soma_total = total_valor.sum()
    
    return total_movimentacoes, soma_total

# Comparação entre Dados
def comparacao_dados(df_extrato, df_controle):
    """
    Compara os valores e datas dos dois dataframes e retorna um dataframe conciliado
    Garante que cada valor converja com apenas um outro valor
    
    Args:
        df_extrato: DataFrame do extrato bancário
        df_controle: DataFrame do controle financeiro
    
    Returns:
        DataFrame com as colunas de conciliação
    """
    
    # Prepara os dataframes
    df_e = df_extrato[['data', 'documento', 'descricao', 'valor_convertido']].copy()
    df_e.columns = ['data_extrato', 'documento_extrato', 'descricao_extrato', 'valor_extrato']
    
    df_c = df_controle[['data', 'descricao', 'contraparte', 'plano de contas', 'valor_convertido']].copy()
    df_c.columns = ['data_controle', 'recurso_controle', 'contraparte_controle', 'plano de contas_controle', 'valor_controle']
    
    # Resetar índices para IDs únicos
    df_e = df_e.reset_index(drop=True).reset_index().rename(columns={'index': '_id_extrato'})
    df_c = df_c.reset_index(drop=True).reset_index().rename(columns={'index': '_id_controle'})
    
    # Criar colunas auxiliares para marcar matches
    df_e['_matched'] = False
    df_c['_matched'] = False
    
    # Lista para armazenar os matches encontrados
    matches = []
    
    # PERCORRER POR ORDEM PARA GARANTIR REPRODUTIBILIDADE
    # Ordenar por valor para matching consistente
    df_e_sorted = df_e.sort_values(['valor_extrato', '_id_extrato']).reset_index(drop=True)
    df_c_sorted = df_c.sort_values(['valor_controle', '_id_controle']).reset_index(drop=True)
    
    # Fazer matching 1:1
    c_index = 0
    for e_idx in range(len(df_e_sorted)):
        if df_e_sorted.loc[e_idx, '_matched']:
            continue
            
        valor_e = df_e_sorted.loc[e_idx, 'valor_extrato']
        
        # Encontrar primeiro match não utilizado no controle
        while c_index < len(df_c_sorted):
            if (not df_c_sorted.loc[c_index, '_matched'] and 
                df_c_sorted.loc[c_index, 'valor_controle'] == valor_e):
                
                # Encontrou match!
                matches.append({
                    '_id_extrato': df_e_sorted.loc[e_idx, '_id_extrato'],
                    '_id_controle': df_c_sorted.loc[c_index, '_id_controle']
                })
                
                # Marcar como utilizado
                df_e_sorted.loc[e_idx, '_matched'] = True
                df_c_sorted.loc[c_index, '_matched'] = True
                
                c_index += 1  # Avançar para próximo no controle
                break
            c_index += 1
        else:
            # Se não encontrou match, avançar para próximo no extrato
            c_index = 0  # Resetar busca no controle
    
    # AGORA CRIAR O DATAFRAME FINAL COM TODAS AS LINHAS
    
    # 1. Começar com todos os matches
    matches_df = pd.DataFrame(matches) if matches else pd.DataFrame(
        columns=['_id_extrato', '_id_controle']
    )
    
    # 2. Criar dataframe com todas as linhas do extrato (com ou sem match)
    df_result_e = pd.merge(
        df_e[['_id_extrato', 'data_extrato', 'documento_extrato', 'descricao_extrato', 'valor_extrato']],
        matches_df,
        on='_id_extrato',
        how='left'
    )
    
    # 3. Adicionar dados do controle para as que têm match
    df_result = pd.merge(
        df_result_e,
        df_c[['_id_controle', 'data_controle', 'recurso_controle', 'contraparte_controle', 'plano de contas_controle', 'valor_controle']],
        on='_id_controle',
        how='left'
    )
    
    # 4. Adicionar as linhas do controle que NÃO foram usadas em nenhum match
    # Primeiro, identificar IDs do controle que não foram usados
    ids_controle_usados = matches_df['_id_controle'].dropna().unique()
    linhas_controle_nao_usadas = df_c[~df_c['_id_controle'].isin(ids_controle_usados)].copy()
    
    # Criar DataFrame para as linhas não usadas do controle
    if not linhas_controle_nao_usadas.empty:
        df_controle_sem_match = pd.DataFrame({
            'data_extrato': [None] * len(linhas_controle_nao_usadas),
            'descricao_extrato': [None] * len(linhas_controle_nao_usadas),
            'documento_extrato': [None] * len(linhas_controle_nao_usadas),
            'valor_extrato': [None] * len(linhas_controle_nao_usadas),
            '_id_extrato': [None] * len(linhas_controle_nao_usadas),
            '_id_controle': linhas_controle_nao_usadas['_id_controle'].values,
            'data_controle': linhas_controle_nao_usadas['data_controle'].values,
            'recurso_controle': linhas_controle_nao_usadas['recurso_controle'].values,
            'contraparte_controle': linhas_controle_nao_usadas['contraparte_controle'].values,
            'plano de contas_controle': linhas_controle_nao_usadas['plano de contas_controle'].values,
            'valor_controle': linhas_controle_nao_usadas['valor_controle'].values
        })

        # Align columns to avoid FutureWarning from pandas.concat when adding empty/all-NA columns
        df_controle_sem_match = df_controle_sem_match.reindex(columns=df_result.columns)

        _LOGGER.info(
            "Adicionando %d linhas de controle sem match ao resultado (ids: %s)",
            len(df_controle_sem_match),
            list(linhas_controle_nao_usadas['_id_controle'].values)
        )

        # Concatenar com os resultados anteriores
        df_result = pd.concat([df_result, df_controle_sem_match], ignore_index=True)
    
    # Remover colunas auxiliares
    # df_result = df_result.drop(columns=['_id_extrato', '_id_controle'], errors='ignore')
    
    # Cria status - IMPORTANTE: considerar todas as combinações
    df_result['status_conciliacao'] = df_result.apply(
        lambda x: "CONCILIADA" if (
            pd.notna(x.get('descricao_extrato')) and 
            (pd.notna(x.get('recurso_controle')) or pd.notna(x.get('contraparte_controle')))
        ) else "NÃO CONCILIADO",
        axis=1
    )
    
    # Reordenar colunas para melhor visualização
    col_order = [
        '_id_extrato', '_id_controle',
        'data_extrato', 'documento_extrato', 'descricao_extrato', 'valor_extrato',
        'data_controle', 'recurso_controle', 'contraparte_controle', 'plano de contas_controle', 'valor_controle',
        'status_conciliacao'
    ]
    
    # Garantir que todas as colunas existam
    col_order = [col for col in col_order if col in df_result.columns]
    
    return df_result[col_order]

# Processo de Conciliação
def conciliacao_simples(ex, cf, si):
    
    # Quantidade de movimentações
    mov_extrato, total_extrato = contar_movimentacoes(ex)
    
    st.session_state.saldo_final_ex = si + total_extrato
    
    mov_controle, total_controle = contar_movimentacoes(cf)
    
    st.session_state.saldo_final_cf = si + total_controle
    
    # Conciliação Simples
    resultado = comparacao_dados(ex,cf)
     
    # CRIAÇÃO DO RELATÓRIO
    nome_usuario = st.session_state.get('nome', 'Usuário não identificado')
    
    df_relatorico_conv, df_relatorio_div = r.criar_relatorio_conciliação_simples(
        resultado,
        si,
        mov_extrato,
        mov_controle,
        total_extrato,
        total_controle,
        nome_usuario
    )
    
    excel_bytes = r.exportar_relatorio_excel_simples(df_relatorico_conv, df_relatorio_div)
    
    return excel_bytes


# CONCILIAÇÃO COM AGRUPAMENTO

# Separar não conciliados
def separar_nao_conciliados(df):
    
    # Extrato não conciliado → tem valor_extrato e não está conciliado
    extrato_nc = df[
        (df['status_conciliacao'] == "NÃO CONCILIADO") &
        (df['valor_extrato'].notna())
    ][['_id_extrato', 'data_extrato', 'documento_extrato', 'descricao_extrato', 'valor_extrato']].copy()

    extrato_nc = extrato_nc.rename(columns={'_id_extrato': '_id'})


    # Controle não conciliado → tem valor_controle e não está conciliado
    controle_nc = df[
        (df['status_conciliacao'] == "NÃO CONCILIADO") &
        (df['valor_controle'].notna())
    ][['_id_controle', 'data_controle', 'recurso_controle', 'contraparte_controle', 'plano de contas_controle', 'valor_controle']].copy()
    
    controle_nc = controle_nc.rename(columns={'_id_controle': '_id'})

    return extrato_nc, controle_nc

# ==========================================================
# CACHE GEMINI
# ==========================================================

_CACHE_CONTEXTO = {}


def score_contexto_cache(
    descricao_extrato,
    descricao_controle
):

    chave = (
        str(descricao_extrato),
        str(descricao_controle)
    )

    if chave in _CACHE_CONTEXTO:
        return _CACHE_CONTEXTO[chave]

    try:

        score = (
            IA.avaliar_contexto_gemini(
                descricao_extrato,
                descricao_controle
            ) / 100
        )

    except Exception:
        score = 0.5

    _CACHE_CONTEXTO[chave] = score

    return score


# ==========================================================
# GERAÇÃO DE CANDIDATOS
# MATCH EXATO
# ==========================================================

def gerar_candidatos(
    df_base,
    valor_alvo,
    max_itens=5
):

    valor_coluna = (
        "valor_controle"
        if "valor_controle" in df_base.columns
        else "valor_extrato"
    )

    valores = list(
        zip(
            df_base["_id"],
            df_base[valor_coluna]
        )
    )

    valores = [
        x
        for x in valores
        if (
            x[1] != 0
            and abs(x[1]) <= abs(valor_alvo)
            and x[1] * valor_alvo > 0
        )
    ]

    valores.sort(
        key=lambda x: (
            -abs(x[1]),
            x[0]
        )
    )

    resultados = []

    def backtrack(
        pos,
        atual,
        soma
    ):

        if len(resultados) >= 20:
            return

        if len(atual) > max_itens:
            return

        if soma == valor_alvo:

            resultados.append({
                "ids": [x[0] for x in atual],
                "soma": soma
            })

            return

        if valor_alvo > 0 and soma > valor_alvo:
            return

        if valor_alvo < 0 and soma < valor_alvo:
            return

        for i in range(pos, len(valores)):

            atual.append(valores[i])

            backtrack(
                i + 1,
                atual,
                soma + valores[i][1]
            )

            atual.pop()

    backtrack(
        0,
        [],
        0
    )

    return resultados


# ==========================================================
# MELHOR CANDIDATO
# ==========================================================

def selecionar_melhor_candidato(
    candidatos,
    valor_alvo,
    mov_ref,
    df_ref
):

    if not candidatos:
        return None

    # Se existe apenas uma combinação possível,
    # aceita diretamente.
    if len(candidatos) == 1:
        return {
            **candidatos[0],
            "score": 1.0
        }

    melhor = None
    melhor_score = -1

    for cand in candidatos:

        qtd_itens = len(
            cand["ids"]
        )

        # Prefere agrupamentos com menos itens
        score_qtd = max(
            0,
            1 - (qtd_itens - 1) * 0.15
        )

        descricao_ref = str(
            mov_ref.get(
                "descricao_extrato",
                mov_ref.get(
                    "recurso_controle",
                    ""
                )
            )
        )

        descricao_coluna = (
            "descricao_extrato"
            if "descricao_extrato" in df_ref.columns
            else "recurso_controle"
        )

        descricoes = (
            df_ref[
                df_ref["_id"].isin(
                    cand["ids"]
                )
            ][descricao_coluna]
            .fillna("")
            .astype(str)
            .tolist()
        )

        descricao_destino = (
            " | ".join(descricoes)
        )

        score_contexto = (
            score_contexto_cache(
                descricao_ref,
                descricao_destino
            )
        )

        # IA usada apenas como desempate
        score_total = (
            score_contexto * 0.80
            +
            score_qtd * 0.20
        )

        if score_total > melhor_score:

            melhor_score = score_total

            melhor = {
                **cand,
                "score": score_total
            }

    return melhor


# ==========================================================
# RESOLUÇÃO GLOBAL DE CONFLITOS
# ==========================================================

def resolver_conflitos(
    hipoteses
):

    usados_ex = set()
    usados_cf = set()

    resultado = []

    hipoteses.sort(
        key=lambda x: (
            -x["score"],
            len(x["extrato_ids"])
            +
            len(x["controle_ids"])
        )
    )

    for h in hipoteses:

        conflito = False

        for ex_id in h["extrato_ids"]:

            if ex_id in usados_ex:
                conflito = True
                break

        for cf_id in h["controle_ids"]:

            if cf_id in usados_cf:
                conflito = True
                break

        if conflito:
            continue

        usados_ex.update(
            h["extrato_ids"]
        )

        usados_cf.update(
            h["controle_ids"]
        )

        resultado.append(h)

    return resultado


# ==========================================================
# NOVA COMPARAÇÃO DE AGRUPAMENTOS
# ==========================================================

def comparacao_agrupamentos(
    ex_nc,
    cf_nc,
    barra_progresso=None,
    max_itens=5
):

    hipoteses = []

    total = (
        len(ex_nc)
        +
        len(cf_nc)
    )

    contador = 0

    # ----------------------------------
    # EXTRATO -> CONTROLE
    # ----------------------------------

    for _, mov_ex in ex_nc.iterrows():

        contador += 1

        valor_alvo = mov_ex[
            "valor_extrato"
        ]

        if abs(valor_alvo) < 200:
            continue

        controle_filtrado = (
            IA.filtrar_por_contexto(
                mov_ex,
                cf_nc
            )
        )

        if "score_contexto" in controle_filtrado.columns:

            controle_filtrado = (
                controle_filtrado
                .sort_values(
                    "score_contexto",
                    ascending=False
                )
                .head(10)
            )

        candidatos = gerar_candidatos(
            controle_filtrado,
            valor_alvo,
            max_itens=max_itens
        )
        
        # st.write(f"Valor alvo: {valor_alvo} | Candidatos encontrados: {len(candidatos)}")

        melhor = (
            selecionar_melhor_candidato(
                candidatos,
                valor_alvo,
                mov_ex,
                cf_nc
            )
        )
        
        # st.write("Candidato:", candidatos)
        # st.write("Melhor:", melhor)

        if melhor:

            hipoteses.append({
                "score": melhor["score"],
                "valor": valor_alvo,
                "extrato_ids": [
                    mov_ex["_id"]
                ],
                "controle_ids": melhor["ids"]
            })

    # ----------------------------------
    # CONTROLE -> EXTRATO
    # ----------------------------------

    for _, mov_cf in cf_nc.iterrows():

        contador += 1

        valor_alvo = mov_cf[
            "valor_controle"
        ]

        if abs(valor_alvo) < 200:
            continue

        extrato_filtrado = (
            IA.filtrar_por_contexto(
                mov_cf,
                ex_nc
            )
        )

        if "score_contexto" in extrato_filtrado.columns:

            extrato_filtrado = (
                extrato_filtrado
                .sort_values(
                    "score_contexto",
                    ascending=False
                )
                .head(10)
            )

        candidatos = gerar_candidatos(
            extrato_filtrado,
            valor_alvo,
            max_itens=max_itens
        )

        melhor = (
            selecionar_melhor_candidato(
                candidatos,
                valor_alvo,
                mov_cf,
                ex_nc
            )
        )

        if melhor:

            hipoteses.append({
                "score": melhor["score"],
                "valor": valor_alvo,
                "extrato_ids": melhor["ids"],
                "controle_ids": [
                    mov_cf["_id"]
                ]
            })

    finais = resolver_conflitos(
        hipoteses
    )

    agrupamentos = []

    for idx, item in enumerate(
        finais,
        start=1
    ):

        agrupamentos.append({

            "id":
                f"AGR-{idx:03d}",

            "valor_extrato":
                item["valor"],

            "extrato_ids":
                item["extrato_ids"],

            "controle_ids":
                item["controle_ids"]
        })

    return agrupamentos

# Aplicação dos agrupamentos para construção do relatório
def aplicar_agrupamentos(resultado, agrupamentos):
    resultado = resultado.copy()

    resultado["agrupamento"] = None
    resultado["tipo_conciliacao"] = resultado["status_conciliacao"]

    for agr in agrupamentos:

        id_agr = agr["id"]

        extrato_ids = agr.get("extrato_ids")
        if extrato_ids is None:
            extrato_ids = [agr.get("extrato_id")] if agr.get("extrato_id") is not None else []

        controle_ids = agr.get("controle_ids", [])

        if extrato_ids:
            mask_ex = resultado["_id_extrato"].isin(extrato_ids)
            resultado.loc[mask_ex, "status_conciliacao"] = "CONCILIADA"
            resultado.loc[mask_ex, "tipo_conciliacao"] = "AGRUPAMENTO"
            resultado.loc[mask_ex, "agrupamento"] = id_agr

        if controle_ids:
            mask_cf = resultado["_id_controle"].isin(controle_ids)
            resultado.loc[mask_cf, "status_conciliacao"] = "CONCILIADA"
            resultado.loc[mask_cf, "tipo_conciliacao"] = "AGRUPAMENTO"
            resultado.loc[mask_cf, "agrupamento"] = id_agr

    return resultado

# Processo de Conciliação
def conciliacao_agrupamento(ex, cf, si, barra_progresso=None):
    
    # 0. Contar movimentações
    mov_extrato, total_extrato = contar_movimentacoes(ex)
    
    st.session_state.saldo_final_ex = si + total_extrato
    
    mov_controle, total_controle = contar_movimentacoes(cf)
    
    st.session_state.saldo_final_cf = si + total_controle

    if barra_progresso is not None:
        barra_progresso.progress(30)
    st.write("Realizando comparação inicial entre extrato e controle...")
    resultado_inicial = comparacao_dados(ex, cf)

    if barra_progresso is not None:
        barra_progresso.progress(40)
    st.write("Separando itens não conciliados para análise de agrupamento...")
    ex_nc, cf_nc = separar_nao_conciliados(resultado_inicial)

    if barra_progresso is not None:
        barra_progresso.progress(50)
    st.write("Gerando agrupamentos inteligentes para itens não conciliados...")
    agrupamentos = comparacao_agrupamentos(ex_nc, cf_nc, barra_progresso=barra_progresso)

    if barra_progresso is not None:
        barra_progresso.progress(70)
    st.write("Gerando relatório final com os agrupamentos aplicados...")
    resultado_final = aplicar_agrupamentos(resultado_inicial, agrupamentos)

    if barra_progresso is not None:
        barra_progresso.progress(80)
    st.write("Exportando relatório...")
    nome_usuario = st.session_state.get('nome', 'Usuário não identificado')
    
    df_relatorico_conv, df_relatorio_div = r.criar_relatorio_conciliação_agrupamento(
        resultado_final,
        si,
        mov_extrato,
        mov_controle,
        total_extrato,
        total_controle,
        nome_usuario
    )
    
    excel_bytes = r.exportar_relatorio_excel_agrupamento(df_relatorico_conv, df_relatorio_div)
    
    return excel_bytes
    