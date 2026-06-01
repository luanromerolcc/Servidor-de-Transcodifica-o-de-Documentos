# Servidor de Transcodificação de Documentos

Servidor UDP de conversão de arquivos, suporte a múltiplas sessões simultâneas e envio fragmentado de dados.

---

## Visão Geral

Este projeto implementa um sistema cliente-servidor via **UDP** para conversão de arquivos entre formatos suportados.

### Arquitetura

```
client.py  ──UDP──▶  server.py  ──▶  converters.py
```

- **`client.py`** — envia o arquivo fragmentado e recebe o resultado convertido
- **`server.py`** — recebe os dados, gerencia sessões e executa a conversão em threads paralelas
- **`converters.py`** — define as funções de conversão e o mapa de formatos suportados

---

## Pré-requisitos

- Python **3.8+**
- pip

``` bash
sudo apt install python3 python3-pip
```

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/luanromerolcc/Servidor-de-Transcodifica-o-de-Documentos
cd Servidor-de-Transcodifica-o-de-Documentos/
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install markdown
```

## Como Usar

### Passo 1 — Inicie o servidor

Abra um terminal e execute:

```bash
python server.py
```

Você verá a mensagem de confirmação:

```
[INFO] Servidor UDP rodando em 0.0.0.0:9000
```

O servidor ficará aguardando conexões na porta **9000**.

---

### Passo 2 — Execute o cliente

Em outro terminal, envie um arquivo para conversão:

```bash
python client.py <arquivo> <formato_entrada> <formato_saida>
```

#### Exemplos

**Converter Markdown para HTML:**
```bash
python client.py README.md md html
```

**Converter HTML para texto puro:**
```bash
python client.py index.html html text
```

**Converter texto para maiúsculas:**
```bash
python client.py notas.txt txt upper
```

O resultado da conversão será impresso diretamente no terminal.

---

## Formatos Suportados

| `formato_entrada` | `formato_saida` | Descrição |
|:-----------------:|:---------------:|-----------|
| `md`              | `html`          | Markdown → HTML |
| `html`            | `text`          | HTML → texto puro (strip de tags) |
| `txt`             | `upper`         | Texto → maiúsculas |

---
