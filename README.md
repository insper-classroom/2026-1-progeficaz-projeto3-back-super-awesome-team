# Projeto 3 Programação Eficaz ( BACKEND ) - Super Awesome Team

[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/) [![uv](https://img.shields.io/badge/uv-111111?style=for-the-badge&logo=uv&logoColor=white)](https://docs.astral.sh/uv/)

Este repositório contém o backend do Projeto 3 da disciplina de Programação Eficaz.

## Equipe

- Brenda Lima
- Mateus Ahn
- Miqueias Ayron
- Pedro Pereira
- Victor Costa

## Comandos GIT

- Listar `branchs` locais:

```bash
    git branch
```

- Criar nova `branch` localmente:

```bash
    git branch nome-da-branch
```

- Mudar para outra `branch`:

```bash
    git switch nome-da-outra-branch
```

- Criar `branch` e já mudar para a nova `branch`:

```bash
    git checkout -b nome-da-branch
```

- Deletar `branch` localmente:

```bash
    git branch -D nome-da-branch
```

- Deletar `branch` do repositório remoto ( github ):

```bash
    git push origin --delete nome-da-branch
```

- Verificar status de local changes:

```bash
    git status
```

- Escolher arquivos alterados que serão commitados ( adiciona à `Staging Area`):

```bash
    git add nome-do-arquivo1 nome-do-arquivo2 nome_do_arquivo3
```

- Adicionar Diretório ( Pasta ) à `Staging Area`:

```bash
    git add nome-da-pasta/
```

- Adicionar TODAS as alterações do diretório atual na `Staging Area`:

```bash
    git add .
```

- Adiconar arquivos por extensão à `Staging Area`:
  - Ex:

  ```bash
  git add *.css
  ```

  Adicona todos os arquivos CSS.

- Commita na `branch` atual ( Sobe para o Repositório Local )

```bash
    git commit -m 'nome-do-commit'
```

                        │
                        ▼

- Subir `branch` para o repositório remoto ( github ):

```bash
    git push -u origin nome-da-branch
```

## Instruções de sincronização e instalação de dependências

Usaremos o gerenciador de pacotes Python `uv`. Se você ainda não tem o `uv` na sua máquina, execute no terminal:

```shell
pip install uv
```

Ou, caso não tenha o Python configurado como variável de ambiente:

```shell
py -m pip install uv
```

Após a instalação, abra o terminal e execute, no diretório do projeto:

```shell
uv sync
```

- Isso vai criar um ambiente virtual com todas as dependências contidas no arquivo `uv.lock`.
- Você não precisa ativar o ambiente manualmente. Sempre que abrir o terminal, o ambiente será inicializado automaticamente.

Para instalar uma nova dependência, execute:

```shell
uv add nome-da-biblioteca
```

- A dependência instalada é automaticamente listada no `uv.lock`, então, quando você fizer um _commit_, isso sobe para o repositório remoto.
- Quando outro membro da equipe fizer _pull_, basta usar `uv sync` para sincronizar as dependências contidas no `uv.lock` com o ambiente virtual e tudo estará pronto.

Em caso de dúvida, clique nos ícones do topo para acessar as respectivas documentações.

## Configuracao do .env

```py
    MONGODB_URI=mongodb+srv://usuario:<senha>@project3.7pbdixa.mongodb.net/?appName=project3
    CLIENT_ID=placeholder
    CLIENT_SECRET=placeholder
    REFRESH_TOKEN=placeholder
```

## Subindo com o servidor gunicorn

- **desenvolvimento**: servidor single-thread, reload automático ao salvar, mensagens de erro detalhadas no browser ( mas roda síncrono )

```bash
    uv run flask --app wsgi:app run --debug
```

- **produção**: múltiplos workers, gevent, robusto, sem reload automático ( roda assíncrono )

```bash
    uv run gunicorn wsgi:app
```

## Modularização

### Fluxo da Requisição

![alt text](img/flask_request_flow.svg)

# Assincronismo no Flask

## Concorrência com Gevent

O gevent usa concorrência cooperativa — uma greenlet só cede o controle quando chega numa operação de I/O (query no banco, chamada HTTP, etc.), e só volta a executar quando essa operação retorna o resultado.

Então dentro de uma requisição, o código continua sequencial:

```py
existing = mongo['users'].find_one(...)  # cede o controle, MAS espera o resultado
if existing:                              # só executa depois do find_one retornar
    return None, {'error': '...'}
```

O gevent permite que outra requisição rode enquanto essa espera o banco, mas **nunca avança para a linha seguinte sem ter o resultado.**

O único lugar onde coisas rodam de forma verdadeiramente paralela é o `gevent.spawn` — que você usou explicitamente para o email, justamente porque ele não afeta a resposta.

O risco real existe entre **requisições diferentes** rodando concorrentemente — por exemplo, dois cadastros com o mesmo email passando no `find_one` ao mesmo tempo antes de qualquer um inserir. Mas isso é um problema de qualquer sistema concorrente, resolvido com índice único no MongoDB, não com controle de concorrência no código.

## Formatador Automático

Instale a extensão `ruff`

![alt text](img/ruff.png)
