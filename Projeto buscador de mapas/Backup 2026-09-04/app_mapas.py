"""
Aplicativo: app_mapas.py
Central de Mapas — organizar, localizar e compilar mapas em PDF.

Interface gráfica em customtkinter, dividida em dois passos:

    1) Buscar mapas
       - Procura, em uma pasta e subpastas, arquivos cujo nome contenha os
         termos informados e mostra o mais recente de cada termo.
       - Copia os arquivos encontrados para uma pasta de destino.

    2) Gerar PDF e imprimir
       - Junta todas as imagens e PDFs de uma pasta em um único arquivo
         PDF (na ordem alfabética), abre no navegador e permite imprimir.

Requisitos (instalar uma vez, no terminal / prompt de comando):
    pip install customtkinter pypdf img2pdf

Para usar: dê dois cliques em "Abrir Central de Mapas.pyw"
(ou rode "python app_mapas.py"). Uma janela vai abrir - não é necessário
usar o terminal.
"""

import os
import re
import shutil
import subprocess
import sys
import threading
from datetime import datetime

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    import customtkinter as ctk
except ImportError:  # pragma: no cover - mensagem amigável se faltar instalar
    raise SystemExit(
        "A biblioteca 'customtkinter' não está instalada.\n"
        "Abra o Prompt de Comando e rode: pip install customtkinter"
    )

try:
    import img2pdf
except ImportError:
    img2pdf = None

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    PdfReader = None
    PdfWriter = None

try:  # deixa a janela nítida em monitores com escala alta (Windows)
    from ctypes import windll

    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


def caminho_recurso(nome_arquivo):
    """
    Resolve o caminho de um arquivo que acompanha o app (ex.: ícone),
    tanto rodando como script quanto já empacotado pelo PyInstaller.
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nome_arquivo)


# ---------------------------------------------------------------------------
# Configuração visual
# ---------------------------------------------------------------------------

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

COR_FUNDO = "#EEF2F7"
COR_CARTAO = "#FFFFFF"
COR_BORDA = "#DCE3EC"
COR_HEADER_DE = "#0C2340"
COR_HEADER_PARA = "#154270"
COR_DESTAQUE = "#3ED6A5"
COR_TEXTO_PRINCIPAL = "#10243E"
COR_TEXTO_SECUNDARIO = "#5B6B7F"
COR_TEXTO_CLARO = "#EAF0F8"
COR_VERDE = "#1E9E6B"
COR_VERDE_HOVER = "#187F55"
COR_NAVY_BOTAO = "#153A63"
COR_NAVY_BOTAO_HOVER = "#0F2A49"
COR_CINZA_BOTAO = "#E3E8F0"
COR_CINZA_BOTAO_HOVER = "#D2DAE6"
COR_PILL_INATIVO = "#2A4A70"
COR_STATUS_FUNDO = "#F4F7FB"
COR_PERIGO = "#C0392B"

FONTE_TAG = ("Segoe UI", 13, "bold")
FONTE_TITULO = ("Segoe UI", 29, "bold")
FONTE_SUBTITULO = ("Segoe UI", 14)
FONTE_LABEL = ("Segoe UI", 16, "bold")
FONTE_AJUDA = ("Segoe UI", 12)
FONTE_BASE = ("Segoe UI", 14)
FONTE_BOTAO = ("Segoe UI", 14, "bold")
FONTE_STATUS = ("Segoe UI", 12)
FONTE_PASSO = ("Segoe UI", 14, "bold")
FONTE_TABELA = ("Segoe UI", 12)
FONTE_TABELA_CABECALHO = ("Segoe UI", 12, "bold")

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
EXTENSAO_PDF = ".pdf"

PASTA_PADRAO_BUSCA = r"B:\TOPOGRAFIA - PLANEJAMENTO\UNIDADE MARACAÍ"
PASTA_PADRAO_DESTINO = r"C:\Users\coa.115\Desktop\mapas"

TEXTO_AJUDA = """PASSO 1 — BUSCAR MAPAS

1. Escolha a pasta onde os mapas ficam guardados.
   A busca entra automaticamente em todas as subpastas.

2. Digite os códigos das zonas que você precisa (ex.: 7467, 8227).
   Separe por ponto e vírgula ( ; ), vírgula ( , ) ou uma por linha.
   Se preferir, cole direto "zona 1 zona 2 zona 3" — nós separamos
   os códigos automaticamente para você.

3. Clique em "Buscar versões mais recentes".
   A tabela mostra a versão mais recente encontrada de cada código.

4. Escolha a pasta de destino e clique em "Salvar arquivos na pasta
   destino" para copiar os arquivos encontrados para lá.


PASSO 2 — GERAR PDF E IMPRIMIR

1. A pasta usada no passo 1 já aparece preenchida aqui automaticamente.

2. Clique em "Gerar PDF único" para juntar todas as imagens e PDFs
   dessa pasta em um único arquivo, em ordem alfabética.

3. Use "Abrir no navegador" para conferir o resultado antes de imprimir.

4. Use "Imprimir" para enviar o PDF direto para a impressora padrão
   do Windows.


MANTENDO A PASTA ORGANIZADA

Use o botão "Limpar pasta de destino" (no passo 1, logo abaixo da
pasta de destino) sempre que quiser apagar os arquivos já usados e
recomeçar do zero. O aplicativo sempre pede confirmação antes de
apagar qualquer coisa, então não há risco de perder arquivos sem querer.


DICA

Os botões verdes são a ação principal de cada passo. Os botões
escuros (azul-marinho) são ações complementares, e os botões claros
servem para escolher pastas ou atualizar listas."""


# ---------------------------------------------------------------------------
# Lógica: dividir termos digitados/colados
# ---------------------------------------------------------------------------

def dividir_termos(texto):
    """
    Transforma o texto colado pelo usuário em uma lista de termos de busca.

    Se o texto já tiver vírgula, ponto e vírgula ou quebra de linha, cada
    pedaço vira um termo. Caso contrário, tenta separar automaticamente
    sequências como "zona 1 zona 2 zona 3" em ["zona 1", "zona 2", "zona 3"].
    """
    texto = (texto or "").strip()
    if not texto:
        return []

    if re.search(r"[;,\n]", texto):
        partes = re.split(r"[;,\n]+", texto)
    else:
        partes = re.findall(r"[^\d\s][^\d]*?\d+|\S+", texto)

    vistos = []
    for parte in partes:
        termo = parte.strip()
        if termo and termo not in vistos:
            vistos.append(termo)
    return vistos


def formatar_termo_como_zona(termo):
    """
    Exibe o termo pesquisado com o prefixo "ZONA" (ex.: "7467" -> "ZONA 7467").
    Se o termo já mencionar "zona", mantém como está para não duplicar.
    """
    termo = (termo or "").strip()
    if not termo:
        return termo
    if "zona" in termo.lower():
        return termo.upper()
    return f"ZONA {termo}"


# ---------------------------------------------------------------------------
# Lógica: buscar e copiar arquivos
# ---------------------------------------------------------------------------

def buscar_arquivos_recentes(pasta_raiz, termos_busca, log=None):
    resultados = {termo: None for termo in termos_busca}

    if not os.path.isdir(pasta_raiz):
        if log:
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

    log(f"Concluído: {total_copiados} arquivo(s) copiado(s) para {pasta_destino}")
    return total_copiados


def contar_arquivos_da_pasta(pasta):
    """Conta apenas os arquivos soltos direto na pasta (não entra em subpastas)."""
    if not os.path.isdir(pasta):
        return 0
    return sum(1 for nome in os.listdir(pasta) if os.path.isfile(os.path.join(pasta, nome)))


def limpar_pasta(pasta, log):
    """
    Apaga os arquivos soltos direto dentro de 'pasta' (não mexe em subpastas).
    Usado pelo botão "Limpar pasta de destino" para manter a pasta organizada.
    """
    if not os.path.isdir(pasta):
        log(f"Pasta '{pasta}' não encontrada.")
        return 0

    removidos = 0
    for nome in os.listdir(pasta):
        caminho = os.path.join(pasta, nome)
        if not os.path.isfile(caminho):
            continue
        try:
            os.remove(caminho)
            removidos += 1
        except OSError as erro:
            log(f"Não foi possível remover '{nome}': {erro}")

    log(f"{removidos} arquivo(s) removido(s) de {pasta}")
    return removidos


# ---------------------------------------------------------------------------
# Lógica: compactar em PDF único, abrir e imprimir
# ---------------------------------------------------------------------------

def listar_arquivos_validos(pasta):
    arquivos = []
    if not os.path.isdir(pasta):
        return arquivos
    for nome in sorted(os.listdir(pasta)):
        caminho = os.path.join(pasta, nome)
        if not os.path.isfile(caminho):
            continue
        if nome.lower().startswith("mapas_compilados_"):
            continue
        extensao = os.path.splitext(nome)[1].lower()
        if extensao in EXTENSOES_IMAGEM or extensao == EXTENSAO_PDF:
            arquivos.append(caminho)
    return arquivos


def gerar_pdf_unico(arquivos, caminho_saida, log):
    if img2pdf is None or PdfReader is None or PdfWriter is None:
        log("Bibliotecas 'pypdf' e/ou 'img2pdf' não instaladas.")
        return False

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
            with open(caminho_temp, "wb") as arquivo_temp:
                arquivo_temp.write(pdf_bytes)

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

    with open(caminho_saida, "wb") as arquivo_saida:
        writer.write(arquivo_saida)

    return True


def abrir_no_chrome(caminho_pdf, log):
    caminhos_possiveis = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    chrome_exe = next((c for c in caminhos_possiveis if os.path.isfile(c)), None)

    if chrome_exe is None:
        log("Google Chrome não encontrado. Abrindo com o programa padrão do Windows.")
        try:
            os.startfile(caminho_pdf)
        except OSError as erro:
            log(f"Não foi possível abrir o arquivo: {erro}")
        return

    try:
        subprocess.Popen([chrome_exe, caminho_pdf])
        log(f"Aberto no Google Chrome: {caminho_pdf}")
    except OSError as erro:
        log(f"Erro ao abrir o Chrome: {erro}")


def imprimir_pdf(caminho_pdf, log):
    if not caminho_pdf or not os.path.isfile(caminho_pdf):
        log("Gere o PDF antes de enviar para impressão.")
        return
    try:
        os.startfile(caminho_pdf, "print")
        log("Comando de impressão enviado. Verifique a fila de impressão do Windows.")
    except AttributeError:
        log("A impressão automática só funciona no Windows.")
    except OSError as erro:
        log(f"Erro ao tentar imprimir: {erro}")


# ---------------------------------------------------------------------------
# Widgets reutilizáveis
# ---------------------------------------------------------------------------

class Cartao(ctk.CTkFrame):
    """Cartão branco com cantos arredondados e borda sutil."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COR_CARTAO,
            corner_radius=16,
            border_width=1,
            border_color=COR_BORDA,
            **kwargs,
        )


class CampoDePasta(ctk.CTkFrame):
    """Título + descrição + campo de texto + botão 'Selecionar pasta'."""

    def __init__(self, master, titulo, descricao="", valor_inicial="", ao_mudar=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._ao_mudar = ao_mudar

        ctk.CTkLabel(
            self, text=titulo, font=FONTE_LABEL, text_color=COR_TEXTO_PRINCIPAL, anchor="w"
        ).grid(row=0, column=0, columnspan=2, sticky="ew")

        if descricao:
            _rotulo_com_quebra_automatica(
                self, descricao, FONTE_AJUDA, COR_TEXTO_SECUNDARIO,
            ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 8))

        self.variavel = tk.StringVar(value=valor_inicial)
        self.entrada = ctk.CTkEntry(
            self, textvariable=self.variavel, height=46, font=FONTE_BASE,
            corner_radius=9, border_color=COR_BORDA, fg_color="#FBFCFE",
        )
        self.entrada.grid(row=2, column=0, sticky="ew", padx=(0, 10))

        self.botao = ctk.CTkButton(
            self, text="Selecionar pasta", width=176, height=46, corner_radius=9,
            fg_color=COR_CINZA_BOTAO, hover_color=COR_CINZA_BOTAO_HOVER,
            text_color=COR_TEXTO_PRINCIPAL, font=FONTE_BOTAO, command=self._selecionar,
        )
        self.botao.grid(row=2, column=1)

    def _selecionar(self):
        pasta = filedialog.askdirectory(title="Selecione uma pasta")
        if pasta:
            self.set(pasta)

    def get(self):
        return self.variavel.get().strip()

    def set(self, valor):
        self.variavel.set(valor)
        if self._ao_mudar:
            self._ao_mudar(valor)


# Largura de quebra de texto pensada para caber até no tamanho mínimo da
# janela (minsize). Um valor fixo é mais previsível e seguro do que amarrar
# o wraplength ao evento <Configure>, que nos widgets do customtkinter pode
# entrar num laço de eventos (o próprio ajuste dispara um novo <Configure>).
LARGURA_QUEBRA_TEXTO = 760


def _rotulo_com_quebra_automatica(master, text, font, text_color, **kwargs):
    """Cria um CTkLabel com quebra de linha automática em várias linhas."""
    return ctk.CTkLabel(
        master, text=text, font=font, text_color=text_color,
        anchor="w", justify="left", wraplength=LARGURA_QUEBRA_TEXTO, **kwargs,
    )


def _criar_tabela(master, colunas, larguras):
    """Cria um ttk.Treeview estilizado dentro de 'master', com scrollbar."""
    estilo = ttk.Style(master)
    try:
        estilo.theme_use("clam")
    except tk.TclError:
        pass
    estilo.configure(
        "Mapas.Treeview",
        background="#FFFFFF",
        fieldbackground="#FFFFFF",
        foreground=COR_TEXTO_PRINCIPAL,
        rowheight=38,
        borderwidth=0,
        font=FONTE_TABELA,
    )
    estilo.configure(
        "Mapas.Treeview.Heading",
        background=COR_HEADER_DE,
        foreground="white",
        font=FONTE_TABELA_CABECALHO,
        borderwidth=0,
        relief="flat",
    )
    estilo.map(
        "Mapas.Treeview.Heading",
        background=[("active", COR_HEADER_DE)],
    )
    estilo.map(
        "Mapas.Treeview",
        background=[("selected", "#DCEEE6")],
        foreground=[("selected", COR_TEXTO_PRINCIPAL)],
    )

    envoltorio = ctk.CTkFrame(master, fg_color="transparent")
    envoltorio.grid_rowconfigure(0, weight=1)
    envoltorio.grid_columnconfigure(0, weight=1)

    tabela = ttk.Treeview(
        envoltorio, columns=colunas, show="headings", style="Mapas.Treeview", selectmode="browse"
    )
    for coluna, largura in zip(colunas, larguras):
        tabela.heading(coluna, text=coluna)
        tabela.column(coluna, width=largura, anchor="w", stretch=True)

    barra = ttk.Scrollbar(envoltorio, orient="vertical", command=tabela.yview)
    tabela.configure(yscrollcommand=barra.set)

    tabela.grid(row=0, column=0, sticky="nsew")
    barra.grid(row=0, column=1, sticky="ns")

    return envoltorio, tabela


# ---------------------------------------------------------------------------
# Passo 1: Buscar mapas
# ---------------------------------------------------------------------------

class PassoBuscar(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.ultimos_resultados = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # -- Cartão 1: onde procurar / o que procurar -----------------------
        cartao_busca = Cartao(self)
        cartao_busca.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        cartao_busca.grid_columnconfigure(0, weight=1)
        cartao_busca.grid_columnconfigure(1, weight=1)

        interno = ctk.CTkFrame(cartao_busca, fg_color="transparent")
        interno.grid(row=0, column=0, columnspan=2, sticky="ew", padx=28, pady=28)
        interno.grid_columnconfigure(0, weight=1)

        self.campo_pasta_busca = CampoDePasta(
            interno,
            "Onde estão os mapas?",
            "A busca inclui todas as subpastas.",
            valor_inicial=PASTA_PADRAO_BUSCA,
        )
        self.campo_pasta_busca.grid(row=0, column=0, sticky="ew", pady=(0, 22))

        ctk.CTkLabel(
            interno, text="Quais mapas você procura?", font=FONTE_LABEL,
            text_color=COR_TEXTO_PRINCIPAL, anchor="w",
        ).grid(row=1, column=0, sticky="ew")
        _rotulo_com_quebra_automatica(
            interno,
            "Separe os códigos por ponto e vírgula ( ; ), vírgula ( , ) ou um em cada linha. "
            'Sem separador, tentamos identificar automaticamente sequências como "zona 1 zona 2 zona 3".',
            FONTE_AJUDA, COR_TEXTO_SECUNDARIO,
        ).grid(row=2, column=0, sticky="ew", pady=(4, 10))

        self.entrada_termos = ctk.CTkEntry(
            interno, height=46, font=FONTE_BASE, corner_radius=9,
            border_color=COR_BORDA, fg_color="#FBFCFE",
            placeholder_text="ex.: zona 1 zona 2 zona 3",
        )
        self.entrada_termos.grid(row=3, column=0, sticky="ew", pady=(0, 22))

        linha_botoes = ctk.CTkFrame(interno, fg_color="transparent")
        linha_botoes.grid(row=4, column=0, sticky="ew")
        linha_botoes.grid_columnconfigure(0, weight=1)
        linha_botoes.grid_columnconfigure(1, weight=1)

        self.botao_buscar = ctk.CTkButton(
            linha_botoes, text="Buscar versões mais recentes", height=48, corner_radius=9,
            fg_color=COR_VERDE, hover_color=COR_VERDE_HOVER, font=FONTE_BOTAO,
            command=self.executar_busca,
        )
        self.botao_buscar.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.botao_salvar = ctk.CTkButton(
            linha_botoes, text="Salvar arquivos na pasta destino", height=48, corner_radius=9,
            fg_color=COR_NAVY_BOTAO, hover_color=COR_NAVY_BOTAO_HOVER, font=FONTE_BOTAO,
            command=self.executar_copia,
        )
        self.botao_salvar.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.aviso_var = tk.StringVar(value="Informe os códigos e faça a busca para confirmar os arquivos encontrados.")
        ctk.CTkLabel(
            interno, textvariable=self.aviso_var, font=FONTE_AJUDA, text_color=COR_TEXTO_SECUNDARIO,
            anchor="w", fg_color=COR_STATUS_FUNDO, corner_radius=8, height=36,
        ).grid(row=5, column=0, sticky="ew", pady=(16, 0), ipady=6)

        # -- Cartão 2: para onde copiar --------------------------------------
        cartao_destino = Cartao(self)
        cartao_destino.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        cartao_destino.grid_columnconfigure(0, weight=1)

        interno_destino = ctk.CTkFrame(cartao_destino, fg_color="transparent")
        interno_destino.grid(row=0, column=0, sticky="ew", padx=28, pady=28)
        interno_destino.grid_columnconfigure(0, weight=1)

        self.campo_pasta_destino = CampoDePasta(
            interno_destino,
            "Para onde deseja copiar?",
            "Os resultados encontrados serão reunidos nessa pasta.",
            valor_inicial=PASTA_PADRAO_DESTINO,
            ao_mudar=self.app.definir_pasta_pdf_padrao,
        )
        self.campo_pasta_destino.grid(row=0, column=0, sticky="ew")

        self.botao_limpar_destino = ctk.CTkButton(
            interno_destino, text="Limpar pasta de destino", height=38, corner_radius=9,
            fg_color="transparent", hover_color="#FBEAEA", border_width=1,
            border_color=COR_PERIGO, text_color=COR_PERIGO, font=FONTE_AJUDA,
            command=self.confirmar_limpar_pasta,
        )
        self.botao_limpar_destino.grid(row=1, column=0, sticky="w", pady=(16, 0))

        # -- Cartão 3: resultado da busca -------------------------------------
        cartao_resultado = Cartao(self)
        cartao_resultado.grid(row=2, column=0, sticky="nsew")
        cartao_resultado.grid_columnconfigure(0, weight=1)
        cartao_resultado.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            cartao_resultado, text="Resultado da busca", font=FONTE_LABEL,
            text_color=COR_TEXTO_PRINCIPAL, anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 12))

        envoltorio_tabela, self.tabela = _criar_tabela(
            cartao_resultado,
            colunas=("Termo", "Última modificação"),
            larguras=(300, 200),
        )
        envoltorio_tabela.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 28))

    # -- ações -------------------------------------------------------------
    def _definir_aviso(self, texto):
        self.after(0, lambda: self.aviso_var.set(texto))

    def executar_busca(self):
        pasta = self.campo_pasta_busca.get()
        termos = dividir_termos(self.entrada_termos.get())

        if not pasta:
            messagebox.showwarning("Campo obrigatório", "Informe a pasta onde os mapas estão.")
            return
        if not termos:
            messagebox.showwarning("Campo obrigatório", "Informe ao menos um mapa para buscar.")
            return

        self.botao_buscar.configure(state="disabled", text="Buscando...")
        self._definir_aviso(f"Buscando {len(termos)} código(s) em '{pasta}'...")
        self.app.definir_status(f"Buscando em: {pasta}")

        def tarefa():
            resultados = buscar_arquivos_recentes(pasta, termos, log=self.app.definir_status)
            self.ultimos_resultados = resultados
            self.after(0, lambda: self._preencher_tabela(resultados))

        threading.Thread(target=tarefa, daemon=True).start()

    def _preencher_tabela(self, resultados):
        for linha in self.tabela.get_children():
            self.tabela.delete(linha)

        encontrados = 0
        for termo, info in resultados.items():
            rotulo_termo = formatar_termo_como_zona(termo)
            if info is None:
                self.tabela.insert("", "end", values=(rotulo_termo, "Não encontrado"))
                continue
            _caminho, data_mod = info
            data_fmt = datetime.fromtimestamp(data_mod).strftime("%d/%m/%Y %H:%M")
            self.tabela.insert("", "end", values=(rotulo_termo, data_fmt))
            encontrados += 1

        total = len(resultados)
        self._definir_aviso(f"{encontrados} de {total} código(s) encontrado(s). Confira a tabela abaixo.")
        self.app.definir_status("Busca concluída.")
        self.botao_buscar.configure(state="normal", text="Buscar versões mais recentes")

    def executar_copia(self):
        if not self.ultimos_resultados:
            messagebox.showinfo("Nada para copiar", "Faça uma busca antes de salvar os arquivos.")
            return

        pasta_destino = self.campo_pasta_destino.get()
        if not pasta_destino:
            messagebox.showwarning("Campo obrigatório", "Informe a pasta de destino.")
            return

        self.botao_salvar.configure(state="disabled", text="Salvando...")
        self._definir_aviso("Copiando arquivos encontrados...")

        def tarefa():
            total = copiar_arquivos(self.ultimos_resultados, pasta_destino, log=self.app.definir_status)
            mensagem = f"{total} arquivo(s) copiado(s) para '{pasta_destino}'."
            self._definir_aviso(mensagem)
            self.app.definir_status(mensagem)
            self.after(0, lambda: self.botao_salvar.configure(state="normal", text="Salvar arquivos na pasta destino"))

        threading.Thread(target=tarefa, daemon=True).start()

    def confirmar_limpar_pasta(self):
        pasta = self.campo_pasta_destino.get()
        if not pasta or not os.path.isdir(pasta):
            messagebox.showinfo("Pasta não encontrada", "Selecione uma pasta de destino válida.")
            return

        total = contar_arquivos_da_pasta(pasta)
        if total == 0:
            messagebox.showinfo("Pasta já está vazia", "Não há arquivos para remover nessa pasta.")
            return

        confirmar = messagebox.askyesno(
            "Limpar pasta de destino",
            f"Isso vai apagar definitivamente {total} arquivo(s) em:\n{pasta}\n\n"
            "Essa ação não pode ser desfeita. Deseja continuar?",
            icon="warning",
        )
        if not confirmar:
            return

        removidos = limpar_pasta(pasta, log=self.app.definir_status)
        self._definir_aviso(f"{removidos} arquivo(s) removido(s) da pasta de destino.")
        self.app.definir_status(f"{removidos} arquivo(s) removido(s) de '{pasta}'.")
        self.app.passo_pdf.atualizar_lista()


# ---------------------------------------------------------------------------
# Passo 2: Gerar PDF e imprimir
# ---------------------------------------------------------------------------

class PassoPdf(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.ultimo_pdf_gerado = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        cartao_pasta = Cartao(self)
        cartao_pasta.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        cartao_pasta.grid_columnconfigure(0, weight=1)

        interno = ctk.CTkFrame(cartao_pasta, fg_color="transparent")
        interno.grid(row=0, column=0, sticky="ew", padx=28, pady=28)
        interno.grid_columnconfigure(0, weight=1)

        self.campo_pasta_pdf = CampoDePasta(
            interno,
            "De onde vêm os arquivos?",
            "A pasta usada no passo anterior já vem preenchida aqui. Imagens e PDFs serão juntados em ordem alfabética.",
            valor_inicial=PASTA_PADRAO_DESTINO,
        )
        self.campo_pasta_pdf.grid(row=0, column=0, sticky="ew", pady=(0, 22))

        linha_botoes = ctk.CTkFrame(interno, fg_color="transparent")
        linha_botoes.grid(row=1, column=0, sticky="ew")
        linha_botoes.grid_columnconfigure(0, weight=1)
        linha_botoes.grid_columnconfigure(1, weight=1)
        linha_botoes.grid_columnconfigure(2, weight=1)

        self.botao_gerar = ctk.CTkButton(
            linha_botoes, text="Gerar PDF único", height=48, corner_radius=9,
            fg_color=COR_VERDE, hover_color=COR_VERDE_HOVER, font=FONTE_BOTAO,
            command=self.executar_gerar_pdf,
        )
        self.botao_gerar.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.botao_abrir = ctk.CTkButton(
            linha_botoes, text="Abrir no navegador", height=48, corner_radius=9,
            fg_color=COR_NAVY_BOTAO, hover_color=COR_NAVY_BOTAO_HOVER, font=FONTE_BOTAO,
            command=self.executar_abrir, state="disabled",
        )
        self.botao_abrir.grid(row=0, column=1, sticky="ew", padx=8)

        self.botao_imprimir = ctk.CTkButton(
            linha_botoes, text="Imprimir", height=48, corner_radius=9,
            fg_color=COR_CINZA_BOTAO, hover_color=COR_CINZA_BOTAO_HOVER,
            text_color=COR_TEXTO_PRINCIPAL, font=FONTE_BOTAO,
            command=self.executar_imprimir, state="disabled",
        )
        self.botao_imprimir.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        self.aviso_var = tk.StringVar(value="Escolha a pasta e gere o PDF para revisar antes de imprimir.")
        ctk.CTkLabel(
            interno, textvariable=self.aviso_var, font=FONTE_AJUDA, text_color=COR_TEXTO_SECUNDARIO,
            anchor="w", fg_color=COR_STATUS_FUNDO, corner_radius=8, height=36,
        ).grid(row=2, column=0, sticky="ew", pady=(16, 0), ipady=6)

        cartao_lista = Cartao(self)
        cartao_lista.grid(row=1, column=0, sticky="nsew")
        cartao_lista.grid_columnconfigure(0, weight=1)
        cartao_lista.grid_rowconfigure(1, weight=1)

        cabecalho = ctk.CTkFrame(cartao_lista, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 12))
        cabecalho.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            cabecalho, text="Arquivos que serão incluídos", font=FONTE_LABEL,
            text_color=COR_TEXTO_PRINCIPAL, anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            cabecalho, text="Atualizar lista", width=140, height=36, corner_radius=8,
            fg_color=COR_CINZA_BOTAO, hover_color=COR_CINZA_BOTAO_HOVER,
            text_color=COR_TEXTO_PRINCIPAL, font=FONTE_AJUDA, command=self.atualizar_lista,
        ).grid(row=0, column=1, sticky="e")

        envoltorio_tabela, self.tabela = _criar_tabela(
            cartao_lista, colunas=("Arquivo", "Tipo"), larguras=(500, 120)
        )
        envoltorio_tabela.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 28))

    # -- helpers -------------------------------------------------------------
    def definir_pasta(self, pasta):
        self.campo_pasta_pdf.set(pasta)
        self.atualizar_lista()

    def _definir_aviso(self, texto):
        self.after(0, lambda: self.aviso_var.set(texto))

    def atualizar_lista(self):
        pasta = self.campo_pasta_pdf.get()
        for linha in self.tabela.get_children():
            self.tabela.delete(linha)

        arquivos = listar_arquivos_validos(pasta)
        for caminho in arquivos:
            extensao = os.path.splitext(caminho)[1].lower()
            tipo = "PDF" if extensao == EXTENSAO_PDF else "Imagem"
            self.tabela.insert("", "end", values=(os.path.basename(caminho), tipo))

        if not pasta:
            self._definir_aviso("Escolha a pasta e gere o PDF para revisar antes de imprimir.")
        elif not arquivos:
            self._definir_aviso("Nenhuma imagem ou PDF encontrado nessa pasta.")
        else:
            self._definir_aviso(f"{len(arquivos)} arquivo(s) prontos para compor o PDF.")

    # -- ações -------------------------------------------------------------
    def executar_gerar_pdf(self):
        if img2pdf is None or PdfReader is None or PdfWriter is None:
            messagebox.showerror(
                "Bibliotecas faltando",
                "Instale as bibliotecas necessárias abrindo o Prompt de Comando e digitando:\n\n"
                "pip install pypdf img2pdf",
            )
            return

        pasta = self.campo_pasta_pdf.get()
        if not pasta or not os.path.isdir(pasta):
            messagebox.showwarning("Pasta inválida", "Selecione uma pasta válida.")
            return

        arquivos = listar_arquivos_validos(pasta)
        if not arquivos:
            messagebox.showinfo("Nada encontrado", "Nenhuma imagem ou PDF encontrado nessa pasta.")
            return

        self.botao_gerar.configure(state="disabled", text="Gerando...")
        self.botao_abrir.configure(state="disabled")
        self.botao_imprimir.configure(state="disabled")
        self._definir_aviso(f"Gerando PDF com {len(arquivos)} arquivo(s)...")

        def tarefa():
            nome_saida = f"mapas_compilados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            caminho_saida = os.path.join(pasta, nome_saida)
            sucesso = gerar_pdf_unico(arquivos, caminho_saida, log=self.app.definir_status)

            def finalizar():
                self.botao_gerar.configure(state="normal", text="Gerar PDF único")
                if sucesso:
                    self.ultimo_pdf_gerado = caminho_saida
                    self.botao_abrir.configure(state="normal")
                    self.botao_imprimir.configure(state="normal")
                    self._definir_aviso(f"PDF gerado: {os.path.basename(caminho_saida)}")
                    self.app.definir_status(f"PDF gerado: {caminho_saida}")
                else:
                    self._definir_aviso("Não foi possível gerar o PDF. Veja a barra de status para detalhes.")

            self.after(0, finalizar)

        threading.Thread(target=tarefa, daemon=True).start()

    def executar_abrir(self):
        if self.ultimo_pdf_gerado:
            abrir_no_chrome(self.ultimo_pdf_gerado, log=self.app.definir_status)

    def executar_imprimir(self):
        if self.ultimo_pdf_gerado:
            imprimir_pdf(self.ultimo_pdf_gerado, log=self.app.definir_status)
            self._definir_aviso("Comando de impressão enviado.")


# ---------------------------------------------------------------------------
# Janela principal
# ---------------------------------------------------------------------------

class AplicacaoMapas(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Central de Mapas")
        self.geometry("1260x900")
        self.minsize(960, 680)
        self.configure(fg_color=COR_FUNDO)
        self._definir_icone()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._montar_cabecalho()
        self._montar_conteudo()
        self._montar_rodape()

        self.mostrar_passo(1)

    # -- ícone da janela / da barra de tarefas --------------------------------
    def _definir_icone(self):
        try:
            self.iconbitmap(caminho_recurso("central_de_mapas.ico"))
        except Exception:
            try:
                icone_png = tk.PhotoImage(file=caminho_recurso("central_de_mapas.png"))
                self.iconphoto(True, icone_png)
                self._icone_png_ref = icone_png  # mantém referência viva
            except Exception:
                pass

    # -- cabeçalho -----------------------------------------------------------
    def _montar_cabecalho(self):
        cabecalho = ctk.CTkFrame(self, fg_color=COR_HEADER_DE, corner_radius=0, height=172)
        cabecalho.grid(row=0, column=0, sticky="ew")
        cabecalho.grid_propagate(False)
        cabecalho.grid_columnconfigure(0, weight=1)

        conteudo = ctk.CTkFrame(cabecalho, fg_color="transparent")
        conteudo.grid(row=0, column=0, sticky="nsw", padx=40, pady=26)
        conteudo.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            conteudo, text="CENTRAL DE MAPAS", font=FONTE_TAG, text_color=COR_DESTAQUE, anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            conteudo, text="Organize seus mapas com tranquilidade.", font=FONTE_TITULO,
            text_color="white", anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(6, 6))
        ctk.CTkLabel(
            conteudo, text="Busque as versões certas, monte o PDF e envie para impressão em poucos passos.",
            font=FONTE_SUBTITULO, text_color=COR_TEXTO_CLARO, anchor="w",
        ).grid(row=2, column=0, sticky="w")

        ctk.CTkButton(
            cabecalho, text="Como usar", height=42, width=140, corner_radius=21,
            fg_color="transparent", hover_color="#1B3A5C", border_width=1,
            border_color=COR_DESTAQUE, text_color=COR_DESTAQUE, font=FONTE_BOTAO,
            command=self.abrir_ajuda,
        ).grid(row=0, column=1, sticky="ne", padx=40, pady=26)

    def _montar_conteudo(self):
        area_central = ctk.CTkFrame(self, fg_color=COR_FUNDO, corner_radius=0)
        area_central.grid(row=1, column=0, sticky="nsew")
        area_central.grid_columnconfigure(0, weight=1)
        area_central.grid_rowconfigure(1, weight=1)

        # -- pill de navegação, logo abaixo do cabeçalho ----------------------
        # (o tamanho se ajusta sozinho ao texto dos botões, então funciona
        # mesmo se a fonte ou os textos mudarem no futuro)
        pill = ctk.CTkFrame(area_central, fg_color=COR_HEADER_DE, corner_radius=24)
        pill.grid(row=0, column=0, pady=(22, 22))

        self.botao_passo1 = ctk.CTkButton(
            pill, text="1   Buscar mapas", height=42, corner_radius=20,
            font=FONTE_PASSO, command=lambda: self.mostrar_passo(1),
        )
        self.botao_passo1.pack(side="left", padx=(6, 3), pady=6)

        self.botao_passo2 = ctk.CTkButton(
            pill, text="2   Gerar PDF e imprimir", height=42, corner_radius=20,
            font=FONTE_PASSO, command=lambda: self.mostrar_passo(2),
        )
        self.botao_passo2.pack(side="left", padx=(3, 6), pady=6)

        # -- área com rolagem para os cartões ---------------------------------
        self.area_rolagem = ctk.CTkScrollableFrame(
            area_central, fg_color="transparent",
            scrollbar_button_color=COR_BORDA, scrollbar_button_hover_color=COR_TEXTO_SECUNDARIO,
        )
        self.area_rolagem.grid(row=1, column=0, sticky="nsew", padx=40, pady=(0, 24))
        self.area_rolagem.grid_columnconfigure(0, weight=1)

        self.passo_buscar = PassoBuscar(self.area_rolagem, self)
        self.passo_pdf = PassoPdf(self.area_rolagem, self)

    def _montar_rodape(self):
        rodape = ctk.CTkFrame(self, fg_color="#E4E9F0", corner_radius=0, height=40)
        rodape.grid(row=2, column=0, sticky="ew")
        rodape.grid_propagate(False)
        rodape.grid_columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Pronto para começar.")
        ctk.CTkLabel(
            rodape, textvariable=self.status_var, font=FONTE_STATUS,
            text_color=COR_TEXTO_SECUNDARIO, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=18)

    # -- janela de ajuda -------------------------------------------------------
    def abrir_ajuda(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Como usar a Central de Mapas")
        janela.geometry("700x640")
        janela.minsize(560, 420)
        janela.configure(fg_color=COR_FUNDO)
        try:
            janela.iconbitmap(caminho_recurso("central_de_mapas.ico"))
        except Exception:
            pass

        janela.grid_columnconfigure(0, weight=1)
        janela.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            janela, text="Como usar a Central de Mapas", font=FONTE_LABEL,
            text_color=COR_TEXTO_PRINCIPAL, anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 12))

        caixa = ctk.CTkTextbox(
            janela, font=FONTE_BASE, fg_color="#FFFFFF", text_color=COR_TEXTO_PRINCIPAL,
            corner_radius=12, border_width=1, border_color=COR_BORDA, wrap="word",
        )
        caixa.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 12))
        caixa.insert("1.0", TEXTO_AJUDA)
        caixa.configure(state="disabled")

        ctk.CTkButton(
            janela, text="Fechar", height=42, width=140, corner_radius=9,
            fg_color=COR_NAVY_BOTAO, hover_color=COR_NAVY_BOTAO_HOVER, font=FONTE_BOTAO,
            command=janela.destroy,
        ).grid(row=2, column=0, pady=(0, 22))

        janela.transient(self)
        janela.grab_set()

    # -- navegação entre passos -----------------------------------------------
    def mostrar_passo(self, numero):
        ativo = dict(fg_color=COR_DESTAQUE, hover_color=COR_DESTAQUE, text_color=COR_HEADER_DE)
        inativo = dict(fg_color=COR_PILL_INATIVO, hover_color=COR_HEADER_PARA, text_color="white")

        if numero == 1:
            self.botao_passo1.configure(**ativo)
            self.botao_passo2.configure(**inativo)
            self.passo_pdf.grid_forget()
            self.passo_buscar.grid(row=0, column=0, sticky="nsew")
        else:
            self.botao_passo2.configure(**ativo)
            self.botao_passo1.configure(**inativo)
            self.passo_buscar.grid_forget()
            self.passo_pdf.grid(row=0, column=0, sticky="nsew")

    def definir_pasta_pdf_padrao(self, pasta):
        self.passo_pdf.definir_pasta(pasta)

    # -- status global (rodapé) -----------------------------------------------
    def definir_status(self, mensagem):
        self.after(0, lambda: self.status_var.set(mensagem))


if __name__ == "__main__":
    app = AplicacaoMapas()
    app.mainloop()
