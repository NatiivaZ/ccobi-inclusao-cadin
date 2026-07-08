"""Interface desktop da inclusão CADIN."""

import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

import config
from automacao_cadin import AutomacaoCadin
from exportacao_resultados import copiar_checkpoint_para_resultados, exportar_checkpoint_csv, exportar_resultado
from leitor_planilha import aplicar_resultado, obter_registro, preparar_base
from logging_utils import Logger


CORES = {
    "fundo": "#EEF3F8",
    "card": "#FFFFFF",
    "primario": "#12355B",
    "primario_2": "#1F5A8A",
    "verde": "#1E9E63",
    "vermelho": "#D64545",
    "amarelo": "#D99021",
    "texto": "#17202A",
    "muted": "#667085",
    "borda": "#D6E0EA",
    "log_bg": "#0F172A",
    "log_fg": "#DCE7F3",
}

FONTE = "Segoe UI"


def caminho_recurso(relativo: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / relativo
    return Path(__file__).resolve().parent / relativo


class InterfaceCadin:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Inclusao CADIN")
        self.root.geometry("1160x760")
        self.root.minsize(980, 680)
        self.root.configure(bg=CORES["fundo"])
        self.logo_header = None
        self._aplicar_logo_janela()

        self.arquivo_entrada = tk.StringVar()
        self.arquivo_saida = tk.StringVar()
        self.usuario_login = tk.StringVar()
        self.senha_login = tk.StringVar()
        self.status = tk.StringVar(value="Aguardando planilha...")
        self.progresso = tk.DoubleVar(value=0)
        self.total = tk.IntVar(value=0)
        self.processados = tk.IntVar(value=0)
        self.sucessos = tk.IntVar(value=0)
        self.testes = tk.IntVar(value=0)
        self.erros = tk.IntVar(value=0)
        self.ignorados = tk.IntVar(value=0)
        self.manter_navegador = tk.BooleanVar(value=True)
        self.modo_teste_limpar = tk.BooleanVar(value=False)
        self.login_manual_govbr = tk.BooleanVar(value=True)
        self.usar_anonimo = tk.BooleanVar(value=False)

        self.logger = Logger(self._log_callback)
        self.automacao = None
        self.thread_automacao = None
        self.executando = False
        self.pausado = False
        self.parar = False

        self._configurar_estilo()
        self._montar_tela()

    def executar(self):
        self.root.mainloop()

    def _aplicar_logo_janela(self):
        caminho_ico = caminho_recurso("assets/logo_antt.ico")
        if not caminho_ico.exists():
            return
        try:
            ico = Image.open(caminho_ico)
            # Barra de tarefas: .ico com varios tamanhos (inclui 16–48 px)
            self.root.iconbitmap(str(caminho_ico))
        except Exception:
            pass
        try:
            ico = Image.open(caminho_ico)
            ico.seek(0)
            base = ico.copy().convert("RGBA")
            # Titulo da janela: 32 px (proporcao parecida com Explorer/barra)
            titulo = base.resize((32, 32), Image.Resampling.LANCZOS)
            self._icone_janela = ImageTk.PhotoImage(titulo)
            self.root.iconphoto(True, self._icone_janela)
        except Exception:
            pass

    def _configurar_estilo(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=CORES["fundo"])
        style.configure("Card.TFrame", background=CORES["card"], relief="flat")
        style.configure("TLabel", background=CORES["fundo"], foreground=CORES["texto"], font=(FONTE, 10))
        style.configure("Card.TLabel", background=CORES["card"], foreground=CORES["texto"], font=(FONTE, 10))
        style.configure("Muted.TLabel", background=CORES["card"], foreground=CORES["muted"], font=(FONTE, 9))
        style.configure("Titulo.TLabel", background=CORES["primario"], foreground="white", font=(FONTE, 20, "bold"))
        style.configure("Subtitulo.TLabel", background=CORES["primario"], foreground="#BFD4E8", font=(FONTE, 10))
        style.configure("TEntry", fieldbackground="white", bordercolor=CORES["borda"], lightcolor=CORES["borda"])
        style.configure("Horizontal.TProgressbar", troughcolor="#D8E2EC", background=CORES["primario_2"])
        style.configure("TCheckbutton", background=CORES["card"], foreground=CORES["texto"], font=(FONTE, 9))

    def _montar_tela(self):
        header = tk.Frame(self.root, bg=CORES["primario"], height=96)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        bloco_titulo = tk.Frame(header, bg=CORES["primario"])
        bloco_titulo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(bloco_titulo, text="Inclusao CADIN", style="Titulo.TLabel").pack(anchor="w", padx=28, pady=(18, 0))
        ttk.Label(
            bloco_titulo,
            text="Automacao com Chrome visivel, perfil persistente, checkpoints e logs em tempo real",
            style="Subtitulo.TLabel",
        ).pack(anchor="w", padx=30, pady=(4, 0))

        self._adicionar_logo_header(header)

        container = tk.Frame(self.root, bg=CORES["fundo"], padx=22, pady=18)
        container.pack(fill=tk.BOTH, expand=True)

        painel_topo = tk.Frame(container, bg=CORES["fundo"])
        painel_topo.pack(fill=tk.X, pady=(0, 14))

        card_login = self._card(painel_topo, "Acesso gov.br")
        card_login.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self._linha_entry(card_login, "CPF gov.br", self.usuario_login)
        self._linha_entry(card_login, "Senha gov.br", self.senha_login, show="*")
        ttk.Checkbutton(
            card_login,
            text="Manter navegador aberto ao finalizar",
            variable=self.manter_navegador,
        ).pack(anchor="w", padx=16, pady=(8, 0))
        ttk.Checkbutton(
            card_login,
            text="Login gov.br manual (recomendado)",
            variable=self.login_manual_govbr,
        ).pack(anchor="w", padx=16, pady=(4, 0))
        ttk.Checkbutton(
            card_login,
            text="Abrir Chrome em guia anonima (teste)",
            variable=self.usar_anonimo,
        ).pack(anchor="w", padx=16, pady=(4, 0))
        ttk.Checkbutton(
            card_login,
            text="Modo teste: preencher e clicar em Limpar (nao incluir)",
            variable=self.modo_teste_limpar,
        ).pack(anchor="w", padx=16, pady=(4, 0))
        ttk.Label(
            card_login,
            text="Com login manual ativo, a automacao nao preenche CPF/senha no gov.br.",
            style="Muted.TLabel",
        ).pack(anchor="w", padx=16, pady=(6, 2))
        ttk.Label(
            card_login,
            text="Modo teste desmarcado: a automacao clicara em Incluir.",
            style="Muted.TLabel",
        ).pack(anchor="w", padx=16, pady=(0, 2))
        ttk.Label(
            card_login,
            text="Se houver CAPTCHA, resolva manualmente no Chrome aberto. O lote continua do ponto salvo.",
            style="Muted.TLabel",
        ).pack(anchor="w", padx=16, pady=(0, 2))
        ttk.Label(
            card_login,
            text=f"A sessao e renovada automaticamente a cada {config.INTERVALO_RELOGIN_MINUTOS} minutos.",
            style="Muted.TLabel",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        card_arquivo = self._card(painel_topo, "Planilha e resultado")
        card_arquivo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        self._linha_arquivo(card_arquivo, "Planilha", self.arquivo_entrada, self._selecionar_planilha)
        self._linha_arquivo(
            card_arquivo,
            "Resultado",
            self.arquivo_saida,
            self._selecionar_saida,
            texto_botao="Alterar pasta",
            somente_leitura=True,
        )
        ttk.Label(
            card_arquivo,
            text="Colunas esperadas: CPF/CNPJ, PROTOCOLO/PROCESSO, AUTO DE INFRACAO, DATA DE VENCIMENTO",
            style="Muted.TLabel",
        ).pack(anchor="w", padx=16, pady=(8, 12))

        painel_metricas = tk.Frame(container, bg=CORES["fundo"])
        painel_metricas.pack(fill=tk.X, pady=(0, 14))
        self._metric_card(painel_metricas, "Total", self.total, CORES["primario"]).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self._metric_card(painel_metricas, "Processados", self.processados, CORES["primario_2"]).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        self._metric_card(painel_metricas, "Sucessos", self.sucessos, CORES["verde"]).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        self._metric_card(painel_metricas, "Testes", self.testes, CORES["primario_2"]).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        self._metric_card(painel_metricas, "Erros", self.erros, CORES["vermelho"]).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        self._metric_card(painel_metricas, "Ignorados", self.ignorados, CORES["amarelo"]).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

        card_log = self._card(container, "Execucao")
        card_log.pack(fill=tk.BOTH, expand=True, pady=(0, 14))

        barra_status = tk.Frame(card_log, bg=CORES["card"])
        barra_status.pack(fill=tk.X, padx=16, pady=(4, 8))
        ttk.Label(barra_status, textvariable=self.status, style="Card.TLabel", font=(FONTE, 10, "bold")).pack(side=tk.LEFT)

        self.log_text = scrolledtext.ScrolledText(
            card_log,
            height=15,
            font=("Consolas", 9),
            wrap=tk.WORD,
            bg=CORES["log_bg"],
            fg=CORES["log_fg"],
            insertbackground="white",
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))
        self.log_text.tag_config("ERROR", foreground="#FF6B6B")
        self.log_text.tag_config("SUCCESS", foreground="#57D68D")
        self.log_text.tag_config("WARNING", foreground="#F4D03F")
        self.log_text.tag_config("INFO", foreground=CORES["log_fg"])

        self.barra = ttk.Progressbar(container, variable=self.progresso, maximum=100)
        self.barra.pack(fill=tk.X, pady=(0, 14))

        acoes = tk.Frame(container, bg=CORES["fundo"])
        acoes.pack(fill=tk.X)
        self._botao(acoes, "Iniciar", CORES["verde"], self._iniciar).pack(side=tk.LEFT, padx=(0, 10))
        self._botao(acoes, "Pausar / Continuar", CORES["amarelo"], self._alternar_pausa).pack(side=tk.LEFT, padx=(0, 10))
        self._botao(acoes, "Parar", CORES["vermelho"], self._parar).pack(side=tk.LEFT, padx=(0, 10))
        self._botao(acoes, "Abrir resultados", CORES["primario_2"], self._abrir_resultados).pack(side=tk.LEFT)

    def _adicionar_logo_header(self, parent):
        caminho_logo = caminho_recurso("assets/logo_antt.png")
        if not caminho_logo.exists():
            return
        try:
            imagem = Image.open(caminho_logo).convert("RGBA")
            imagem.thumbnail((96, 40), Image.LANCZOS)
            self.logo_header = ImageTk.PhotoImage(imagem)
            tk.Label(parent, image=self.logo_header, bg=CORES["primario"], bd=0).pack(
                side=tk.RIGHT,
                padx=28,
                pady=14,
            )
        except Exception:
            self.logo_header = None

    def _card(self, parent, titulo):
        return tk.LabelFrame(
            parent,
            text=f"  {titulo}  ",
            bg=CORES["card"],
            fg=CORES["primario"],
            font=(FONTE, 10, "bold"),
            relief=tk.GROOVE,
            bd=1,
            padx=0,
            pady=10,
        )

    def _linha_entry(self, parent, titulo, variavel, show=""):
        frame = tk.Frame(parent, bg=CORES["card"])
        frame.pack(fill=tk.X, padx=16, pady=5)
        tk.Label(frame, text=titulo, bg=CORES["card"], fg=CORES["texto"], font=(FONTE, 9), width=18, anchor="w").pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=variavel, show=show).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _linha_arquivo(self, parent, titulo, variavel, comando, texto_botao="Selecionar", somente_leitura=False):
        frame = tk.Frame(parent, bg=CORES["card"])
        frame.pack(fill=tk.X, padx=16, pady=5)
        tk.Label(frame, text=titulo, bg=CORES["card"], fg=CORES["texto"], font=(FONTE, 9), width=14, anchor="w").pack(side=tk.LEFT)
        estado = "readonly" if somente_leitura else "normal"
        ttk.Entry(frame, textvariable=variavel, state=estado).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(frame, text=texto_botao, command=comando).pack(side=tk.LEFT)

    def _mini_entry(self, parent, titulo, variavel):
        frame = tk.Frame(parent, bg=CORES["card"])
        frame.pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(frame, text=titulo, bg=CORES["card"], fg=CORES["muted"], font=(FONTE, 8)).pack(anchor="w")
        ttk.Entry(frame, textvariable=variavel, width=8).pack(anchor="w")

    def _metric_card(self, parent, titulo, variavel, cor):
        frame = tk.Frame(parent, bg=CORES["card"], bd=1, relief=tk.GROOVE, padx=14, pady=12)
        tk.Label(frame, text=titulo, bg=CORES["card"], fg=CORES["muted"], font=(FONTE, 9, "bold")).pack(anchor="w")
        tk.Label(frame, textvariable=variavel, bg=CORES["card"], fg=cor, font=(FONTE, 22, "bold")).pack(anchor="w")
        return frame

    def _botao(self, parent, texto, cor, comando):
        return tk.Button(
            parent,
            text=texto,
            command=comando,
            bg=cor,
            fg="white",
            activebackground=cor,
            activeforeground="white",
            font=(FONTE, 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
        )

    def _selecionar_planilha(self):
        caminho = filedialog.askopenfilename(
            title="Selecione a planilha de inclusao CADIN",
            filetypes=[
                ("Planilhas", "*.xlsx *.xlsm *.xls *.csv"),
                ("Excel", "*.xlsx *.xlsm *.xls"),
                ("CSV", "*.csv"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if not caminho:
            return
        self.arquivo_entrada.set(caminho)
        config.PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
        nome = os.path.splitext(os.path.basename(caminho))[0]
        saida = config.PASTA_RESULTADOS / f"{nome}_resultado_cadin_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        self.arquivo_saida.set(str(saida))
        self.status.set("Planilha selecionada. Pronto para iniciar.")

    def _selecionar_saida(self):
        caminho = filedialog.asksaveasfilename(
            title="Salvar resultado como",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"resultado_cadin_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
        )
        if caminho:
            self.arquivo_saida.set(caminho)

    def _iniciar(self):
        if self.executando:
            messagebox.showwarning("Automacao em andamento", "A automacao ja esta executando.")
            return
        if not self.arquivo_entrada.get().strip():
            messagebox.showwarning("Planilha obrigatoria", "Selecione a planilha de entrada.")
            return
        if not self.arquivo_saida.get().strip():
            messagebox.showwarning("Resultado obrigatorio", "Informe o arquivo de resultado.")
            return
        if not self.modo_teste_limpar.get():
            confirmar = messagebox.askyesno(
                "Confirmar inclusao real",
                "O modo teste esta desmarcado. A automacao vai clicar em INCLUIR para cada linha valida.\n\n"
                "Confirma que deseja iniciar a inclusao real no CADIN?",
            )
            if not confirmar:
                return

        self.executando = True
        self.pausado = False
        self.parar = False
        self._zerar_metricas()

        self.thread_automacao = threading.Thread(target=self._executar_automacao, daemon=True)
        self.thread_automacao.start()

    def _executar_automacao(self):
        caminho_saida = self.arquivo_saida.get().strip()
        config.PASTA_LOGS.mkdir(parents=True, exist_ok=True)
        log_path = config.PASTA_LOGS / f"inclusao_cadin_{datetime.now():%Y%m%d_%H%M%S}.txt"
        self.logger.set_log_file(str(log_path))

        df = None
        try:
            self._set_status("Lendo planilha...")
            df = preparar_base(self.arquivo_entrada.get().strip())
            total = len(df)
            self._set_var(self.total, total)
            self._atualizar_metricas(df)
            exportar_resultado(df, caminho_saida)
            caminho_checkpoint_local = exportar_checkpoint_csv(df, caminho_saida, local=True)

            self.logger.log(f"Planilha carregada com {total} linha(s).")
            self.logger.log(f"Checkpoint rapido local em CSV: {caminho_checkpoint_local}")
            self.automacao = AutomacaoCadin(
                self.logger,
                modo_teste_limpar=self.modo_teste_limpar.get(),
                login_manual_govbr=self.login_manual_govbr.get(),
                usar_anonimo=self.usar_anonimo.get(),
            )
            if self.modo_teste_limpar.get():
                self.logger.log("MODO TESTE ATIVO: a automacao clicara em Limpar, nao em Incluir.", "WARNING")
            if self.login_manual_govbr.get():
                self.logger.log(
                    "LOGIN MANUAL ATIVO: entre no gov.br pelo Chrome aberto; "
                    "a automacao continuara ao detectar a tela inicial do CADIN.",
                    "WARNING",
                )
            if self.usar_anonimo.get():
                self.logger.log(
                    "TESTE EM GUIA ANONIMA ATIVO: cookies e sessao do perfil persistente nao serao usados.",
                    "WARNING",
                )
            self.automacao.abrir_e_logar(self.usuario_login.get(), self.senha_login.get())
            self.automacao.acessar_incluir_cadastro()

            for posicao, indice in enumerate(df.index, start=1):
                if self.parar:
                    aplicar_resultado(df, indice, config.STATUS_PARADO, "Parado pelo usuario.", 0)
                    exportar_checkpoint_csv(df, caminho_saida, local=True)
                    break

                self._sincronizar_flags()
                status_atual = str(df.at[indice, "STATUS_CADIN"] or "").upper()
                if status_atual == config.STATUS_IGNORADO:
                    self.logger.log(f"Linha {int(df.at[indice, '_LINHA_ORIGINAL'])}: ignorada por validacao.", "WARNING")
                    self._atualizar_andamento(df, posicao, total)
                    continue

                registro = obter_registro(df, indice)
                self._set_status(f"Processando linha {registro.linha_original}...")
                self.automacao.renovar_sessao_se_necessario()
                resultado = self.automacao.processar_registro(registro)
                aplicar_resultado(
                    df,
                    indice,
                    resultado.status,
                    resultado.mensagem,
                    resultado.tentativas,
                    resultado.observacao,
                )
                exportar_checkpoint_csv(df, caminho_saida, local=True)
                self._atualizar_andamento(df, posicao, total)

            self._set_status("Gerando Excel final formatado...")
            caminho_checkpoint_final = copiar_checkpoint_para_resultados(caminho_saida, caminho_checkpoint_local)
            exportar_resultado(df, caminho_saida)
            self._set_status("Automacao finalizada." if not self.parar else "Automacao parada pelo usuario.")
            self.logger.log(f"Checkpoint de auditoria salvo em: {caminho_checkpoint_final}", "SUCCESS")
            self.logger.log(f"Resultado salvo em: {caminho_saida}", "SUCCESS")
        except Exception as exc:
            self.logger.log(f"Erro geral: {exc}", "ERROR")
            self._set_status("Erro durante a execucao.")
            if df is not None:
                try:
                    caminho_checkpoint_local = exportar_checkpoint_csv(df, caminho_saida, local=True)
                    copiar_checkpoint_para_resultados(caminho_saida, caminho_checkpoint_local)
                    exportar_resultado(df, caminho_saida)
                except Exception:
                    pass
            msg = str(exc)
            self.root.after(0, lambda: messagebox.showerror("Erro", msg))
        finally:
            if self.automacao and not self.manter_navegador.get():
                self.automacao.fechar()
            self.executando = False
            self.pausado = False

    def _alternar_pausa(self):
        if not self.executando:
            return
        self.pausado = not self.pausado
        self._sincronizar_flags()
        if self.pausado:
            self.status.set("Pausado pelo usuario.")
            self.logger.log("Automacao pausada pelo usuario.", "WARNING")
        else:
            self.status.set("Continuando automacao...")
            self.logger.log("Automacao retomada pelo usuario.", "SUCCESS")

    def _parar(self):
        if not self.executando:
            return
        self.parar = True
        self.pausado = False
        self._sincronizar_flags()
        self.status.set("Parando em ponto seguro...")
        self.logger.log("Parada solicitada. Aguardando ponto seguro.", "WARNING")

    def _abrir_resultados(self):
        config.PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
        os.startfile(config.PASTA_RESULTADOS)

    def _sincronizar_flags(self):
        if self.automacao:
            self.automacao.pausado = self.pausado
            self.automacao.parar = self.parar

    def _atualizar_andamento(self, df, posicao: int, total: int):
        self._set_var(self.processados, posicao)
        self._set_var(self.progresso, (posicao / total) * 100 if total else 0)
        self._atualizar_metricas(df)

    def _atualizar_metricas(self, df):
        status = df["STATUS_CADIN"].astype(str).str.upper()
        self._set_var(self.sucessos, int((status == config.STATUS_SUCESSO).sum()))
        self._set_var(self.testes, int((status == config.STATUS_TESTE).sum()))
        self._set_var(self.erros, int((status == config.STATUS_ERRO).sum()))
        self._set_var(self.ignorados, int((status == config.STATUS_IGNORADO).sum()))

    def _zerar_metricas(self):
        for variavel in (self.total, self.processados, self.sucessos, self.testes, self.erros, self.ignorados):
            self._set_var(variavel, 0)
        self._set_var(self.progresso, 0)

    def _set_status(self, texto):
        self.root.after(0, lambda: self.status.set(texto))

    def _set_var(self, variavel, valor):
        self.root.after(0, lambda: variavel.set(valor))

    def _int_config(self, variavel, padrao):
        try:
            return int(str(variavel.get()).strip())
        except ValueError:
            return padrao

    def _float_config(self, variavel, padrao):
        try:
            return float(str(variavel.get()).replace(",", ".").strip())
        except ValueError:
            return padrao

    def _log_callback(self, entrada, tipo):
        def inserir():
            self.log_text.insert(tk.END, entrada + "\n", tipo)
            self.log_text.see(tk.END)

        self.root.after(0, inserir)


if __name__ == "__main__":
    InterfaceCadin().executar()

