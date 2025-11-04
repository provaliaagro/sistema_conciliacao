import streamlit as st
import pandas as pd

# funcoes_especificas.py

def converter_valor(valor_str):
    """
    Converte valores no formato brasileiro com C/D para float
    Exemplos:
    "3.256,00C" -> 3256.00
    "3.256,00D" -> -3256.00
    "125,50" -> 125.50
    "1000,00" -> 1000.00
    """
    try:
        valor_str = str(valor_str).strip().upper()
        
        # Define sinal: C = positivo, D = negativo
        if valor_str.endswith('C'):
            sinal = 1
            numero_limpo = valor_str[:-1]  # Remove o 'C'
        elif valor_str.endswith('D'):
            sinal = -1
            numero_limpo = valor_str[:-1]  # Remove o 'D'
        else:
            sinal = 1
            numero_limpo = valor_str
        
        # Remove apenas os pontos que são separadores de milhar
        # Verifica se tem vírgula (formato brasileiro)
        if ',' in numero_limpo:
            # Separa parte inteira e decimal
            partes = numero_limpo.split(',')
            parte_inteira = partes[0]
            parte_decimal = partes[1]
            
            # Remove pontos apenas da parte inteira (milhar)
            parte_inteira = parte_inteira.replace('.', '')
            
            # Junta com ponto como separador decimal
            numero_limpo = parte_inteira + '.' + parte_decimal
        else:
            # Se não tem vírgula, trata como número inteiro
            numero_limpo = numero_limpo.replace('.', '')
        
        # Converte para float e aplica sinal
        return float(numero_limpo) * sinal
        
    except:
        return None
    
def remover_linhas_vazias(df, colunas_verificar=['histórico', 'valor']):
    """
    Remove linhas com valores vazios/None nas colunas especificadas
    
    Args:
        df: DataFrame com os dados
        colunas_verificar: Lista de colunas para verificar vazios
    
    Returns:
        DataFrame sem linhas vazias
    """
    df_limpo = df.copy()
    
    for coluna in colunas_verificar:
        if coluna in df_limpo.columns:
            # Remove linhas onde a coluna é None, NaN, vazia ou string vazia
            mask = (
                df_limpo[coluna].notna() & 
                (df_limpo[coluna].astype(str).str.strip() != '') &
                (df_limpo[coluna].astype(str).str.strip() != 'NAN') &
                (df_limpo[coluna].astype(str).str.strip() != 'NONE')
            )
            df_limpo = df_limpo[mask]
    
    linhas_removidas = len(df) - len(df_limpo)
    st.write(f"Linhas vazias removidas: {linhas_removidas}")
    
    return df_limpo

    

def remover_linhas_desnecessarias(df, palavras_remover=None, coluna_historico='histórico'):
    """
    Remove linhas baseadas em palavras ou partes de palavras no histórico
    
    Args:
        df: DataFrame com os dados
        palavras_remover: Lista de palavras para remover
        coluna_historico: Nome da coluna indicada
    
    Returns:
        DataFrame filtrado
    """
    if palavras_remover is None:
        palavras_remover = [
            'SALDO BLOQ.ANTERIOR', 'SALDO BLOQ.C.CORRENTE:', 'VENCTO CHEQUE ESPECIAL:', 'TAXA CHEQUE ESPECIAL',
            'CUSTO EFETIVO TOTAL', 'EXTRATOS EMITIDOS ATÉ', 'SAC', 'OUVIDORIA', 'LIMITE CHEQUE ESPECIAL',
            'SALDO DISPONÍVEL', 'SALDO EM C.CORRENTE', 'JUROS CHQ ESPECIAL'
        ]
    
    # Converte tudo para maiúsculo para busca case-insensitive
    historico_upper = df[coluna_historico].astype(str).str.upper()
    
    # Cria máscara inicial como False
    mask_remover = historico_upper.isin([])  # Inicia vazia
    
    # Para cada palavra na lista, busca se aparece em qualquer parte do histórico
    for palavra in palavras_remover:
        mask_remover = mask_remover | historico_upper.str.contains(palavra, na=False)
    
    # Inverte a máscara: mantém apenas as linhas que NÃO contêm as palavras
    mask_manter = ~mask_remover
    
    df_filtrado = df[mask_manter]
    
    print(f"Filtro aplicado: {len(df) - len(df_filtrado)} linhas removidas")
    
    return df_filtrado

# funcoes_especificas.py

def filtrar_saldos_duplicados(df, coluna_historico='histórico', coluna_data='data'):
    """
    Mantém apenas o último saldo do dia e remove os demais
    """
    # Identifica linhas que contém 'SALDO' no histórico
    mask_saldos = df[coluna_historico].astype(str).str.upper().str.contains('SALDO DO DIA', na=False)
    linhas_saldos = df[mask_saldos]
    linhas_nao_saldos = df[~mask_saldos]
    
    # Se não há saldos, retorna o dataframe original
    if linhas_saldos.empty:
        return df
    
    # Encontra o último saldo (maior índice)
    ultimo_saldo_idx = linhas_saldos.index.max()
    
    # Mantém apenas o último saldo
    ultimo_saldo = df.loc[[ultimo_saldo_idx]]
    
    # Combina: não-saldos + último saldo
    df_filtrado = pd.concat([linhas_nao_saldos, ultimo_saldo]).sort_index()
    
    print(f"Saldos tratados: {len(linhas_saldos)} saldos encontrados, {len(linhas_saldos) - 1} removidos")
    
    return df_filtrado