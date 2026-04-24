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
```

## Rodando a Aplicação
```py
    uv run app.py
```

## Modularização

### Fluxo da Requisição
![alt text](img/flask_request_flow.svg)