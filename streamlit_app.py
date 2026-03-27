import streamlit as st
import pandas as pd
from datetime import datetime
import funcoes_especificas as func
import conciliacao as c

# Inicialização do Sistema
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "nome" not in st.session_state:
    st.session_state.nome = ""

# Função de autenticação
def try_login(username, pw):
    # Exemplo simples: checar contra st.secrets["users"]   
    users = st.secrets["users"]
    if username in users:
        nome_completo, senha_cadastrada = users[username]
        if senha_cadastrada == pw:
            st.session_state.authenticated = True
            st.session_state.nome = nome_completo
    else:
        st.error("Usuário ou senha incorretos.")

# Login
if not st.session_state.authenticated:
    st.title("Sistema CBA | Provalia")
    st.subheader("🔐 Login")
    username = st.text_input("Nome de usuário", key="login_username")
    senha = st.text_input("Senha", type="password", key="login_senha")
    if st.button("Entrar"):
        try_login(username, senha)
    st.stop()

# Sistema Autenticado

# Inicializando as variáves de estado do extrato e do controle financeiro:
st.session_state.df_extrato = None
st.session_state.df_controle = None
st.session_state.excel = None

# Tela Inicial
st.title("Sistema CBA | Provalia")
st.success(f"Bem-vindo(a), {st.session_state.nome}!")
st.markdown("### Saldos Relacionados à conciliação:") 

# ENTRADA DO SALDO
saldo_inicial = st.number_input("Informe o saldo inicial (R$):")
st.session_state.saldo_inicial = saldo_inicial

# UPLOAD DOS ARQUIVOS
if st.session_state.df_extrato is None:
    
    # entrada do extrato
    st.markdown("### Selecione o arquivo do Extrato Bancário")
    
    # Campo de Seleção
    st.session_state.tipo_extrato = st.radio(
            "Selecione o banco emissor do extrato:",
            ["SICOOB", "Banco do Brasil", "Extrato Padrão"]
        )
    
    # EXTRATO SICOOB
    if st.session_state.tipo_extrato == "SICOOB":
        # Upload do arquivo
        extrato = st.file_uploader("Extrato extraído do banco SICOOB no formato Excel", type="xlsx")
        
        if extrato is not None:
            try:
                # Índices e organização inicial
                indices_extrato = ["data", "documento", "descricao", "valor"]
                df_extrato = pd.read_excel(extrato, engine="openpyxl", header=1)
                df_extrato = df_extrato[["DATA", "DOCUMENTO", "HISTÓRICO", "VALOR"]]
                df_extrato.columns = indices_extrato
                df_extrato = func.ordernar_arquivo(df_extrato)
                df_extrato = df_extrato.astype(object)
                st.session_state['df_extrato'] = df_extrato # Salvando a primeira versão no sistema

                # Tratamento dos dados
                if "valor" in df_extrato.columns:
                    df_extrato = func.remover_linhas_vazias(df_extrato)
                    df_extrato = func.remover_linhas_desnecessarias(df_extrato)
                    df_extrato["valor_convertido"] = df_extrato["valor"].apply(func.converter_valor_extrato)
                    df_extrato['valor_convertido'] = pd.to_numeric(df_extrato['valor_convertido'], errors='coerce')
                    
                    # Validação da Conversão dos valores
                    valores_invalidos = df_extrato[df_extrato['valor_convertido'].isna()]
                    if not valores_invalidos.empty:
                        df_extrato = df_extrato.dropna(subset=['valor_convertido'])
                    
                    # Salvando o extrato no sistema
                    st.session_state['df_extrato'] = df_extrato
                    
                else:
                    st.error("Coluna 'valor' não encontrada no arquivo!")
                    st.stop()
                        
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")
    
    # EXTRATO BANCO DO BRASIL
    elif st.session_state.tipo_extrato == "Banco do Brasil":
        # Upload do arquivo
        extrato = st.file_uploader("Extrato extraído do Banco do Brasil no formato Excel", type="xlsx")
        
        if extrato is not None:
            try:
                # Índices e organização inicial
                indices_extrato = ["data", "documento", "descricao", "valor"]
                df_extrato = pd.read_excel(extrato, engine="openpyxl", header=0)
                df_extrato = df_extrato[["Data", "N° documento", "Lançamento", "Detalhes", "Valor"]]
                df_extrato["Lançamento"] = df_extrato["Lançamento"].fillna('--') + " | " + df_extrato["Detalhes"].fillna('--')
                df_extrato = df_extrato[["Data", "N° documento", "Lançamento", "Valor"]]
                df_extrato.columns = indices_extrato
                #df_extrato = func.ordernar_arquivo(df_extrato)
                st.session_state['df_extrato'] = df_extrato # Salvando a primeira versão no sistema
                
                # Tratamento dos dados
                if "valor" in df_extrato.columns:
                    df_extrato = func.remover_linhas_vazias(df_extrato)
                    df_extrato = func.remover_linhas_desnecessarias(df_extrato)
                    
                    # Conversão do Valor para Número
                    df_extrato["valor_convertido"] = df_extrato["valor"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
                    df_extrato["valor_convertido"] = pd.to_numeric(df_extrato["valor_convertido"], errors="coerce")
                    
                    # Salvando o extrato no sistema
                    st.session_state['df_extrato'] = df_extrato
                    
                else:
                    st.error("Coluna 'valor' não encontrada no arquivo!")
                    st.stop()
                        
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")
    
    # EXTRATO PADRÃO
    elif st.session_state.tipo_extrato == "Extrato Padrão":
        # Upload do arquivo
        extrato = st.file_uploader("Extrato no formato Excel padrão", type="xlsx")
        
        if extrato is not None:
            try:
                # Índices e organização inicial
                indices_extrato = ["data", "documento", "descricao", "valor"]
                df_extrato = pd.read_excel(extrato, engine="openpyxl", header=0)
                df_extrato = df_extrato[["DATA", "DOCUMENTO", "DESCRIÇÃO", "INFORMAÇÕES ADICIONAIS", "VALOR"]]
                df_extrato["DESCRIÇÃO"] = df_extrato["DESCRIÇÃO"].fillna('--') + ' | ' + df_extrato["INFORMAÇÕES ADICIONAIS"].fillna('--')
                df_extrato = df_extrato[["DATA", "DOCUMENTO", "DESCRIÇÃO", "VALOR"]]
                df_extrato.columns = indices_extrato
                df_extrato = func.ordernar_arquivo(df_extrato)
                st.session_state['df_extrato'] = df_extrato # Salvando a primeira versão no sistema

                # Tratamento dos dados
                if "valor" in df_extrato.columns:
                    df_extrato = func.remover_linhas_vazias(df_extrato)
                    df_extrato = func.remover_linhas_desnecessarias(df_extrato)
                    df_extrato["valor_convertido"] = df_extrato["valor"]
                    df_extrato['valor_convertido'] = pd.to_numeric(df_extrato['valor_convertido'], errors='coerce')
                    
                    # Validação da Conversão de Valores
                    valores_invalidos = df_extrato[df_extrato['valor_convertido'].isna()]
                    if not valores_invalidos.empty:
                        df_extrato = df_extrato.dropna(subset=['valor_convertido']) 
                    
                    # Salvando o extrato no sistema
                    st.session_state['df_extrato'] = df_extrato
                    
                else:
                    st.error("Coluna 'valor' não encontrada no arquivo!")
                    st.stop()
                        
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")
    
    # entrada do controle financeiro
    if st.session_state.df_extrato is not None:
        st.markdown("### Selecione o arquivo do Controle Financeiro") 
        
        # Campo de Seleção
        st.session_state.tipo_controle = st.radio(
            "Selecione o tipo de Controle Financeiro:",
            ["Controle Financeiro Perfarm", "Controle Financeiro Padrão"]
        )      
        
        # CONTROLE PERFARM
        if st.session_state.tipo_controle == "Controle Financeiro Perfarm":
            # Upload do arquivo
            controle_financeiro = st.file_uploader("Controle Financeiro extraído do sistema Perfarm no formato Excel", type="xlsx")
            
            if controle_financeiro is not None:
                try: 
                    # Índices e organização inicial
                    indices_controle = ["data", "descricao", "contraparte", "plano de contas", "valor"]
                    df_controle = pd.read_excel(controle_financeiro, engine="openpyxl", header=5)
                    st.session_state['df_controle'] = df_controle
                    df_controle = df_controle[["Data", "Recurso", "Contraparte", "Plano de Contas", "Valor"]]
                    df_controle.columns = indices_controle
                    st.session_state['df_controle'] = df_controle # Salvando a primeira versão no sistema
                    
                    # Tratamento dos dados
                    df_controle = func.remover_linhas_vazias(df_controle)
                    df_controle = func.remover_linhas_desnecessarias(df_controle, 'descricao')
                    df_controle["valor_convertido"] = df_controle["valor"].apply(func.converter_valor_reais)
                    
                    # Validação da Conversão dos valores
                    valores_invalidos = df_controle[df_controle['valor_convertido'].isna()]
                    if not valores_invalidos.empty:
                        df_controle = df_controle.dropna(subset=['valor_convertido'])
                        
                    # Salvando o controle financeiro no sistema
                    st.session_state['df_controle'] = df_controle
                    
                except Exception as e:
                    st.error(f"Erro ao processar arquivo: {e}")
                    st.stop()
        
        # CONTROLE PADRÃO
        elif st.session_state.tipo_controle == "Controle Financeiro Padrão":
            # Upload do arquivo
            controle_financeiro = st.file_uploader("Controle Financeiro no formato Excel Padrão", type="xlsx")

            if controle_financeiro is not None:
                try: 
                    # Índices e organização inicial
                    indices_controle = ["data", "descricao", "contraparte", "plano de contas", "valor"]
                    df_controle = pd.read_excel(controle_financeiro, engine="openpyxl", header=0)
                    st.session_state['df_controle'] = df_controle
                    df_controle = df_controle[["Data", "Descrição", "Contraparte", "Plano de Contas", "Valor"]]
                    df_controle.columns = indices_controle
                    st.session_state['df_controle'] = df_controle # Salvando a primeira versão no sistema
                    
                    # Tratamento dos dados
                    df_controle = func.remover_linhas_vazias(df_controle)
                    df_controle["valor_convertido"] = df_controle["valor"]
                    
                    # Salvando o controle financeiro no sistema
                    st.session_state['df_controle'] = df_controle
                    
                except Exception as e:
                    st.error(f"Erro ao processar arquivo: {e}")
                    st.stop()
                    
# PROCESSO DE CONCILIAÇÃO                                                            
if st.session_state.df_controle is not None:
    if st.button("Processar Conciliação"):
        barra_progresso = st.progress(0)
        barra_progresso.progress(20)
        
        # CHAMADA DA FUNÇÃO
        excel_bytes = c.conciliacao(st.session_state.df_extrato, st.session_state.df_controle, st.session_state.saldo_inicial)
        
        barra_progresso.progress(50)
        
        # SALVANDO O RESULTADO DA CONCILIAÇÃO NO SISTEMA
        st.session_state.excel = excel_bytes
        
        barra_progresso.progress(70)


# BOTÃO DE DOWNLOAD DO RELATÓRIO        
if st.session_state.excel is not None:
    barra_progresso.progress(100)
    st.download_button(
        label="📥 Baixar Relatório Excel",
        data=excel_bytes,
        file_name=f"relatorio_conciliação_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )