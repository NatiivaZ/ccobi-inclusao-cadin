# Inclusao CADIN

Automacao desktop para incluir apontamentos individualmente no CADIN a partir de uma planilha.

## Como executar

1. Abra `iniciar.bat`.
2. Selecione a planilha de entrada.
3. Abra o Chrome na porta 9222 ou deixe a automacao abrir o Chrome dedicado automaticamente.
4. Informe CPF/senha gov.br ou use o login manual.
5. Deixe `Modo teste` desmarcado para fazer inclusao real.
6. Clique em `Iniciar` e confirme a inclusao real.

A automacao usa nodriver conectado ao Chrome na porta 9222. Depois do login, ela abre `Inicio`, acessa `Incluir Cadastro` e processa a planilha.

Se quiser validar sem enviar, marque `Modo teste` para preencher e clicar em `Limpar`.

Para testar sem usar cookies do perfil persistente, marque `Abrir Chrome em guia anonima (teste)`.

A sessao do CADIN e renovada automaticamente a cada 30 minutos, em ponto seguro entre uma linha e outra.

## Como gerar o .exe

1. No computador de desenvolvimento, abra `build_exe.bat`.
2. Aguarde a instalacao das dependencias e o build do PyInstaller.
3. O executavel sera gerado em `dist\InclusaoCADIN.exe`.
4. Envie esse `.exe` para o colega.

O colega nao precisa instalar Python nem bibliotecas Python. Ele precisa apenas ter Google Chrome instalado. Ao executar, o app cria as pastas `logs` e `resultados` ao lado do `.exe`.

Se o Chrome na porta 9222 nao estiver aberto, a automacao tenta abrir um Chrome dedicado automaticamente usando a pasta `chrome_profile`.

## Colunas obrigatorias

- `CPF/CNPJ`
- `PROTOCOLO/PROCESSO`
- `AUTO DE INFRACAO`
- `DATA DE VENCIMENTO`

## Resultado

O resultado e salvo automaticamente na pasta `resultados`. Durante o lote, a automacao mantem um checkpoint rapido em CSV e, ao final, gera a planilha Excel formatada com status, mensagem, tentativas, data de processamento e observacao.


---

## Aviso legal (portfólio)

Código **proprietário** — Todos os direitos reservados.  
Publicado apenas para avaliação por recrutadores. **Uso em produção, redistribuição ou comercialização são proibidos** sem autorização escrita. Ver `LICENSE` e `NOTICE.md`.

Este repositório **não** contém dados pessoais reais (LGPD) nem credenciais. Amostras devem ser fictícias.


---

## Versao portfolio (codigo operacional omitido)

Este repositorio publico e uma **demonstracao de portfolio**.

- Estrutura, interfaces e documentacao: visiveis para recrutadores
- Fluxos criticos de integracao / automacao / regras sensiveis: **omitidos de proposito**
- Chamadas as partes omitidas levantam ``PortfolioOmittedError`` / ``OMITIDO PARA PORTFOLIO``
- Uso em producao, redistribuicao ou copia da logica operacional: **proibido** (ver ``LICENSE``)

O codigo operacional completo permanece apenas no ambiente do autor.
