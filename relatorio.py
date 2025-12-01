import pandas as pd
from datetime import datetime
import io

def criar_relatorio_conciliação(
    df_conciliado, 
    saldo_inicial, 
    saldo_final, 
    mov_extrato, 
    mov_controle,
    nome_usuario
):
    """
    Cria um relatório completo da conciliação em um DataFrame estruturado
    que será exportado para excel
    """
    
    relatorio_dados = []
    
    # CABEÇALHO DO RELATÓRIO
    relatorio_dados.append(["RELATÓRIO FINAL DE CONCILIAÇÃO BANCÁRIA"])
    relatorio_dados.append([])  # Linha em branco
    relatorio_dados.append(["Usuário Responsável:", nome_usuario])
    relatorio_dados.append(["Data da Realização:", datetime.now().strftime("%d/%m/%Y %H:%M")])
    relatorio_dados.append([])  # Linha em branco
    
    # DADOS GERAIS DA CONCILIAÇÃO
    relatorio_dados.append(["DADOS GERAIS DA CONCILIAÇÃO"])
    relatorio_dados.append(["Saldo Inicial da Conta:", f"R$ {saldo_inicial:,.2f}" if saldo_inicial else "Não identificado"])
    relatorio_dados.append(["Saldo Final da Conta:", f"R$ {saldo_final:,.2f}" if saldo_final else "Não identificado"])
    relatorio_dados.append([])  # Linha em branco
    
    # RESUMO DE MOVIMENTAÇÕES
    relatorio_dados.append(["RESUMO DE MOVIMENTAÇÕES"])
    relatorio_dados.append(["", "EXTRATO", "CONTROLE FINANCEIRO"])
    relatorio_dados.append(["Total de Movimentações:", mov_extrato, mov_controle])
    relatorio_dados.append([])  # Linha em branco
    relatorio_dados.append(["Quantidade de movimentações omitidas no controle financeiro:", mov_extrato - mov_controle])
    relatorio_dados.append([])  # Linha em branco
    
    # ESTATÍSTICAS DA CONCILIAÇÃO
    #conciliadas = len(df_conciliado[df_conciliado['status_conciliacao'] == 'CONCILIADA'])
    #nao_conciliadas = len(df_conciliado[df_conciliado['status_conciliacao'] == 'NÃO CONCILIADO'])
    
    #relatorio_dados.append(["ESTATÍSTICAS DA CONCILIAÇÃO"])
    #relatorio_dados.append(["Transações Conciliadas:", conciliadas])
    #relatorio_dados.append(["Transações Não Conciliadas:", nao_conciliadas])
    #relatorio_dados.append(["Taxa de Conciliação:", f"{(conciliadas/(conciliadas+nao_conciliadas)*100):.1f}%" if (conciliadas+nao_conciliadas) > 0 else "0%"])
    #relatorio_dados.append([])  # Linha em branco
    #relatorio_dados.append([])  # Linha em branco
    
    # OPERAÇÕES DIVERGENTES (NÃO CONCILIADAS)
    operacoes_divergentes = df_conciliado[df_conciliado['status_conciliacao'] == 'NÃO CONCILIADO']
    
    if len(operacoes_divergentes) > 0:
        relatorio_dados.append(["OPERAÇÕES DIVERGENTES (NÃO CONCILIADAS)"])
        relatorio_dados.append([])  # Linha em branco
        
        # Cabeçalho das operações divergentes
        cabecalho = [
            "Data Extrato", "Descrição Extrato", "Valor Extrato", 
            "Data Controle", "Descrição Controle", "Valor Controle", "Status"
        ]
        relatorio_dados.append(cabecalho)
        
        # Adiciona cada operação divergente
        for _, row in operacoes_divergentes.iterrows():
            # Verifica se tem dados de data (pode não ter se for merge outer)
            data_extrato = row.get('data_extrato', '') if 'data_extrato' in row else ''
            data_controle = row.get('data_controle', '') if 'data_controle' in row else ''
            
            linha = [
                data_extrato,
                row.get('descricao_extrato', ''),
                f"R$ {row.get('valor_extrato', 0):,.2f}" if pd.notna(row.get('valor_extrato')) else "",
                data_controle,
                row.get('descricao_controle', ''),
                f"R$ {row.get('valor_controle', 0):,.2f}" if pd.notna(row.get('valor_controle')) else "",
                row.get('status_conciliacao', '')
            ]
            relatorio_dados.append(linha)
    else:
        relatorio_dados.append(["NENHUMA OPERAÇÃO DIVERGENTE ENCONTRADA"])
    
    # Converte para DataFrame
    df_relatorio = pd.DataFrame(relatorio_dados)
    
    return df_relatorio


def exportar_relatorio_excel(df_relatorio):
    """
    Exporta o DataFrame do relatório para Excel em memória
    """
    # Cria um buffer em memória
    output = io.BytesIO()
    
    # Cria o Excel writer
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Salva o relatório principal
        df_relatorio.to_excel(
            writer,
            index=False,
            header=False,  # Já temos cabeçalhos no DataFrame
            sheet_name='Relatório Final Conciliação'
        )
        
        # Ajusta a largura das colunas
        worksheet = writer.sheets['Relatório Final Conciliação']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    # Pega os bytes
    excel_bytes = output.getvalue()
    output.close()
    
    return excel_bytes