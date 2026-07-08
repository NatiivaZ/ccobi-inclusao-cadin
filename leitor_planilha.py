"""Leitura e normalização da planilha de inclusão CADIN."""

import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

import config


COLUNA_LINHA_ORIGINAL = "_LINHA_ORIGINAL"
COLUNA_CPF_CNPJ_NORMALIZADO = "_CPF_CNPJ_NORMALIZADO"
COLUNA_DATA_NORMALIZADA = "_DATA_VENCIMENTO_NORMALIZADA"

COLUNAS_RESULTADO = [
    "STATUS_CADIN",
    "MENSAGEM",
    "TENTATIVAS",
    "DATA_PROCESSAMENTO",
    "OBSERVACAO",
]


@dataclass
class RegistroCadin:
    indice: int
    linha_original: int
    cpf_cnpj: str
    protocolo_processo: str
    auto_infracao: str
    data_vencimento: str


def normalizar_nome_coluna(nome) -> str:
    texto = str(nome).strip().lower()
    texto = texto.replace("_", " ").replace("-", " ")
    texto = re.sub(r"\s+", " ", texto)
    return texto


def normalizar_cpf_cnpj(valor) -> Optional[str]:
    if pd.isna(valor):
        return None
    digitos = re.sub(r"\D", "", str(valor).strip())
    if not digitos:
        return None
    if len(digitos) in (11, 14):
        return digitos
    return None


def normalizar_texto(valor) -> Optional[str]:
    if pd.isna(valor):
        return None
    texto = str(valor).strip()
    if not texto or texto.lower() in {"nan", "none", "nat"}:
        return None
    return re.sub(r"\s+", " ", texto)


def normalizar_data(valor) -> Optional[str]:
    if pd.isna(valor):
        return None

    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")

    texto = str(valor).strip()
    if not texto or texto.lower() in {"nan", "none", "nat"}:
        return None

    if re.fullmatch(r"\d+(\.0)?", texto):
        serial = int(float(texto))
        if 1 <= serial <= 2958465:
            return (datetime(1899, 12, 30) + timedelta(days=serial)).strftime("%d/%m/%Y")

    texto = texto.split(" ")[0]
    for formato in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y"):
        try:
            return datetime.strptime(texto, formato).strftime("%d/%m/%Y")
        except ValueError:
            pass

    digitos = re.sub(r"\D", "", texto)
    if len(digitos) == 8:
        try:
            return datetime.strptime(digitos, "%d%m%Y").strftime("%d/%m/%Y")
        except ValueError:
            pass

    return None


def ler_planilha(caminho: str) -> pd.DataFrame:
    if not os.path.isfile(caminho):
        raise FileNotFoundError(f"Arquivo nao encontrado: {caminho}")

    extensao = os.path.splitext(caminho)[1].lower()
    if extensao in {".xlsx", ".xlsm"}:
        df = pd.read_excel(caminho, dtype=object, engine="openpyxl")
    elif extensao == ".xls":
        df = pd.read_excel(caminho, dtype=object, engine="xlrd")
    elif extensao == ".csv":
        df = pd.read_csv(caminho, dtype=object, sep=None, engine="python", encoding="utf-8-sig")
    else:
        raise ValueError("Formato nao suportado. Use .xlsx, .xlsm, .xls ou .csv.")

    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(how="all").copy()
    if df.empty:
        raise ValueError("A planilha esta vazia.")

    df[COLUNA_LINHA_ORIGINAL] = range(2, len(df) + 2)
    return df


def validar_colunas(df: pd.DataFrame) -> None:
    mapa = {normalizar_nome_coluna(coluna): coluna for coluna in df.columns}
    faltantes = []
    for coluna in config.COLUNAS_OBRIGATORIAS:
        if normalizar_nome_coluna(coluna) not in mapa:
            faltantes.append(coluna)
    if faltantes:
        raise ValueError("Colunas obrigatorias nao encontradas: " + ", ".join(faltantes))


def preparar_base(caminho: str) -> pd.DataFrame:
    df = ler_planilha(caminho)
    validar_colunas(df)

    for coluna in COLUNAS_RESULTADO:
        if coluna not in df.columns:
            df[coluna] = ""

    df[COLUNA_CPF_CNPJ_NORMALIZADO] = df["CPF/CNPJ"].apply(normalizar_cpf_cnpj)
    df[COLUNA_DATA_NORMALIZADA] = df["DATA DE VENCIMENTO"].apply(normalizar_data)

    for indice, linha in df.iterrows():
        observacoes = []
        if not linha[COLUNA_CPF_CNPJ_NORMALIZADO]:
            observacoes.append("CPF/CNPJ vazio ou invalido")
        if not normalizar_texto(linha["PROTOCOLO/PROCESSO"]):
            observacoes.append("PROTOCOLO/PROCESSO vazio")
        if not normalizar_texto(linha["AUTO DE INFRACAO"]):
            observacoes.append("AUTO DE INFRACAO vazio")
        if not linha[COLUNA_DATA_NORMALIZADA]:
            observacoes.append("DATA DE VENCIMENTO vazia ou invalida")
        if observacoes:
            aplicar_resultado(
                df,
                indice,
                config.STATUS_IGNORADO,
                "Registro ignorado antes do envio.",
                0,
                "; ".join(observacoes),
            )

    return df


def obter_registro(df: pd.DataFrame, indice) -> RegistroCadin:
    linha = df.loc[indice]
    return RegistroCadin(
        indice=indice,
        linha_original=int(linha[COLUNA_LINHA_ORIGINAL]),
        cpf_cnpj=linha[COLUNA_CPF_CNPJ_NORMALIZADO],
        protocolo_processo=normalizar_texto(linha["PROTOCOLO/PROCESSO"]) or "",
        auto_infracao=normalizar_texto(linha["AUTO DE INFRACAO"]) or "",
        data_vencimento=linha[COLUNA_DATA_NORMALIZADA] or "",
    )


def aplicar_resultado(
    df: pd.DataFrame,
    indice,
    status: str,
    mensagem: str,
    tentativas: int,
    observacao: str = "",
) -> None:
    df.at[indice, "STATUS_CADIN"] = status
    df.at[indice, "MENSAGEM"] = mensagem or ""
    df.at[indice, "TENTATIVAS"] = tentativas
    df.at[indice, "DATA_PROCESSAMENTO"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    df.at[indice, "OBSERVACAO"] = observacao or ""

