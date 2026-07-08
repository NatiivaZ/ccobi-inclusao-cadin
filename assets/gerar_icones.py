"""
Gera logo_antt.png (header) e logo_antt.ico (barra de tarefas / .exe).
Execute na pasta do projeto: python assets/gerar_icones.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

PASTA = Path(__file__).resolve().parent
PNG_HEADER = PASTA / "logo_antt.png"
ICO_APP = PASTA / "logo_antt.ico"

# Cabecalho da janela (lado direito)
HEADER_MAX_LARGURA = 96
HEADER_MAX_ALTURA = 40

# ICO: margem ao redor do logo (Explorer + barra de tarefas + .exe)
# ~22% = tamanho equilibrado; menor que isso fica "estourado"
ICO_MARGEM = 0.22

TAMANHOS_ICO = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]


def localizar_origem() -> Path:
    for nome in ("logo_antt_origem.png", "logo_antt.png", "logo_antt_source.png"):
        caminho = PASTA / nome
        if caminho.exists():
            return caminho
    raise SystemExit(
        f"Coloque a imagem de origem em {PASTA} (ex.: logo_antt_origem.png ou logo_antt.png)."
    )


def remover_fundo_preto(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if r <= 45 and g <= 45 and b <= 45:
                px[x, y] = (0, 0, 0, 0)
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    return img


def redimensionar_cabecalho(img: Image.Image) -> Image.Image:
    w, h = img.size
    escala = min(HEADER_MAX_LARGURA / w, HEADER_MAX_ALTURA / h, 1.0)
    nw = max(1, int(w * escala))
    nh = max(1, int(h * escala))
    return img.resize((nw, nh), Image.Resampling.LANCZOS)


def quadrado_contido(img: Image.Image, lado: int, margem: float) -> Image.Image:
    area = max(1, int(lado * (1 - 2 * margem)))
    w, h = img.size
    escala = min(area / w, area / h)
    nw, nh = max(1, int(w * escala)), max(1, int(h * escala))
    red = img.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    canvas.paste(red, ((lado - nw) // 2, (lado - nh) // 2), red)
    return canvas


def normalizar_transparencia(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 16:
                px[x, y] = (0, 0, 0, 0)
    return img


def salvar_ico(logo: Image.Image, destino: Path) -> None:
    """Master 256px; Pillow gera as demais resolucoes (padrao Windows)."""
    master = normalizar_transparencia(quadrado_contido(logo, 256, ICO_MARGEM))
    master.save(destino, format="ICO", sizes=TAMANHOS_ICO)


def main() -> None:
    origem = Image.open(localizar_origem())
    logo = remover_fundo_preto(origem)

    logo_header = redimensionar_cabecalho(logo)
    logo_header = normalizar_transparencia(logo_header)
    logo_header.save(PNG_HEADER, "PNG")

    salvar_ico(logo, ICO_APP)

    ico = Image.open(ICO_APP)
    frames = 0
    while True:
        try:
            ico.seek(frames)
            frames += 1
        except EOFError:
            break
    print(
        f"OK header={logo_header.size} "
        f"ico_frames={frames} margem={ICO_MARGEM:.0%} lados={sorted({t[0] for t in TAMANHOS_ICO})}"
    )


if __name__ == "__main__":
    main()
