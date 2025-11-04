import streamlit as st
import pandas as pd
import funcoes_especificas as func

st.title("Sistema CBA | Provalia")
st.markdown("### Selecione o arquivo do Extrato Bancário")
col1, col2 = st.columns(2)
with col1: 
    extrato = st.file_uploader("Extrato extraído do banco SICOOB no formato Excel", type="xlsx")
# Apenas quando o arquivo de upload do extrato não está vazio
if extrato is not None:
    try:
        indices = ["data", "histórico", "valor"]
        df_extrato = pd.read_excel(extrato, engine="openpyxl")
        df_extrato = df_extrato.iloc[3:]
        df_extrato = df_extrato.iloc[:, 0:3]
        df_extrato.columns = indices
        
        st.session_state['df_extrato'] = df_extrato

        # Mostra o dataframe tratado na tela
        st.write("### Dados do Extrato:")
        st.dataframe(df_extrato)
        if "valor" in df_extrato.columns:
            st.write("DataFrame com linhas vazias removidas")
            df_extrato = func.remover_linhas_vazias(df_extrato)
            st.dataframe(df_extrato)
            st.write("DataFrame com linhas desnecessárias removidas")
            df_extrato = func.remover_linhas_desnecessarias(df_extrato)
            st.dataframe(df_extrato)
            st.write("DataFrame com saldos do dia removidos")
            df_extrato = func.filtrar_saldos_duplicados(df_extrato)
            st.dataframe(df_extrato)
            df_extrato["valor_convertido"] = df_extrato["valor"].apply(func.converter_valor)
                
            # Verifica se há valores que não puderam ser convertidos
            valores_invalidos = df_extrato[df_extrato['valor_convertido'].isna()]
            if not valores_invalidos.empty:
                st.warning(f"DataFrame com {len(valores_invalidos)} de valores não puderam ser convertidos")
                st.dataframe(valores_invalidos[['valor']])
            st.session_state['df_extrato'] = df_extrato
            st.success("Conversão concluída!")
            st.write("DataFrame com valores das transações tratados")
            st.dataframe(df_extrato)
                
        else:
            st.error("Coluna 'valor' não encontrada no arquivo!")
        # Conversão dos valores
                
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")

with col2:
    controle_financeiro = st.file_uploader("Controle Financeiro extraído do sistema Perfarm no formato Excel", type="xlsx")