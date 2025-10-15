 # Primeiro commit 🚀

import streamlit as st

# Configuração do site
st.set_page_config(page_title="Sistema de Conciliação", page_icon="🚀")

st.title("Sistema de Conciliação | Provalia")
nome = st.text_input("Digite seu nome: ")
st.write(f"seu nome é {nome}")
aceita = st.checkbox("Aceita os termos?")
st.write(aceita)

st.sidebar.title("Teste")