# Lumen — E-Commerce de Eletrônicos com Agente de IA

Plataforma full-stack de e-commerce de produtos eletrônicos (**Lumen**) integrada a um agente conversacional inteligente com **RAG (`pgvector`)**, **Tool Calling (`LangGraph`)** e **streaming SSE (`FastAPI`)**, construída com arquitetura em camadas estrita (`Controller -> Service -> Repository`) e diretrizes de usabilidade da **ISO 9241-11**.

## Stack Tecnológica
- **Backend & IA:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, LangChain, LangGraph, OpenAI API.
- **Banco de Dados & RAG:** PostgreSQL 16 + extensão `pgvector` (busca vetorial por distância de cosseno + persistência de memória de chat por sessão).
- **Frontend:** Next.js 14 (App Router), TypeScript estrito, Tailwind CSS, componentes estilo shadcn/ui e Lucide Icons.

## Funcionalidades Implementadas
- **RF01 — Consulta de Produtos e Estoque via Chat:** Busca em tempo real por nome ou SKU (`buscar_produto`). Caso não encontrado, sugere itens similares via busca semântica no `pgvector` (`sugerir_similares`).
- **RF02 — Adicionar ao Carrinho via Chat:** Valida variações obrigatórias (cor, voltagem, armazenamento, switch), renderiza botões clicáveis no chat, atualiza o carrinho no banco e exibe botão direto para `/checkout`.
- **RF03 — Avaliações de Produtos:** Validação estrita de existência do produto e nota inteira entre `1` e `5`, comentário opcional e seletor visual de estrelas para prevenção de erros.
- **RF04 — Sincronização de Catálogo e FAQs (Painel Admin `/admin`):** CRUD completo de FAQs e Produtos com reindexação automática de embeddings no `pgvector` imediatamente após criação ou edição.

## Como Executar Localmente (Docker Compose)

### 1. Configurar variáveis de ambiente
```bash
cp backend/.env.example backend/.env
```
Edite `backend/.env` e adicione sua `OPENAI_API_KEY`.

### 2. Subir PostgreSQL (`pgvector`), Backend e Frontend
```bash
docker compose up --build
```
Ao iniciar, o backend cria automaticamente a extensão `vector`, as tabelas relacionais e executa `python -m app.scripts.seed` com eletrônicos e FAQs iniciais vetorizados.

### 3. Acessar os serviços
- **Loja Lumen + Chat IA:** http://localhost:3000
- **Painel Admin (Catálogo & FAQs RAG):** http://localhost:3000/admin
- **Checkout:** http://localhost:3000/checkout
- **Documentação Swagger / OpenAPI:** http://localhost:8000/docs

## Como Executar os Testes Unitários (Pytest)
Com o Docker rodando:
```bash
docker compose exec backend pytest -v
```
Ou localmente em ambiente virtual Python:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -v
```
