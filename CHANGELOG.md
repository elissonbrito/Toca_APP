# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
versionamento conforme [SemVer](https://semver.org/lang/pt-BR/).

## [2.0.0] - 2026-08-27

Primeiro release publicado no repositório. Reescrita completa a partir do
protótipo inicial (v1, fase local, sem versionamento). Não há caminho de
migração automática de dados a partir da v1.

### Adicionado
- Backend Django 5 + DRF + PostgreSQL, organizado em 11 apps.
- Autenticação JWT (SimpleJWT): login, refresh, logout com blacklist, `/api/auth/me`.
- Modelo de usuário customizado com 7 perfis (roles) e permissões por perfil.
- Mesas, Pedidos (comanda + itens), Cozinha/Parrilla (fila por setor), Fila de
  senhas com painel público, Caixa (abertura/fechamento + pagamentos), Dashboard
  de indicadores, Auditoria.
- **Cardápio** com classificação fiscal completa (Simples Nacional): origem, NCM,
  CEST, CFOP, CSOSN, CST/alíquota de PIS e COFINS, unidade, GTIN.
- **Conferência fiscal** do catálogo (validação de formato e completude).
- **NFC-e (modelo 65, layout 4.00)**: chave de acesso (44 díg. + DV mód-11),
  geração de XML, QR Code, e cliente SEFAZ plugável (assinatura/transmissão
  ativam ao cadastrar certificado A1 + CSC).
- Snapshot fiscal congelado no item do pedido no momento da venda.
- Frontend React + Vite + Tailwind com todas as telas.
- `render.yaml` (deploy no Render: Postgres + backend + frontend estático).
- Coleção Insomnia/Postman e documentação da API no README.

### Notas
- Requer `ALTER ROLE <db_user> CREATEDB;` para rodar a suíte de testes.
- Transmissão real à SEFAZ depende de certificado A1, IE e CSC do estabelecimento.

## [1.0.0]

Protótipo inicial, desenvolvido localmente e nunca publicado em repositório.
