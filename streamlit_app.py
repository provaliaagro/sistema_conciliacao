 # Primeiro commit 🚀

import streamlit as st

# Configuração do site
st.set_page_config(page_title="Sistema de Conciliação", page_icon="🚀")

st.title("Sistema de Conciliação | Provalia")
# nome = st.text_input("Digite seu nome: ")
# st.write(f"seu nome é {nome}")
# aceita = st.checkbox("Aceita os termos?")
# st.write(aceita)

# st.sidebar.title("Teste")
st.title("Login")
username = st.text_input("Nome de Usuário", type="default")
senha = st.text_input("Senha", type="password")

if st.button("Entrar"):
    users = st.secrets["users"]
    # Verifica se o nome está cadastrado
    if username in users:
        nome_completo, email_cadastrado, senha_cadastrada = users[username]
        # Compara credenciais
        if senha == senha_cadastrada:
            st.success(f"Bem-vindo(a), {nome_completo}!")
            st.write(f"Email do responsável pela conciliação: **{email_cadastrado}**")
            # Aqui entra o restante da lógica da conciliação...
        else:
            st.error("E-mail ou senha incorretos.")
    else:
        st.error("Usuário não encontrado.")