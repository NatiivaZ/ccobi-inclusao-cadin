"""PORTFOLIO — automacao operacional omitida. Estrutura publica apenas."""
from __future__ import annotations
from portfolio_omitted import omit


class AutomacaoCadin:
    """Stub publico. Metodos operacionais levantam PortfolioOmittedError."""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def iniciar(self, *args, **kwargs):
        omit("AutomacaoCadin.iniciar")

    def abrir_e_logar(self, *args, **kwargs):
        omit("AutomacaoCadin.abrir_e_logar")

    def renovar_sessao_se_necessario(self, *args, **kwargs):
        omit("AutomacaoCadin.renovar_sessao_se_necessario")

    def fechar(self, *args, **kwargs):
        omit("AutomacaoCadin.fechar")

    def acessar_incluir_cadastro(self, *args, **kwargs):
        omit("AutomacaoCadin.acessar_incluir_cadastro")

    def processar_registro(self, *args, **kwargs):
        omit("AutomacaoCadin.processar_registro")

    def __getattr__(self, name):
        def _missing(*args, **kwargs):
            omit(f"AutomacaoCadin.{name}")

        return _missing
