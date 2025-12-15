import streamlit as st
import pandas as pd
from datetime import datetime
import io
import funcoes_especificas as func
import conciliacao as c

# Inicializando as variáves de estado do extrato e do controle financeiro:
st.session_state.df_extrato = None
st.session_state.df_controle = None
st.session_state.excel = None

   
if st.session_state.df_extrato is None:
    st.title("Sistema CBA | Provalia")
    st.markdown("### Selecione o arquivo do Extrato Bancário") 
    extrato = st.file_uploader("Extrato extraído do banco SICOOB no formato Excel", type="xlsx")
    # Para fazer o tratamento de dados do extrato
    if extrato is not None:
        try:
            indices_extrato = ["data", "descricao", "valor"]
            df_extrato = pd.read_excel(extrato, engine="openpyxl")
            df_extrato = df_extrato.iloc[3:]
            df_extrato = df_extrato.iloc[:, 0:3]
            df_extrato.columns = indices_extrato
            
            df_extrato = func.ordernar_arquivo(df_extrato)
                        
            st.session_state['df_extrato'] = df_extrato

            # Mostra o dataframe tratado na tela
            # st.write("### Dados do Extrato:")
            if "valor" in df_extrato.columns:
                df_extrato = func.remover_linhas_vazias(df_extrato)
                df_extrato = func.remover_linhas_desnecessarias(df_extrato)
                df_extrato = func.filtrar_saldos_duplicados(df_extrato)
                df_extrato = func.converter_coluna_data_brasileira(df_extrato)
                df_extrato["valor_convertido"] = df_extrato["valor"].apply(func.converter_valor)
                    
                # Verifica se há valores que não puderam ser convertidos
                valores_invalidos = df_extrato[df_extrato['valor_convertido'].isna()]
                if not valores_invalidos.empty:
                    st.warning(f"DataFrame com {len(valores_invalidos)} de valores não puderam ser convertidos")
                    st.dataframe(valores_invalidos[['valor']])
                st.session_state['df_extrato'] = df_extrato
                
                # Mostra o dataframe na tela
                # st.dataframe(df_extrato)
                
                # Salvando o extrato no session_state
                st.session_state['df_extrato'] = df_extrato
                
            else:
                st.error("Coluna 'valor' não encontrada no arquivo!")
                st.stop()
                    
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")
    # Para fazer upload do controle financeiro
    if st.session_state.df_extrato is not None:
        controle_financeiro = st.file_uploader("Controle Financeiro extraído do sistema Perfarm no formato Excel", type="xlsx")
        # st.write("### Dados do Controle Financeiro:")
        # Para fazer o tratamento de dados do controle financeiro
        if controle_financeiro is not None:
            try: 
                indices_controle = ["data", "descricao", "valor"]
                df_controle = pd.read_excel(controle_financeiro, engine="openpyxl")
                st.session_state['df_controle'] = df_controle
                df_controle = df_controle.iloc[5:]
                df_controle = df_controle.iloc[:,[2,4,8]]
                df_controle.columns = indices_controle
                df_controle = func.remover_linhas_vazias(df_controle)
                df_controle["valor_convertido"] = df_controle["valor"].apply(func.converter_valor_reais)
                # Verifica se há valores que não puderam ser convertidos
                valores_invalidos = df_controle[df_controle['valor_convertido'].isna()]
                if not valores_invalidos.empty:
                    st.warning(f"DataFrame com {len(valores_invalidos)} de valores não puderam ser convertidos")
                    st.dataframe(valores_invalidos[['valor']])
                    
                # Mostra o dataframe na tela
                # st.dataframe(df_controle)

                # Salvando o controle financeiro no session_state
                st.session_state['df_controle'] = df_controle
                
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")
                st.stop()

if st.session_state.df_controle is not None:
    if st.button("Processar Conciliação"):
        barra_progresso = st.progress(0)
        barra_progresso.progress(20)
        excel_bytes = c.conciliacao(st.session_state.df_extrato, st.session_state.df_controle)
        barra_progresso.progress(50)
        st.session_state.excel = excel_bytes
        barra_progresso.progress(70)
        
if st.session_state.excel is not None:
    barra_progresso.progress(100)
    st.download_button(
        label="📥 Baixar Relatório Excel",
        data=excel_bytes,
        file_name=f"relatorio_conciliação_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
            
        
        