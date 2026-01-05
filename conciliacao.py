import streamlit as st
import pandas as pd
import funcoes_especificas as func
import relatorio as r

def conciliacao(ex, cf):
    # st.write("### Dataframe Extrato")
    # st.dataframe(ex)
    #st.write("### Dataframe Controle Financeiro")
    #st.dataframe(cf)

    # Extração dos saldos
    saldo_inicial, saldo_final, ex = func.extrair_saldos(ex)
    
    # Quantidade de movimentações
    mov_extrato, entradas_extrato, saidas_extrato = func.contar_movimentacoes(ex)
    mov_controle, entradas_controle, saidas_controle = func.contar_movimentacoes(cf)
    
    #st.write(f"Foram realizadas {mov_extrato} movimentações computadas pelo extrato")
    #st.write(f"Destas {entradas_extrato} foram entradas")
    #st.write(f"Destas {saidas_extrato} foram saídas")
    #st.write("=======================================================================")
    #st.write(f"Foram cadastradas {mov_controle} movimentações no Controle Financeiro")
    #st.write(f"Destas {entradas_controle} foram entradas")
    #st.write(f"Destas {saidas_controle} foram saídas")
    
    # Conciliação Simples
    resultado = func.conciliacao_simples(ex,cf)
     
    # CRIAÇÃO DO RELATÓRIO
    nome_usuario = st.session_state.get('nome', 'Usuário não identificado')
    
    df_relatorico_conv, df_relatorio_div = r.criar_relatorio_conciliação(
        resultado,
        saldo_inicial,
        saldo_final,
        mov_extrato,
        mov_controle,
        nome_usuario
    )
    
    excel_bytes = r.exportar_relatorio_excel(df_relatorico_conv, df_relatorio_div)
    
    return excel_bytes
    
    
    