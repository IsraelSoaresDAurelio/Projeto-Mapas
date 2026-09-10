# Central de Mapas

Aplicativo desktop (Windows) que automatiza a busca, cópia e impressão de mapas. Em vez de vasculhar pastas manualmente, copiar arquivo por arquivo e montar um PDF, o usuário digita os códigos das zonas que precisa e o programa faz o resto.

## O que o aplicativo faz

O uso é dividido em dois passos, alternados por uma aba no topo da tela:

**1. Buscar mapas**
- Informe a pasta onde os mapas ficam guardados (a busca entra em todas as subpastas sozinha).
- Digite os códigos das zonas procuradas, separados por `;`, `,` ou um por linha. Sem separador, o app tenta identificar sozinho sequências como "zona 1 zona 2 zona 3".
- Informe a pasta de destino.
- **Buscar versões mais recentes** localiza, para cada código, o arquivo mais atualizado (por data de modificação) e mostra o resultado numa tabela (Termo / Última modificação).
- **Salvar arquivos na pasta destino** copia os arquivos encontrados para a pasta de destino e a abre automaticamente no Explorador de Arquivos ao final.
- **Limpar pasta de destino** apaga o conteúdo da pasta de destino (com confirmação) — recomendado usar sempre ao abrir o aplicativo, para não misturar buscas antigas com a atual.

**2. Gerar PDF e imprimir**
- A pasta usada no Passo 1 já vem preenchida.
- **Gerar PDF único** junta todas as imagens e PDFs da pasta em um único arquivo, em ordem alfabética.
- **Abrir no navegador** permite revisar o PDF antes de imprimir.
- **Imprimir** envia o PDF direto para a impressora.

Um botão **"Como usar"**, no canto superior direito, abre as instruções completas a qualquer momento dentro do próprio app.

## Estrutura desta pasta

| Arquivo/pasta | Descrição |
|---|---|
| `app_mapas.py` | Código-fonte principal do aplicativo (interface + lógica de busca/cópia/PDF). |
| `Abrir Central de Mapas.pyw` | Launcher usado para abrir o app a partir do código-fonte (sem gerar exe). |
| `central_de_mapas.ico` / `.png` | Ícone do aplicativo (janela e executável). |
| `CentralDeMapas.spec` | Configuração do PyInstaller usada para gerar o `.exe`. |
| `Gerar_Executavel.bat` | Script que instala as dependências e gera/atualiza o `Central de Mapas.exe` com um duplo clique. |
| `Central de Mapas.exe` | Executável pronto para uso, sem precisar instalar Python. |
| `buscar_arquivos_recentes.py`, `compactar_e_imprimir_mapas.py` | Módulos auxiliares de uma versão anterior do projeto, mantidos como referência. |
| `app_mapas_ANTIGO_backup.py` | Versão bem antiga do app (pré-redesenho), guardada apenas como histórico. |
| `Backup 2026-09-04/` | Cópia de segurança do código-fonte e recursos, feita antes de uma rodada de mudanças visuais em 04/09/2026. |
| `Claude outputs/` | Guia rápido de uso do aplicativo (Word e PDF), com capturas de tela de cada etapa — pode ser compartilhado com quem for usar o app. |

## Como rodar

**Opção 1 — usar o executável (mais simples):** dar duplo clique em `Central de Mapas.exe`. Não precisa ter Python instalado.

**Opção 2 — rodar a partir do código-fonte:** com Python 3.10+ instalado, instalar as dependências e abrir `Abrir Central de Mapas.pyw` (ou rodar `python app_mapas.py`).

## Como gerar/atualizar o executável

1. Alterar `app_mapas.py` conforme necessário.
2. Dar duplo clique em `Gerar_Executavel.bat`.
3. O script instala/atualiza as bibliotecas (`customtkinter`, `pypdf`, `img2pdf`, `pyinstaller`), limpa builds antigas e gera o novo `Central de Mapas.exe` nesta mesma pasta.
4. Todo o processo é registrado em `build_log.txt`, útil para diagnosticar qualquer erro na geração.

**Requisito:** Python instalado "de verdade" (via python.org, com a opção "Add python.exe to PATH" marcada) — não o atalho da Microsoft Store, que não executa o script corretamente.

## Dependências (quando rodando via código-fonte)

- `customtkinter` — interface gráfica
- `pypdf` e `img2pdf` — montagem do PDF único
- `pyinstaller` — apenas para gerar o `.exe`

## Observação

Este projeto é irmão do **Buscador GPS** (projeto separado, na pasta "Projeto GPS -Monitores"), que resolve uma necessidade parecida só que para localizar monitores de GPS. São aplicativos independentes, cada um com seu próprio código, ícone e executável.
