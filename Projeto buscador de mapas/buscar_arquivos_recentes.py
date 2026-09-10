"""
Script: buscar_arquivos_recentes.py

Analisa uma pasta e todas as suas subpastas, procurando por arquivos cujo
nome contenha os termos informados (separados por ponto e vírgula) e retorna,
para cada termo, o arquivo mais recente encontrado (baseado na data de
modificação).

Uso:
    python buscar_arquivos_recentes.py

O script vai pedir:
    1. O caminho da pasta a ser analisada
    2. Os nomes (ou trechos de nomes) dos arquivos, separados por ";"

Exemplo de entrada:
    Pasta: C:\\Users\\Usuario\\Documents
    Arquivos: relatorio; planilha; contrato

O script vai procurar recursivamente por arquivos cujo nome contenha
"relatorio", "planilha" ou "contrato" e mostrar o mais recente de cada grupo.
"""

import os
import shutil
from datetime import datetime


def buscar_arquivos_recentes(pasta_raiz, termos_busca):
    """
    Percorre a pasta_raiz e subpastas, encontra os arquivos cujo nome
    contém cada termo em termos_busca, e retorna o mais recente de cada grupo.

    :param pasta_raiz: caminho da pasta onde a busca vai começar
    :param termos_busca: lista de strings (termos/nomes a procurar)
    :return: dicionário {termo: (caminho_completo, data_modificacao) ou None}
    """
    # Inicializa o resultado: cada termo começa sem nenhum arquivo encontrado
    resultados = {termo: None for termo in termos_busca}

    if not os.path.isdir(pasta_raiz):
        print(f"Erro: a pasta '{pasta_raiz}' não existe ou não é um diretório.")
        return resultados

    # os.walk percorre a pasta e TODAS as subpastas automaticamente
    for pasta_atual, subpastas, arquivos in os.walk(pasta_raiz):
        for nome_arquivo in arquivos:
            caminho_completo = os.path.join(pasta_atual, nome_arquivo)

            for termo in termos_busca:
                # Comparação sem diferenciar maiúsculas/minúsculas
                if termo.lower() in nome_arquivo.lower():
                    try:
                        data_modificacao = os.path.getmtime(caminho_completo)
                    except OSError:
                        # Arquivo pode ter sido removido/bloqueado durante a leitura
                        continue

                    atual = resultados[termo]
                    # Se ainda não há arquivo salvo para esse termo, ou se o
                    # arquivo atual é mais recente que o salvo, atualiza
                    if atual is None or data_modificacao > atual[1]:
                        resultados[termo] = (caminho_completo, data_modificacao)

    return resultados


def exibir_resultados(resultados):
    print("\n" + "=" * 60)
    print("RESULTADO DA BUSCA")
    print("=" * 60)

    for termo, info in resultados.items():
        print(f"\nTermo: '{termo}'")
        if info is None:
            print("  -> Nenhum arquivo encontrado.")
        else:
            caminho, timestamp = info
            data_formatada = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S")
            print(f"  -> Arquivo mais recente: {caminho}")
            print(f"  -> Última modificação:   {data_formatada}")

    print("\n" + "=" * 60)


def copiar_arquivos(resultados, pasta_destino):
    """
    Copia os arquivos encontrados em 'resultados' para a pasta_destino.
    Se o nome do arquivo já existir no destino, adiciona um sufixo numérico
    para não sobrescrever.

    :param resultados: dicionário retornado por buscar_arquivos_recentes
    :param pasta_destino: caminho da pasta onde os arquivos serão copiados
    """
    # Cria a pasta de destino se ela não existir
    os.makedirs(pasta_destino, exist_ok=True)

    print("\n" + "=" * 60)
    print("COPIANDO ARQUIVOS")
    print("=" * 60)

    for termo, info in resultados.items():
        if info is None:
            print(f"\nTermo: '{termo}' -> nenhum arquivo para copiar.")
            continue

        caminho_origem, _ = info
        nome_arquivo = os.path.basename(caminho_origem)
        caminho_destino = os.path.join(pasta_destino, nome_arquivo)

        # Evita sobrescrever arquivos com o mesmo nome no destino
        contador = 1
        nome_base, extensao = os.path.splitext(nome_arquivo)
        while os.path.exists(caminho_destino):
            caminho_destino = os.path.join(pasta_destino, f"{nome_base} ({contador}){extensao}")
            contador += 1

        try:
            shutil.copy2(caminho_origem, caminho_destino)
            print(f"\nTermo: '{termo}'")
            print(f"  -> Copiado de: {caminho_origem}")
            print(f"  -> Copiado para: {caminho_destino}")
        except OSError as erro:
            print(f"\nTermo: '{termo}'")
            print(f"  -> Erro ao copiar '{caminho_origem}': {erro}")

    print("\n" + "=" * 60)


def main():
    print("=== Busca de arquivos mais recentes em pasta e subpastas ===\n")

    # Pastas padrão pré-configuradas
    pasta_padrao_busca = r"B:\TOPOGRAFIA - PLANEJAMENTO\UNIDADE MARACAÍ"
    pasta_padrao_destino = r"C:\Users\coa.115\Desktop\mapas"

    pasta = input(
        f"Pasta a ser analisada [Enter para usar: {pasta_padrao_busca}]: "
    ).strip().strip('"')
    if not pasta:
        pasta = pasta_padrao_busca

    entrada_arquivos = input(
        "Digite os nomes (ou partes dos nomes) dos arquivos, separados por ';': "
    ).strip()

    # Separa por ponto e vírgula e remove espaços em branco extras
    termos_busca = [termo.strip() for termo in entrada_arquivos.split(";") if termo.strip()]

    if not termos_busca:
        print("Nenhum termo de busca informado. Encerrando.")
        return

    resultados = buscar_arquivos_recentes(pasta, termos_busca)
    exibir_resultados(resultados)

    # Pergunta se o usuário quer copiar os arquivos encontrados
    resposta = input("\nDeseja copiar os arquivos encontrados para outra pasta? (s/n): ").strip().lower()
    if resposta == "s":
        pasta_destino = input(
            f"Pasta de destino [Enter para usar: {pasta_padrao_destino}]: "
        ).strip().strip('"')
        if not pasta_destino:
            pasta_destino = pasta_padrao_destino
        copiar_arquivos(resultados, pasta_destino)
    else:
        print("Nenhum arquivo foi copiado.")


if __name__ == "__main__":
    main()
