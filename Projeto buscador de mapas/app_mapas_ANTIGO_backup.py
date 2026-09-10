"""
Aplicativo: app_mapas.py

Interface gráfica simples (sem linha de comando) com duas funções:

1) Buscar e copiar arquivos mais recentes
   - Procura, em uma pasta e subpastas, arquivos cujo nome contenha os
     termos informados (separados por ";") e copia o mais recente de
     cada termo para uma pasta de destino.

2) Compactar em PDF e abrir no Chrome
   - Junta todas as imagens e PDFs de uma pasta em um único arquivo PDF
     e abre o resultado no Google Chrome.

Requisitos (instalar uma vez, no terminal / prompt de comando):
    pip install pypdf img2pdf

Para usar: dê dois cliques no arquivo (ou rode "python app_mapas.py").
Uma janela vai abrir - não é necessário usar o terminal.
"""

import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

try:
    import img2pdf
except ImportError:
    img2pdf = None

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    PdfReader = None
    PdfWriter = None


EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
EXTENSAO_PDF = ".pdf"

PASTA_PADRAO_BUSCA = r"B:\TOPOGRAFIA - PLANEJAMENTO\UNIDADE MARACAÍ"
PASTA_PADRAO_DESTINO = r"C:\Users\coa.115\Desktop\mapas"


# ---------------------------------------------------------------------------
# Lógica: buscar e copiar arquivos
# ---------------------------------------------------------------------------

def buscar_arquivos_recentes(pasta_raiz, termos_busca, log):
    resultados = {termo: None for termo in termos_busca}

    if not os.path.isdir(pasta_raiz):
        log(f"Erro: a pasta '{pasta_raiz}' não existe.")
        return resultados

    for pasta_atual, _subpastas, arquivos in os.walk(pasta_raiz):
        for nome_arquivo in arquivos:
            caminho_completo = os.path.join(pasta_atual, nome_arquivo)
            for termo in termos_busca:
                if termo.lower() in nome_arquivo.lower():
                    try:
                        data_modificacao = os.path.getmtime(caminho_completo)
                    except OSError:
                        continue
                    atual = resultados[termo]
                    if atual is None or data_modificacao > atual[1]:
                        resultados[termo] = (caminho_completo, data_modificacao)

    return resultados


def copiar_arquivos(resultados, pasta_destino, log):
    import shutil

    os.makedirs(pasta_destino, exist_ok=True)
    total_copiados = 0

    for termo, info in resultados.items():
        if info is None:
            log(f"'{termo}': nenhum arquivo encontrado.")
            continue

        caminho_origem, data_mod = info
        nome_arquivo = os.path.basename(caminho_origem)
        caminho_destino = os.path.join(pasta_destino, nome_arquivo)

        contador = 1
        nome_base, extensao = os.path.splitext(nome_arquivo)
        while os.path.exists(caminho_destino):
            caminho_destino = os.path.join(pasta_destino, f"{nome_base} ({contador}){extensao}")
            contador += 1

        try:
            shutil.copy2(caminho_origem, caminho_destino)
            data_fmt = datetime.fromtimestamp(data_mod).strftime("%d/%m/%Y %H:%M")
            log(f"'{termo}': copiado -> {nome_arquivo} (modificado em {data_fmt})")
            total_copiados += 1
        except OSError as erro:
            log(f"'{termo}': erro ao copiar - {erro}")

    log(f"\nConcluído: {total_copiados} arquivo(s) copiado(s) para {pasta_destino}")


# ---------------------------------------------------------------------------
# Lógica: compactar em PDF único e abrir no Chrome
# ---------------------------------------------------------------------------

def listar_arquivos_validos(pasta):
    arquivos = []
    for nome in sorted(os.listdir(pasta)):
        caminho = os.path.join(pasta, nome)
        if not os.path.isfile(caminho):
            continue
        extensao = os.path.splitext(nome)[1].lower()
        if extensao in EXTENSOES_IMAGEM or extensao == EXTENSAO_PDF:
            arquivos.append(caminho)
    return arquivos


def gerar_pdf_unico(arquivos, caminho_saida, log):
    writer = PdfWriter()

    for caminho in arquivos:
        extensao = os.path.splitext(caminho)[1].lower()

        if extensao in EXTENSOES_IMAGEM:
            try:
                pdf_bytes = img2pdf.convert(caminho)
            except Exception as erro:
                log(f"Aviso: não converti '{os.path.basename(caminho)}': {erro}")
                continue

            caminho_temp = caminho + ".temp_convert.pdf"
            with open(caminho_temp, "wb") as f:
                f.write(pdf_bytes)

            reader = PdfReader(caminho_temp)
            for pagina in reader.pages:
                writer.add_page(pagina)

            os.remove(caminho_temp)
            log(f"Imagem adicionada: {os.path.basename(caminho)}")

        elif extensao == EXTENSAO_PDF:
            try:
                reader = PdfReader(caminho)
            except Exception as erro:
                log(f"Aviso: não li o PDF '{os.path.basename(caminho)}': {erro}")
                continue
            for pagina in reader.pages:
                writer.add_page(pagina)
            log(f"PDF adicionado: {os.path.basename(caminho)}")

    if len(writer.pages) == 0:
        log("Nenhuma página foi gerada.")
        return False

    with open(caminho_saida, "wb") as f:
        writer.write(f)

    return True


def abrir_no_chrome(caminho_pdf, log):
    caminhos_possiveis = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    chrome_exe = next((c for c in caminhos_possiveis if os.path.isfile(c)), None)

    if chrome_exe is None:
        log("Google Chrome não encontrado nos caminhos padrão.")
        log(f"Abra manualmente: {caminho_pdf}")
        return

    try:
        subprocess.Popen([chrome_exe, caminho_pdf])
        log(f"Aberto no Google Chrome: {caminho_pdf}")
    except OSError as erro:
        log(f"Erro ao abrir o Chrome: {erro}")


# ---------------------------------------------------------------------------
# Interface gráfica
# ---------------------------------------------------------------------------

class AppMapas(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Ferramenta de Mapas")
        self.geometry("640x600")
        self.resizable(False, False)

        estilo = ttk.Style(self)
        try:
            estilo.theme_use("vista")
        except tk.TclError:
            pass
        estilo.configure("TButton", padding=8, font=("Segoe UI", 10))
        estilo.configure("TLabel", font=("Segoe UI", 10))
        estilo.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))

        self._montar_secao_busca()
        self._montar_secao_pdf()
        self._montar_log()

    # -- Seção 1: buscar e copiar -----------------------------------------
    def _montar_secao_busca(self):
        frame = ttk.LabelFrame(self, text="1) Buscar e copiar arquivos mais recentes", padding=12)
        frame.pack(fill="x", padx=12, pady=(12, 6))

        ttk.Label(frame, text="Pasta onde procurar:").grid(row=0, column=0, sticky="w", pady=4)
        self.entrada_pasta_busca = ttk.Entry(frame, width=55)
        self.entrada_pasta_busca.insert(0, PASTA_PADRAO_BUSCA)
        self.entrada_pasta_busca.grid(row=0, column=1, padx=6)
        ttk.Button(frame, text="Procurar...", command=self._escolher_pasta_busca).grid(row=0, column=2)

        ttk.Label(frame, text="Nomes dos arquivos (separados por ;):").grid(row=1, column=0, sticky="w", pady=4)
        self.entrada_termos = ttk.Entry(frame, width=55)
        self.entrada_termos.insert(0, "relatorio; planilha; contrato")
        self.entrada_termos.grid(row=1, column=1, padx=6, columnspan=2, sticky="w")

        ttk.Label(frame, text="Copiar para a pasta:").grid(row=2, column=0, sticky="w", pady=4)
        self.entrada_pasta_destino = ttk.Entry(frame, width=55)
        self.entrada_pasta_destino.insert(0, PASTA_PADRAO_DESTINO)
        self.entrada_pasta_destino.grid(row=2, column=1, padx=6)
        ttk.Button(frame, text="Procurar...", command=self._escolher_pasta_destino).grid(row=2, column=2)

        self.botao_buscar = ttk.Button(frame, text="Buscar e Copiar Arquivos", command=self._executar_busca)
        self.botao_buscar.grid(row=3, column=0, columnspan=3, pady=(10, 0), sticky="ew")

    def _escolher_pasta_busca(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta onde procurar")
        if pasta:
            self.entrada_pasta_busca.delete(0, tk.END)
            self.entrada_pasta_busca.insert(0, pasta)

    def _escolher_pasta_destino(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta de destino")
        if pasta:
            self.entrada_pasta_destino.delete(0, tk.END)
            self.entrada_pasta_destino.insert(0, pasta)

    def _executar_busca(self):
        pasta = self.entrada_pasta_busca.get().strip()
        termos_texto = self.entrada_termos.get().strip()
        pasta_destino = self.entrada_pasta_destino.get().strip()

        termos = [t.strip() for t in termos_texto.split(";") if t.strip()]
        if not pasta or not termos or not pasta_destino:
            messagebox.showwarning("Campos incompletos", "Preencha a pasta de busca, os termos e a pasta de destino.")
            return

        self.botao_buscar.config(state="disabled")
        self._log("\n--- Iniciando busca ---")

        def tarefa():
            resultados = buscar_arquivos_recentes(pasta, termos, self._log)
            copiar_arquivos(resultados, pasta_destino, self._log)
            self.botao_buscar.config(state="normal")

        threading.Thread(target=tarefa, daemon=True).start()

    # -- Seção 2: compactar em PDF e abrir no Chrome ------------------------
    def _montar_secao_pdf(self):
        frame = ttk.LabelFrame(self, text="2) Compactar arquivos em um único PDF", padding=12)
        frame.pack(fill="x", padx=12, pady=6)

        ttk.Label(frame, text="Pasta com os arquivos:").grid(row=0, column=0, sticky="w", pady=4)
        self.entrada_pasta_pdf = ttk.Entry(frame, width=55)
        self.entrada_pasta_pdf.insert(0, PASTA_PADRAO_DESTINO)
        self.entrada_pasta_pdf.grid(row=0, column=1, padx=6)
        ttk.Button(frame, text="Procurar...", command=self._escolher_pasta_pdf).grid(row=0, column=2)

        self.botao_pdf = ttk.Button(frame, text="Gerar PDF e Abrir no Chrome", command=self._executar_pdf)
        self.botao_pdf.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky="ew")

    def _escolher_pasta_pdf(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta com os arquivos")
        if pasta:
            self.entrada_pasta_pdf.delete(0, tk.END)
            self.entrada_pasta_pdf.insert(0, pasta)

    def _executar_pdf(self):
        if img2pdf is None or PdfReader is None:
            messagebox.showerror(
                "Bibliotecas faltando",
                "Instale as bibliotecas necessárias abrindo o Prompt de Comando e digitando:\n\n"
                "pip install pypdf img2pdf",
            )
            return

        pasta = self.entrada_pasta_pdf.get().strip()
        if not pasta or not os.path.isdir(pasta):
            messagebox.showwarning("Pasta inválida", "Selecione uma pasta válida.")
            return

        self.botao_pdf.config(state="disabled")
        self._log("\n--- Gerando PDF único ---")

        def tarefa():
            arquivos = listar_arquivos_validos(pasta)
            if not arquivos:
                self._log("Nenhum arquivo de imagem ou PDF encontrado nessa pasta.")
                self.botao_pdf.config(state="normal")
                return

            nome_saida = f"mapas_compilados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            caminho_saida = os.path.join(pasta, nome_saida)

            sucesso = gerar_pdf_unico(arquivos, caminho_saida, self._log)
            if sucesso:
                self._log(f"PDF gerado: {caminho_saida}")
                abrir_no_chrome(caminho_saida, self._log)

            self.botao_pdf.config(state="normal")

        threading.Thread(target=tarefa, daemon=True).start()

    # -- Log ------------------------------------------------------------
    def _montar_log(self):
        frame = ttk.LabelFrame(self, text="Andamento", padding=8)
        frame.pack(fill="both", expand=True, padx=12, pady=(6, 12))

        self.texto_log = tk.Text(frame, height=14, wrap="word", state="disabled",
                                   font=("Consolas", 9), bg="#f5f5f5")
        self.texto_log.pack(side="left", fill="both", expand=True)

        barra = ttk.Scrollbar(frame, command=self.texto_log.yview)
        barra.pack(side="right", fill="y")
        self.texto_log.config(yscrollcommand=barra.set)

    def _log(self, mensagem):
        def escrever():
            self.texto_log.config(state="normal")
            self.texto_log.insert(tk.END, mensagem + "\n")
            self.texto_log.see(tk.END)
            self.texto_log.config(state="disabled")
        self.after(0, escrever)


if __name__ == "__main__":
    app = AppMapas()
    app.mainloop()
