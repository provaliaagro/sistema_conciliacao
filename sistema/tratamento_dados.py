##### TRATAMENTO DE DADOS #####

# Importações
import pandas as pd

# CONVERSÃO DE VALORES

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
    
# LIMPEZA DE DADOS
    
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

def agrupar_linhas_extrato(df):
    linhas_agrupadas = []
    buffer_descricao = ""

    for _, row in df.iterrows():
        data = row['data']
        valor = row['valor']

        # ⚠️ TRATAMENTO CORRETO DA DESCRIÇÃO
        descricao = row['descricao']
        if pd.notna(descricao):
            descricao = str(descricao).strip()
        else:
            descricao = ""

        # Linha principal
        if pd.notna(data) and str(data).strip() != "":
            if buffer_descricao:
                linhas_agrupadas[-1]['descricao'] += " | " + buffer_descricao
                buffer_descricao = ""

            linhas_agrupadas.append(row.to_dict())

        else:
            # Linha complementar
            if descricao:  # só entra se NÃO for vazio
                if buffer_descricao:
                    buffer_descricao += " " + descricao
                else:
                    buffer_descricao = descricao

    # Final
    if buffer_descricao and linhas_agrupadas:
        linhas_agrupadas[-1]['descricao'] += " | " + buffer_descricao

    return pd.DataFrame(linhas_agrupadas)

# ORDENAÇÃO DE ARQUIVOS

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