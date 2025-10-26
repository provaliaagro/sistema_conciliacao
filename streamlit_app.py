import streamlit as st
import pandas as pd

# ----- Estado inicial (garante chaves) -----
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
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
    extrato = st.file_uploader("Extrato extraído do banco SICOOB no formtao Excel", type="xlsx")
    df_extrato = pd.read_excel(extrato)
    st.dataframe(df_extrato)
    
