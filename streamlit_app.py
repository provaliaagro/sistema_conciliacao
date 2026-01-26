import streamlit as st
import pandas as pd
from datetime import datetime
import funcoes_especificas as func
import conciliacao as c

# ----- Estado inicial (garante chaves) -----
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "nome" not in st.session_state:
    st.session_state.nome = ""

# ----- Função de autenticação (substitua validação real) -----
def try_login(username, pw):
    # Exemplo simples: checar contra st.secrets["users"]   
    users = st.secrets["users"]
    if username in users:
        nome_completo, senha_cadastrada = users[username]
        if senha_cadastrada == pw:
            st.session_state.authenticated = True
            st.session_state.nome = nome_completo
            st.rerun()
    else:
        st.error("Usuário ou senha incorretos.")

# ----- Fluxo: se não autenticado, mostra o formulário de login -----
if not st.session_state.authenticated:
    st.title("Sistema CBA | Provalia")
    st.subheader("🔐 Login")
    username = st.text_input("Nome de usuário", key="login_username")
    senha = st.text_input("Senha", type="password", key="login_senha")
    if st.button("Entrar"):
        try_login(username, senha)
    st.stop()

# ----- Fluxo protegido: mostra a área da conciliação (após login) -----

# Inicializando as variáves de estado do extrato e do controle financeiro:
st.session_state.df_extrato = None
st.session_state.df_controle = None
st.session_state.excel = None

st.title("Sistema CBA | Provalia")
st.success(f"Bem-vindo(a), {st.session_state.nome}!")
st.markdown("### Saldos Relacionados à conciliação:") 
saldo_inicial = st.number_input("Informe o saldo inicial (R$):")
st.session_state.saldo_inicial = saldo_inicial

if st.session_state.df_extrato is None:
    st.markdown("### Selecione o arquivo do Extrato Bancário") 
    extrato = st.file_uploader("Extrato extraído do banco SICOOB no formato Excel", type="xlsx")
    # Para fazer o tratamento de dados do extrato
    if extrato is not None:
        try:
            indices_extrato = ["data", "descricao", "valor"]
            df_extrato = pd.read_excel(extrato, engine="openpyxl", header=1)
            df_extrato = df_extrato[["DATA", "HISTÓRICO", "VALOR"]]
            df_extrato.columns = indices_extrato
            
            df_extrato = func.ordernar_arquivo(df_extrato)
                        
            st.session_state['df_extrato'] = df_extrato

            # Mostra o dataframe tratado na tela
            # st.write("### Dados do Extrato:")
            if "valor" in df_extrato.columns:
                df_extrato = func.remover_linhas_vazias(df_extrato)
                df_extrato = func.remover_linhas_desnecessarias(df_extrato)
                df_extrato["valor_convertido"] = df_extrato["valor"].apply(func.converter_valor_extrato)
                
                # Verifica se há valores que não puderam ser convertidos
                valores_invalidos = df_extrato[df_extrato['valor_convertido'].isna()]
                if not valores_invalidos.empty:
                    st.warning(f"DataFrame com {len(valores_invalidos)} de valores não puderam ser convertidos")
                    st.dataframe(valores_invalidos[['valor']])
                
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
        st.markdown("### Selecione o arquivo do Controle Financeiro") 
        controle_financeiro = st.file_uploader("Controle Financeiro extraído do sistema Perfarm no formato Excel", type="xlsx")
        # st.write("### Dados do Controle Financeiro:")
        # Para fazer o tratamento de dados do controle financeiro
        if controle_financeiro is not None:
            try: 
                indices_controle = ["data", "recurso", "contraparte", "valor"]
                df_controle = pd.read_excel(controle_financeiro, engine="openpyxl", header=5)
                st.session_state['df_controle'] = df_controle
                df_controle = df_controle[["Data", "Recurso", "Contraparte", "Valor"]]
                df_controle.columns = indices_controle
                df_controle = func.remover_linhas_vazias(df_controle)
                df_controle = func.remover_linhas_desnecessarias(df_controle, 'recurso')
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
        excel_bytes = c.conciliacao(st.session_state.df_extrato, st.session_state.df_controle, st.session_state.saldo_inicial)
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