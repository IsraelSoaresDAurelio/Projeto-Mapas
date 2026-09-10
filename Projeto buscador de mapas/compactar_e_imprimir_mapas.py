"""
Script: compactar_e_imprimir_mapas.py

Pega todos os arquivos de uma pasta (imagens e/ou PDFs), junta tudo em um
único arquivo PDF (na ordem alfabética dos nomes) e envia esse PDF para
impressão usando a impressora padrão do Windows.

Requisitos (instalar uma vez, se ainda não tiver):
    pip install pypdf img2pdf

Uso:
    python compactar_e_imprimir_mapas.py

Por padrão, ele usa:
    Pasta de origem: C:\\Users\\coa.115\\Desktop\\mapas
    PDF final salvo em: C:\\Users\\coa.115\\Desktop\\mapas\\mapas_compilados.pdf

Formatos de imagem aceitos: .jpg, .jpeg, .png, .bmp, .tif, .tiff
PDFs existentes na pasta também são incluídos (mesclados) no arquivo final.
"""

import os
import sys
import subprocess
from datetime import datetime

try:
    import img2pdf
except ImportError:
    print("A biblioteca 'img2pdf' não está instalada. Rode: pip install img2pdf")
    sys.exit(1)

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("A biblioteca 'pypdf' não está instalada. Rode: pip install pypdf")
    sys.exit(1)


EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
EXTENSAO_PDF = ".pdf"


def listar_arquivos_validos(pasta):
    """
    Retorna a lista de arquivos (imagens e PDFs) dentro da pasta,
    em ordem alfabética. Não entra em subpastas.
    """
    arquivos = []
    for nome in sorted(os.listdir(pasta)):
        caminho = os.path.join(pasta, nome)
        if not os.path.isfile(caminho):
            continue
        # Evita que PDFs compilados em execuções anteriores sejam inseridos
        # novamente no próximo arquivo final.
        if nome.lower().startswith("mapas_compilados_"):
            continue
        extensao = os.path.splitext(nome)[1].lower()
        if extensao in EXTENSOES_IMAGEM or extensao == EXTENSAO_PDF:
            arquivos.append(caminho)
    return arquivos


def gerar_pdf_unico(arquivos, caminho_saida):
    """
    Converte imagens em páginas de PDF e mescla com PDFs existentes,
    gerando um único arquivo PDF final em caminho_saida.
    """
    writer = PdfWriter()

    for caminho in arquivos:
        extensao = os.path.splitext(caminho)[1].lower()

        if extensao in EXTENSOES_IMAGEM:
            # Converte a imagem em um PDF temporário de 1 página, em memória
            try:
                pdf_bytes = img2pdf.convert(caminho)
            except Exception as erro:
                print(f"  -> Aviso: não foi possível converter '{caminho}': {erro}")
                continue

            caminho_temp = caminho + ".temp_convert.pdf"
            with open(caminho_temp, "wb") as f:
                f.write(pdf_bytes)

            reader = PdfReader(caminho_temp)
            for pagina in reader.pages:
                writer.add_page(pagina)

            os.remove(caminho_temp)
            print(f"  -> Imagem adicionada: {caminho}")

        elif extensao == EXTENSAO_PDF:
            try:
                reader = PdfReader(caminho)
            except Exception as erro:
                print(f"  -> Aviso: não foi possível ler o PDF '{caminho}': {erro}")
                continue

            for pagina in reader.pages:
                writer.add_page(pagina)
            print(f"  -> PDF adicionado: {caminho}")

    if len(writer.pages) == 0:
        print("Nenhuma página foi gerada. Verifique se a pasta contém imagens ou PDFs válidos.")
        return False

    with open(caminho_saida, "wb") as f:
        writer.write(f)

    return True


def imprimir_pdf(caminho_pdf):
    """
    Envia o PDF para a impressora padrão do Windows.
    Usa o comando 'print' associado ao aplicativo padrão de PDF
    (equivalente a clicar com botão direito -> Imprimir).
    """
    try:
        os.startfile(caminho_pdf, "print")
        print(f"\nComando de impressão enviado para: {caminho_pdf}")
        print("Verifique a fila de impressão / a impressora padrão do Windows.")
    except AttributeError:
        print("Erro: este comando de impressão automática só funciona no Windows.")
    except OSError as erro:
        print(f"Erro ao tentar imprimir: {erro}")
        print("Você pode abrir o arquivo manualmente e imprimir com Ctrl+P.")


def main():
    print("=== Compactar arquivos em PDF único e imprimir ===\n")

    pasta_padrao = r"C:\Users\coa.115\Desktop\mapas"
    pasta = input(f"Pasta com os arquivos [Enter para usar: {pasta_padrao}]: ").strip().strip('"')
    if not pasta:
        pasta = pasta_padrao

    if not os.path.isdir(pasta):
        print(f"Erro: a pasta '{pasta}' não existe.")
        return

    arquivos = listar_arquivos_validos(pasta)
    if not arquivos:
        print("Nenhum arquivo de imagem ou PDF encontrado nessa pasta.")
        return

    print(f"\n{len(arquivos)} arquivo(s) encontrado(s). Gerando PDF único...\n")

    nome_saida = f"mapas_compilados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    caminho_saida = os.path.join(pasta, nome_saida)

    sucesso = gerar_pdf_unico(arquivos, caminho_saida)
    if not sucesso:
        return

    print(f"\nPDF único gerado com sucesso: {caminho_saida}")

    resposta = input("\nDeseja enviar esse PDF para impressão agora? (s/n): ").strip().lower()
    if resposta == "s":
        imprimir_pdf(caminho_saida)
    else:
        print("Impressão não enviada. O PDF ficou salvo na pasta.")


if __name__ == "__main__":
    main()
