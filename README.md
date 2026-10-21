# Fin-Tracker

Sistema de controle financeiro pessoal: registre receitas e despesas, organize por categorias e acompanhe tudo num dashboard.

> **Esta é a primeira versão do projeto.** Funciona de ponta a ponta, mas ainda tem bastante coisa para evoluir.

## Funcionalidades

- Cadastro e login com JWT (senhas com bcrypt)
- Categorias de receita/despesa com cor personalizada (6 categorias padrão criadas no cadastro)
- Lançamento e exclusão de transações
- Dashboard com saldo total, gráfico por categoria e resumo mensal
- Perfil do usuário: nome, senha e avatar
- Painel de administração para gerenciar usuários e papéis
- Tema claro/escuro

## Stack

- **Backend:** Python, FastAPI, MongoDB (Motor)
- **Frontend:** React 18, Tailwind CSS, shadcn/ui, Chart.js

## Como rodar

Pré-requisitos: Python 3.11+, Node 18+ e um MongoDB rodando.

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```

Crie `backend/.env`:

```env
MONGO_URL=mongodb://127.0.0.1:27017/fintracker
DB_NAME=fintracker
CORS_ORIGINS=http://localhost:3000
JWT_SECRET=troque-por-uma-chave-aleatoria
```

```bash
uvicorn server:app --reload --port 8000
```

### Frontend

Crie `frontend/.env`:

```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

```bash
cd frontend
npm install
npm start
```

Acesse http://localhost:3000.

### Primeiro administrador

Não há rota para criar o primeiro admin. Cadastre um usuário pelo app e promova-o direto no Mongo:

```js
db.users.updateOne({ email: "seu@email.com" }, { $set: { role: "admin" } })
```

## Próximos passos

- Editar transações e categorias
- Filtros por período no dashboard
- Exportação de dados (CSV)
- Testes automatizados
