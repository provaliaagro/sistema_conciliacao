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