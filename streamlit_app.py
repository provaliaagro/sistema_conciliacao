import streamlit as st
import pandas as pd
import funcoes_especificas as func

# ----- Estado inicial (garante chaves) -----
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "nome" not in st.session_state:
    st.session_state["nome"] = ""

# ----- Função de autenticação (substitua validação real) -----
def try_login(username, pw):
    # Exemplo simples: checar contra st.secrets["users"]   
    users = st.secrets["users"]
    if username in users:
        nome_completo, email, senha_cadastrada = users[username]
        if senha_cadastrada == pw:
            st.session_state["authenticated"] = True
            st.session_state["nome"] = nome_completo
            st.rerun()
    else:
        st.error("Usuário ou senha incorretos.")

# ----- Fluxo: se não autenticado, mostra o formulário de login -----
if not st.session_state["authenticated"]:
    st.title("Sistema CBA | Provalia")
    st.subheader("🔐 Login")
    username = st.text_input("Nome de usuário", key="login_username")
    senha = st.text_input("Senha", type="password", key="login_senha")
    if st.button("Entrar"):
        try_login(username, senha)

# ----- Fluxo protegido: mostra a área da conciliação (após login) -----
else:
    st.title("Sistema CBA | Provalia")
    st.success(f"Bem-vindo(a), {st.session_state["nome"]}!")
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
            
            st.session_state['df_extrato'] = df_extrato

            # Mostra o dataframe tratado na tela
            st.write("### Dados do Extrato:")
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
                st.dataframe(df_extrato)
                
                st.session_state['df_extrato'] = df_extrato
                
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")

# Para fazer upload do controle financeiro
if extrato is not None:
    controle_financeiro = st.file_uploader("Controle Financeiro extraído do sistema Perfarm no formato Excel", type="xlsx")
    st.write("### Dados do Controle Financeiro:")
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
            st.dataframe(df_controle)
            st.session_state['df_controle'] = df_controle
            
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")
    
    
