### FUNÇÕES PARA A INTERAÇÃO COM A API DO GEMINI ###

# Importações
import pandas as pd
import streamlit as st
import os
import google.genai as genai
from google.genai import types
import re
import unicodedata

# Configuração da API do Gemini
def _obter_chave_gemini():
    """Obtém chave do Gemini de st.session_state (cada app configura à sua forma)."""
    return st.session_state.get("API_gemini", None)

# Função para normalizar texto: remover acentos, caracteres especiais e palavras curtas
def normalizar_texto(texto):

    texto = str(texto).upper()

    texto = unicodedata.normalize(
        'NFKD',
        texto
    ).encode(
        'ASCII',
        'ignore'
    ).decode(
        'ASCII'
    )

    texto = re.sub(r'[^A-Z0-9 ]', ' ', texto)

    palavras = [
        p for p in texto.split()
        if len(p) > 2
    ]

    return set(palavras)

# Função para avaliar o contexto entre a descrição do extrato e a descrição do controle usando o Gemini
def avaliar_contexto_gemini( 
    descricao_extrato,
    descricao_controle,
    valor_extrato=None,
    valor_controle=None
):

    prompt = f"""
    Você é um auditor especialista em conciliação bancária.

    Seu objetivo NÃO é encontrar semelhanças.

    Seu objetivo é verificar se as descrições
    representam a MESMA operação financeira.

    Considere:

    1. Nome do favorecido
    2. Nome do pagador
    3. Tipo de operação
    4. Banco
    5. PIX
    6. TED
    7. DOC
    8. Boleto
    9. Cartão
    10. Taxa
    11. Estorno
    12. Transferência interna

    REGRAS:

    - Não assuma relações que não estejam explícitas.
    - Não considere valores.
    - Não considere datas.
    - Não invente contexto.
    - Similaridade textual não implica mesma operação.
    - Se houver dúvida, atribua nota baixa.

    Escala:

    0-20:
    operações claramente diferentes

    21-50:
    alguma semelhança textual

    51-80:
    forte evidência contextual

    81-100:
    mesma operação ou altíssima probabilidade

    Retorne apenas um inteiro.
    """
    api_key = _obter_chave_gemini()
    if api_key is None:
        return 50

    client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            max_output_tokens=64,
        ),
    )

    try:
        candidate = response.candidates[0]
        part = candidate.content[0]
        text = getattr(part, 'text', None) or getattr(part, 'content', None) or str(part)
        return int(str(text).strip())
    except Exception:
        return 0

# Função para filtrar o dataframe de controle com base no contexto do extrato
def filtrar_por_contexto(mov_ex, df_controle):

    descricao_extrato = str(
        mov_ex.get(
            "descricao_extrato",
            mov_ex.get("descricao",
                mov_ex.get("recurso_controle", "")
            )
        )
    ).upper()

    palavras_extrato = normalizar_texto(descricao_extrato)

    scores = []

    for _, row in df_controle.iterrows():

        descricao_controle = str(
            row.get(
                "descricao_extrato",
                row.get(
                    "descricao",
                    row.get(
                        "recurso_controle",
                        row.get("recurso", "")
                    )
                )
            )
        ).upper()

        palavras_controle = normalizar_texto(descricao_controle)

        intersecao = palavras_extrato.intersection(palavras_controle)

        score = len(intersecao)

        scores.append(score)

    df_controle = df_controle.copy()
    df_controle["score_contexto"] = scores

    filtrado = df_controle[df_controle["score_contexto"] > 0]

    # fallback
    if filtrado.empty:
        return df_controle

    return filtrado

