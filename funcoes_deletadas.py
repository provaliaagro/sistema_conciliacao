import pandas as pd


def extrair_saldos(df, coluna_descricao='descricao', coluna_valor='valor_convertido'):
    """
    Extrai saldo anterior e saldo do dia do dataframe
    
    Returns:
        tuple: (saldo_anterior, saldo_dia)
    """
    palavras_filtro = ['SALDO ANTERIOR', 'SALDO DO DIA']
    
    # Converte para maiúsculo
    descricao_upper = df[coluna_descricao].astype(str).str.upper()
    
    # Encontra linhas com os saldos
    mask_saldos = descricao_upper.str.contains('|'.join(palavras_filtro), na=False)
    df_saldos = df[mask_saldos].copy()
    
    saldo_anterior = None
    saldo_dia = None
    
    # Dataframe SEM os saldos
    df_sem_saldos = df[~mask_saldos].copy()
    
    # Extrai os valores
    for idx, row in df_saldos.iterrows():
        descricao = str(row[coluna_descricao]).upper()
        valor = row[coluna_valor]
        
        if 'SALDO ANTERIOR' in descricao:
            saldo_anterior = valor
        elif 'SALDO DO DIA' in descricao:
            saldo_dia = valor
    
    return saldo_anterior, saldo_dia, df_sem_saldos


def filtrar_saldos_duplicados(df, coluna_descricao='descricao', coluna_data='data'):
    """
    Mantém apenas o último saldo do dia e remove os demais
    """
    # Identifica linhas que contém 'SALDO' no histórico
    mask_saldos = df[coluna_descricao].astype(str).str.upper().str.contains('SALDO DO DIA', na=False)
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
    
    return df_filtrado


def converter_coluna_data_brasileira(df, coluna_data='data'):
    """
    Converte coluna inteira de datas para formato brasileiro
    """
    df_temp = df.copy()
    
    # Converte para datetime
    df_temp[coluna_data] = pd.to_datetime(df_temp[coluna_data], errors='coerce')
    
    # Formata para brasileiro
    df_temp[coluna_data] = df_temp[coluna_data].dt.strftime('%d/%m/%Y')
    
    return df_temp

def conciliacao_simples(df_extrato, df_controle):
    """
    Compara os valores e datas dos dois dataframes e retorna um dataframe conciliado
    
    Args:
        df_extrato: DataFrame do extrato bancário
        df_controle: DataFrame do controle financeiro
    
    Returns:
        DataFrame com as colunas de conciliação
    """
    
    # Prepara os dataframes
    df_e = df_extrato[['data', 'descricao', 'valor_convertido',]].copy()
    df_e.columns = ['data_extrato', 'descricao_extrato', 'valor_extrato']
    
    df_c = df_controle[['data','descricao', 'valor_convertido']].copy()
    df_c.columns = ['data_controle', 'descricao_controle', 'valor_controle']
    
    # Adicionar IDs únicos para cada linha
    df_e['_id'] = range(len(df_e))
    df_c['_id'] = range(len(df_c))
    
    # Faz o merge por valor (strings no formato brasileiro)
    df_final = pd.merge(
        df_e,
        df_c,
        left_on=['valor_extrato'],
        right_on=['valor_controle'],
        how='outer',
        suffixes=('_extrato','_controle')
    )
    
    # Remover IDs
    df_final = df_final.drop(columns=['_id_extrato', '_id_controle'])
    
    # Cria status
    df_final['status_conciliacao'] = df_final.apply(
        lambda x: "CONCILIADA" if (
            pd.notna(x['descricao_extrato']) and 
            pd.notna(x['descricao_controle'])
        ) else "NÃO CONCILIADO",
        axis=1
    )
    
    return df_final