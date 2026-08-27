# Toca do Espanhol — Plano de Migração e Reestruturação

Documento de referência para guiar o trabalho no Claude Code, dentro da pasta
`~/Downloads/toca-do-espanhol/`. Cole o "Prompt de início" (no final) na primeira
mensagem do Claude Code para começar.

---

## 0. Contexto atual → contexto alvo

| Aspecto | Atual | Alvo |
|---|---|---|
| Banco | SQLite | PostgreSQL |
| Apps | monolítico | `users`, `auth`, `tables`, `orders`, `queue`, `kitchen`, `cash_register`, `audit`, `dashboard` |
| Auth | básica | JWT (SimpleJWT) com roles |
| Frontend | React+Vite+Tailwind (base pronta) | mesma stack + Router, Axios, RHF, Toastify, ícones |
| Infra | manual | Docker Compose (backend + frontend + postgres) |

O código existente (models, admin, credenciais) não será descartado — será
migrado e reorganizado, não reescrito do zero.

---

## 1. Ordem de execução recomendada

Construir em fatias verticais funcionais, não "todo o backend depois todo o
frontend". Cada fase termina com algo testável.

**Fase 1 — Fundação**
1. Configurar PostgreSQL local (ou via Docker) e apontar `settings.py` com `dotenv`.
2. Criar modelo de usuário customizado (`users`) com `role` (enum dos 7 perfis).
3. Configurar SimpleJWT: login, refresh, logout, `/api/auth/me`.
4. Rodar `makemigrations`/`migrate` no Postgres, criar seed do admin
   (`admin@toca.com` / `123456` / `ADM_MAXIMO`).
5. Testar login via Insomnia/Postman antes de tocar no frontend.

**Fase 2 — Operação básica**
6. App `tables`: CRUD de mesas + status.
7. App `orders`: `Order` + `OrderItem`, endpoints de criação/listagem/itens.
8. Permissões por role (`IsAdmin`, `IsGarcom`, `IsCozinha` etc. em `permissions.py`).
9. App `audit`: middleware/signal simples que loga ações-chave.

**Fase 3 — Setores**
10. App `kitchen` (serve cozinha e parrilla via filtro de `sector`): fila de
    pedidos pendentes, mudança de status.
11. App `queue`: senhas, chamada, painel público.
12. App `cash_register`: abertura/fechamento de caixa, `Payment`.

**Fase 4 — Consolidação**
13. App `dashboard`: agregações (vendas do dia, mês, produtos mais vendidos).
14. Frontend: telas na mesma ordem (Login → Mesas/Pedidos → Cozinha/Parrilla →
    Caixa → Fila → Dashboard → Usuários).
15. Docker Compose juntando os três serviços.
16. README + coleção Postman/Insomnia atualizada.

---

## 2. Estrutura de pastas alvo (backend)

```
backend/
  config/                 # settings, urls raiz, wsgi/asgi
  apps/
    users/
    auth/
    tables/
    orders/
    queue/
    kitchen/
    cash_register/
    audit/
    dashboard/
  each app com:
    models.py
    serializers.py
    views.py
    services.py           # regra de negócio fora da view
    permissions.py
    urls.py
    admin.py
```

## 3. Variáveis de ambiente (`.env`)

```
DEBUG=True
SECRET_KEY=...
DATABASE_URL=postgres://toca:toca@localhost:5432/toca_espanhol
JWT_ACCESS_LIFETIME_MIN=15
JWT_REFRESH_LIFETIME_DAYS=7
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

## 4. Pontos de atenção herdados de sessões anteriores

- Usar `.zip` em vez de `.tar` se precisar empacotar algo entre máquinas.
- **Não** incluir `psycopg2-binary` sem revisar — agora que o alvo é
  Postgres de verdade, ele é necessário (antes era descartado por causa do SQLite).
- Ativar o virtualenv sempre a partir da pasta `backend/` antes de rodar comandos Django.
- `/` retornando 404 é esperado; API fica em `/api/`, admin em `/admin/`.

---

## Prompt de início para o Claude Code

```
Estou na pasta do projeto Toca do Espanhol (Django + React). Preciso migrar
o backend de SQLite para PostgreSQL e reestruturar em apps separados
(users, auth, tables, orders, queue, kitchen, cash_register, audit,
dashboard), seguindo o plano em PLANO_TOCA_DO_ESPANHOL.md.

Comece pela Fase 1: configuração do Postgres via .env, modelo de usuário
customizado com roles, e autenticação JWT com SimpleJWT (login, refresh,
logout, /api/auth/me). Antes de gerar código, me mostre a estrutura de
pastas proposta para eu validar.
```
