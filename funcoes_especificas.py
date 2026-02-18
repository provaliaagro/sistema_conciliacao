import streamlit as st
import pandas as pd

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

def converter_valor_extrato(valor_str):
    """
    Converte valores no formato brasileiro com C/D para float
    Agora trata casos com espaço e hífen:
    "1.204,54 C" -> 1204.54
    "- 850,00 D" -> -850.00
    "63.173,85 C" -> 63173.85
    """
    try:
        # Se for None ou vazio
        if valor_str is None:
            return None
            
        valor_str = str(valor_str).strip().upper()
        
        if valor_str == "" or valor_str == "NAN":
            return None
        
        # Remove qualquer hífen no início (com ou sem espaço)
        if valor_str.startswith('-'):
            valor_str = valor_str[1:].strip()
            # Se tinha hífen, já forçamos negativo, independente da letra
            sinal_forcado = -1
        else:
            sinal_forcado = None
        
        # Remove espaços extras e identifica C/D
        # Pode terminar com "C", " D", "C ", etc
        valor_str = valor_str.strip()
        
        # Define sinal baseado na letra (se não tiver sinal_forcado)
        if valor_str.endswith('C'):
            sinal = 1
            numero_limpo = valor_str[:-1].strip()  # Remove 'C' e espaços
        elif valor_str.endswith('D'):
            sinal = -1
            numero_limpo = valor_str[:-1].strip()  # Remove 'D' e espaços
        else:
            sinal = 1
            numero_limpo = valor_str.strip()
        
        # Sobrescreve sinal se tinha hífen no início
        if sinal_forcado is not None:
            sinal = sinal_forcado
        
        # Remove apenas os pontos que são separadores de milhar
        if ',' in numero_limpo:
            partes = numero_limpo.split(',')
            parte_inteira = partes[0]
            parte_decimal = partes[1]
            
            # Remove pontos apenas da parte inteira (milhar)
            parte_inteira = parte_inteira.replace('.', '')
            
            # Junta com ponto como separador decimal
            numero_limpo = parte_inteira + '.' + parte_decimal
        else:
            numero_limpo = numero_limpo.replace('.', '')
        
        # Converte para float e aplica sinal
        return float(numero_limpo) * sinal
        
    except Exception as e:
        print(f"Erro ao converter '{valor_str}': {e}")
        return None
    
def remover_linhas_vazias(df, colunas_verificar=['descricao', 'valor']):
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
    
    return df_limpo

def remover_linhas_desnecessarias(df, coluna_descricao='descricao', palavras_remover=None):
    """
    Remove linhas baseadas em palavras ou partes de palavras no histórico
    
    Args:
        df: DataFrame com os dados
        palavras_remover: Lista de palavras para remover
        coluna_descricao: Nome da coluna indicada
    
    Returns:
        DataFrame filtrado
    """
    if palavras_remover is None:
        palavras_remover = [
            'SALDO BLOQUEADO ANTERIOR', 'A Perfarm', 'SALDO DO DIA', 'SALDO ANTERIOR', 'S A L D O' ]
    
    # Converte tudo para maiúsculo para busca case-insensitive
    descricao_upper = df[coluna_descricao].astype(str).str.upper()
    
    # Cria máscara inicial como False
    mask_remover = descricao_upper.isin([])  # Inicia vazia
    
    # Para cada palavra na lista, busca se aparece em qualquer parte do histórico
    for palavra in palavras_remover:
        mask_remover = mask_remover | descricao_upper.str.contains(palavra, na=False)
    
    # Inverte a máscara: mantém apenas as linhas que NÃO contêm as palavras
    mask_manter = ~mask_remover
    
    df_filtrado = df[mask_manter]
    
    return df_filtrado

def ordernar_arquivo(df):
    
    def formatacao_data(data):
        try:
            # Supondo formato DD/MM/YYYY
            if '/' in str(data):
                dia, mes, ano = str(data).split('/')
                return f"{ano}{mes.zfill(2)}{dia.zfill(2)}"
            # Se já estiver em outro formato, retorna original
            return str(data)
        except:
            return "00000000"  # Para datas inválidas
    
    df['_ordenar'] = df['data'].apply(formatacao_data)
    
    # Ordenar
    df = df.sort_values(by='_ordenar')
    
    # Remover coluna auxiliar
    df = df.drop(columns=['_ordenar'])
    
    # Resetar índice
    df = df.reset_index(drop=True)
    
    return df

def converter_valor_reais(valor_str):
    """
    Converte strings do formato '-R$ 497,21' para float
    Trata automaticamente o sinal negativo
    """
    try:
        valor_str = str(valor_str).strip()
        
        # Verifica se tem sinal negativo
        if valor_str.startswith('-'):
            sinal = -1
            valor_limpo = valor_str[1:]  # Remove o '-'
        else:
            sinal = 1
            valor_limpo = valor_str
        
        # Remove 'R$' e espaços extras
        valor_limpo = valor_limpo.replace('R$', '').strip()
        
        # Remove pontos (separadores de milhar)
        valor_limpo = valor_limpo.replace('.', '')
        
        # Substitui vírgula por ponto (decimal)
        valor_limpo = valor_limpo.replace(',', '.')
        
        # Converte para float e aplica sinal
        return float(valor_limpo) * sinal
        
    except (ValueError, AttributeError, TypeError):
        return None

def contar_movimentacoes(df, coluna_valor='valor_convertido'):
    """
    Conta movimentações, entradas e saídas excluindo linhas com descrição igual a 'SALDO' e derivadas disso
    
    Returns:
        tuple: (total_movimentacoes, total_entradas, total_saidas)
    """
    
    df_movimentacoes = df
    
    # Conta totais
    total_movimentacoes = len(df_movimentacoes)
    
    total_valor = 0
    # Conta entradas (valores positivos) e saídas (valores negativos)
    if coluna_valor in df_movimentacoes.columns:
        entradas = len(df_movimentacoes[df_movimentacoes[coluna_valor] > 0])
        saidas = len(df_movimentacoes[df_movimentacoes[coluna_valor] < 0])
        total_valor += df_movimentacoes[coluna_valor]
    else:
        entradas = saidas = 0
        
    #total_valor = sum(total_valor)
    total_alternativo = 0
    for i in total_valor:
        total_alternativo += i
    st.write(total_alternativo)
    st.stop()
    
    return total_movimentacoes, entradas, saidas, total_valor

def conciliacao_simples(df_extrato, df_controle):
    """
    Compara os valores e datas dos dois dataframes e retorna um dataframe conciliado
    Garante que cada valor converja com apenas um outro valor
    
    Args:
        df_extrato: DataFrame do extrato bancário
        df_controle: DataFrame do controle financeiro
    
    Returns:
        DataFrame com as colunas de conciliação
    """
    
    # Prepara os dataframes
    df_e = df_extrato[['data', 'documento', 'descricao', 'valor_convertido']].copy()
    df_e.columns = ['data_extrato', 'documento_extrato', 'descricao_extrato', 'valor_extrato']
    
    df_c = df_controle[['data', 'recurso', 'contraparte', 'valor_convertido']].copy()
    df_c.columns = ['data_controle', 'recurso_controle', 'contraparte_controle', 'valor_controle']
    
    # Resetar índices para IDs únicos
    df_e = df_e.reset_index(drop=True).reset_index().rename(columns={'index': '_id_extrato'})
    df_c = df_c.reset_index(drop=True).reset_index().rename(columns={'index': '_id_controle'})
    
    # Criar colunas auxiliares para marcar matches
    df_e['_matched'] = False
    df_c['_matched'] = False
    
    # Lista para armazenar os matches encontrados
    matches = []
    
    # PERCORRER POR ORDEM PARA GARANTIR REPRODUTIBILIDADE
    # Ordenar por valor para matching consistente
    df_e_sorted = df_e.sort_values(['valor_extrato', '_id_extrato']).reset_index(drop=True)
    df_c_sorted = df_c.sort_values(['valor_controle', '_id_controle']).reset_index(drop=True)
    
    # Fazer matching 1:1
    c_index = 0
    for e_idx in range(len(df_e_sorted)):
        if df_e_sorted.loc[e_idx, '_matched']:
            continue
            
        valor_e = df_e_sorted.loc[e_idx, 'valor_extrato']
        
        # Encontrar primeiro match não utilizado no controle
        while c_index < len(df_c_sorted):
            if (not df_c_sorted.loc[c_index, '_matched'] and 
                df_c_sorted.loc[c_index, 'valor_controle'] == valor_e):
                
                # Encontrou match!
                matches.append({
                    '_id_extrato': df_e_sorted.loc[e_idx, '_id_extrato'],
                    '_id_controle': df_c_sorted.loc[c_index, '_id_controle']
                })
                
                # Marcar como utilizado
                df_e_sorted.loc[e_idx, '_matched'] = True
                df_c_sorted.loc[c_index, '_matched'] = True
                
                c_index += 1  # Avançar para próximo no controle
                break
            c_index += 1
        else:
            # Se não encontrou match, avançar para próximo no extrato
            c_index = 0  # Resetar busca no controle
    
    # AGORA CRIAR O DATAFRAME FINAL COM TODAS AS LINHAS
    
    # 1. Começar com todos os matches
    matches_df = pd.DataFrame(matches) if matches else pd.DataFrame(
        columns=['_id_extrato', '_id_controle']
    )
    
    # 2. Criar dataframe com todas as linhas do extrato (com ou sem match)
    df_result_e = pd.merge(
        df_e[['_id_extrato', 'data_extrato', 'documento_extrato', 'descricao_extrato', 'valor_extrato']],
        matches_df,
        on='_id_extrato',
        how='left'
    )
    
    # 3. Adicionar dados do controle para as que têm match
    df_result = pd.merge(
        df_result_e,
        df_c[['_id_controle', 'data_controle', 'recurso_controle', 'contraparte_controle', 'valor_controle']],
        on='_id_controle',
        how='left'
    )
    
    # 4. Adicionar as linhas do controle que NÃO foram usadas em nenhum match
    # Primeiro, identificar IDs do controle que não foram usados
    ids_controle_usados = matches_df['_id_controle'].dropna().unique()
    linhas_controle_nao_usadas = df_c[~df_c['_id_controle'].isin(ids_controle_usados)].copy()
    
    # Criar DataFrame para as linhas não usadas do controle
    if not linhas_controle_nao_usadas.empty:
        df_controle_sem_match = pd.DataFrame({
            'data_extrato': [None] * len(linhas_controle_nao_usadas),
            'descricao_extrato': [None] * len(linhas_controle_nao_usadas),
            'documento_extrato': [None] * len(linhas_controle_nao_usadas),
            'valor_extrato': [None] * len(linhas_controle_nao_usadas),
            '_id_extrato': [None] * len(linhas_controle_nao_usadas),
            '_id_controle': linhas_controle_nao_usadas['_id_controle'].values,
            'data_controle': linhas_controle_nao_usadas['data_controle'].values,
            'recurso_controle': linhas_controle_nao_usadas['recurso_controle'].values,
            'contraparte_controle': linhas_controle_nao_usadas['contraparte_controle'].values,
            'valor_controle': linhas_controle_nao_usadas['valor_controle'].values
        })
        
        # Concatenar com os resultados anteriores
        df_result = pd.concat([df_result, df_controle_sem_match], ignore_index=True)
    
    # Remover colunas auxiliares
    df_result = df_result.drop(columns=['_id_extrato', '_id_controle'], errors='ignore')
    
    # Cria status - IMPORTANTE: considerar todas as combinações
    df_result['status_conciliacao'] = df_result.apply(
        lambda x: "CONCILIADA" if (
            pd.notna(x.get('descricao_extrato')) and 
            (pd.notna(x.get('recurso_controle')) or pd.notna(x.get('contraparte_controle')))
        ) else "NÃO CONCILIADO",
        axis=1
    )
    
    # Reordenar colunas para melhor visualização
    col_order = [
        'data_extrato', 'documento_extrato', 'descricao_extrato', 'valor_extrato',
        'data_controle', 'recurso_controle', 'contraparte_controle', 'valor_controle',
        'status_conciliacao'
    ]
    
    # Garantir que todas as colunas existam
    col_order = [col for col in col_order if col in df_result.columns]
    
    return df_result[col_order]

def ordenar_por_data_br(lista_dados, campo_data='data'):
        """Ordena lista de dicionários por data no formato brasileiro DD/MM/YYYY"""
        def chave_ordenacao(item):
            data_str = item.get(campo_data, '')
            if not data_str:
                return (1, '')  # Datas vazias vão para o final
            
            try:
                # Converte DD/MM/YYYY para tuple (ano, mes, dia) para ordenação
                partes = data_str.split('/')
                if len(partes) == 3:
                    dia, mes, ano = partes
                    # Extrai valor numérico para desempate
                    valor = 0
                    if 'valor' in item:
                        valor_str = str(item['valor'])
                        # Se o valor já for numérico
                        if isinstance(item['valor'], (int, float)):
                            valor = float(item['valor'])
                        else:
                            # Tenta extrair de string formatada "R$ 1.234,56"
                            try:
                                valor_limpo = valor_str.replace('R$', '').replace('.', '').replace(',', '.').strip()
                                valor = float(valor_limpo)
                            except:
                                valor = 0
                    
                    return (0, ano, mes, dia, valor)
            except:
                pass
            
            return (1, 9999, 13, 32, float('inf')) # Para datas inválidas
        
        return sorted(lista_dados, key=chave_ordenacao)