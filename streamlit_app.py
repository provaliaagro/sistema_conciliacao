import streamlit as st

# ----- Estado inicial (garante chaves) -----
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# ----- Função de autenticação (substitua validação real) -----
def try_login(usename, pw):
    # Exemplo simples: checar contra st.secrets["users"]   
    users = st.secrets["users"]
    if username in users:
        nome_completo, email, senha_cadastrada = users[username]
        if senha_cadastrada == pw:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.experimental_rerun()
    else:
        st.error("Usuário ou senha incorretos.")

# ----- Fluxo: se não autenticado, mostra o formulário de login -----
if not st.session_state["authenticated"]:
    st.header("🔐 Login")
    username = st.text_input("Nome de usuário", key="login_user")        # key evita reuso
    senha = st.text_input("Senha", type="password", key="login_pw")
    if st.button("Entrar"):
        try_login(username, senha)

# ----- Fluxo protegido: mostra a área da conciliação (após login) -----
else:
    st.success(f"Bem-vindo(a), {st.session_state['username']} — sessão autenticada.")
    # A partir daqui, renderize o resto da aplicação (upload, processamento, relatório)
    st.write("Área da conciliação — aqui vai o resto do app.")
