import streamlit as st
import pandas as pd

st.title("Sistema CBA | Provalia")
st.markdown("### Selecione o arquivo do Extrato Bancário")
extrato = st.file_uploader("Extrato extraído do banco SICOOB no formato Excel", type="xlsx")
if extrato != None:
    indices = ["data", "histórico", "valor"]
    df_extrato = pd.read_excel(extrato, engine="openpyxl")
    df_extrato = df_extrato.iloc[3:]
    df_extrato = df_extrato.iloc[:, 0:3]
    df_extrato.columns = indices
    st.dataframe(df_extrato)
    
