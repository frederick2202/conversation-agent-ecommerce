# Lumen — E-Commerce de Eletrônicos com Agente Conversacional (IA)

Plataforma full-stack de e-commerce de produtos eletrônicos (**Lumen**) integrada a um agente conversacional inteligente alimentado pela **Google Gemini API**, com busca semântica via **RAG (`pgvector`)**, **Tool Calling (`LangGraph`)** e respostas em tempo real via **Server-Sent Events (SSE)**.

O projeto foi concebido seguindo rigorosamente a arquitetura em camadas **`Controller → Service → Repository`**, princípios **SOLID**, Clean Code e diretrizes de Engenharia de Usabilidade e Interface Homem-Máquina (**ISO 9241-11**).

---

## Sumário

1. [Visão Geral e Funcionalidades (Requisitos Funcionais)](#1-visão-geral-e-funcionalidades)
2. [Stack Tecnológica](#2-stack-tecnológica)
3. [Arquitetura do Sistema e Fluxo do Agente](#3-arquitetura-do-sistema-e-fluxo-do-agente)
4. [Ferramentas do Agente de IA e Protocolo SSE](#4-ferramentas-do-agente-de-ia-e-protocolo-sse)
5. [Princípios de IHM e Engenharia de Usabilidade](#5-princípios-de-ihm-e-engenharia-de-usabilidade)
6. [Estrutura do Monorepo](#6-estrutura-do-monorepo)
7. [Principais Endpoints da API](#7-principais-endpoints-da-api)
8. [Como Executar com Docker Compose (Recomendado)](#8-como-executar-com-docker-compose-recomendado)
9. [Como Executar Localmente (Sem Docker)](#9-como-executar-localmente-sem-docker)
10. [Testes Unitários (Pytest)](#10-testes-unitários-pytest)

---

## 1. Visão Geral e Funcionalidades

### RF01 — Consulta de Detalhes e Estoque via Chat
* Reconhece consultas por **nome** ou **código SKU** (ex.: `LMN-NB-001`).
* Retorna nome, preço, descrição resumida, variações e disponibilidade de estoque **em tempo real** consultando o PostgreSQL (sem alucinação de dados).
* Caso o produto exato não seja encontrado, executa busca semântica no `pgvector` e sugere alternativas similares de forma amigável.

### RF02 — Adição ao Carrinho Diretamente pelo Chat
* Verifica automaticamente se o produto exige variações obrigatórias (ex.: cor, voltagem, armazenamento, tipo de switch).
* Renderiza **botões clicáveis de seleção de variação** dentro do próprio painel do chat, evitando erros de digitação.
* Após incluir o item, exibe confirmação com resumo atualizado (itens, quantidades e subtotal), sincroniza o contador do carrinho no cabeçalho e disponibiliza um **botão direto para o Checkout (`/checkout`)**.

### RF03 — Cadastro e Exibição de Avaliações de Produtos
* Permite avaliar apenas produtos existentes na base de dados.
* Valida estritamente na camada `Service` e no banco (`CHECK CONSTRAINT`) que a nota seja um número inteiro no intervalo de **1 a 5**.
* O comentário é opcional; após o envio, a avaliação é persistida e exibida imediatamente com feedback visual.

### RF04 — Sincronização de Catálogo e FAQs com o Agente (Painel Admin)
* Disponibiliza interface administrativa em `/admin` e endpoints REST de CRUD para **FAQs** (trocas, frete, garantia, pagamento) e **Produtos**.
* Sempre que um produto ou FAQ é criado ou editado, o backend gera e atualiza automaticamente o respectivo vetor (*embedding*) de 1536 dimensões no `pgvector`, refletindo as alterações imediatamente no pipeline de RAG do agente.

---

## 2. Stack Tecnológica

### Backend & Orquestração de IA
* **Linguagem:** Python 3.11+
* **Framework Web:** FastAPI (assíncrono, com `StreamingResponse` SSE para streaming do chat)
* **Agente e LLM:** LangChain + LangGraph + `langchain-google-genai` (**Google Gemini API** — chat e embeddings)
* **Validação e ORM:** Pydantic v2 + SQLAlchemy 2.0 (assíncrono com `asyncpg`)
* **Testes:** Pytest + `pytest-asyncio`

### Banco de Dados, RAG e Memória
* **Banco Relacional e Vetorial:** PostgreSQL 16 + extensão `pgvector` (busca por distância de cosseno em vetores de 1536 dimensões)
* **Memória de Conversa:** Persistência do histórico de mensagens e ações de UI por `session_id` em tabela dedicada (`chat_messages`)

### Frontend (E-Commerce + Chat + Admin)
* **Linguagem e Framework:** TypeScript (tipagem estrita) + Next.js 14 (App Router / React 18)
* **Estilização e Componentes:** Tailwind CSS + componentes estilo shadcn/ui + Lucide Icons

---

## 3. Arquitetura do Sistema e Fluxo do Agente

O backend aplica separação estrita de responsabilidades em três camadas:

```text
[Next.js Frontend + Chat Widget]
        │  REST JSON + SSE Streaming
        ▼
┌─────────────────────────────────────────┐
│  Controllers (Routers FastAPI)          │ ──► Apenas roteamento, Pydantic e status HTTP
└───────────────────┬─────────────────────┘
                    ▼
┌─────────────────────────────────────────┐
│  Services (Regras de Negócio & RAG)     │ ──► Validações, estoque, notas 1..5, embeddings
└────────▲──────────────────────┬─────────┘
         │                      ▼
         │         ┌─────────────────────────────────────────┐
         │         │  Repositories (SQLAlchemy + pgvector)   │ ──► Queries SQL e busca vetorial
         │         └────────────────────┬────────────────────┘
         │                              ▼
         │                 [PostgreSQL 16 + pgvector]
         │
┌────────┴────────────────────────────────┐
│  Agente LangGraph (Gemini + Tools)      │ ──► Ferramentas chamam EXCLUSIVAMENTE os Services
└─────────────────────────────────────────┘
```

* **Controller (`app/controllers/`):** Não contém lógica de negócio; apenas recebe a requisição, delega ao `Service` e devolve a resposta padronizada.
* **Service (`app/services/`):** Centraliza regras de domínio (ex.: impedir estoque negativo, validar nota `1..5`, reindexar embeddings após criação/edição) e lança exceções de domínio tratadas globalmente em `app/core/exceptions.py`.
* **Repository (`app/repositories/`):** Encapsula todas as consultas SQLAlchemy assíncronas e operações de distância de cosseno do `pgvector`.

---

## 4. Ferramentas do Agente de IA e Protocolo SSE

O grafo do LangGraph (`app/agent/graph.py`) conecta o modelo Gemini a 4 ferramentas definidas em `app/agent/tools.py`:

| Ferramenta | Finalidade |
| :--- | :--- |
| `buscar_produto` | Consulta nome, SKU, preço, resumo, variações e estoque real no banco. Gera botões clicáveis de variações em estoque. |
| `sugerir_similares` | Executa busca vetorial (`pgvector`) para recomendar produtos similares quando o termo pedido não existe no catálogo. |
| `adicionar_ao_carrinho` | Valida variações obrigatórias e estoque; adiciona o item ao carrinho da sessão e emite card de resumo com link para `/checkout`. |
| `consultar_faq` | Recupera políticas atualizadas de troca, frete, garantia e pagamento via RAG no `pgvector`. |

### Eventos de Streaming SSE (`POST /api/v1/chat/stream`)
* `event: status` — Feedback imediato enquanto o agente executa uma ferramenta (ex.: `"Consultando buscar_produto..."`).
* `event: token` — Tokens de texto gerados em tempo real pelo Gemini.
* `event: ui_actions` — Payloads estruturados (`SELECT_VARIANT` ou `CART_UPDATED`) renderizados como botões interativos no chat.
* `event: done` — Sinaliza o encerramento do stream.

---

## 5. Princípios de IHM e Engenharia de Usabilidade

A interface segue as metas da **ISO 9241-11** (*Eficácia, Eficiência e Satisfação*):
* **Feedback Imediato:** Indicadores de digitação/consulta no chat, skeletons de carregamento no catálogo e notificações *toast* após cada ação.
* **Prevenção de Erros:** Seletor visual de 1 a 5 estrelas (impede notas inválidas), variações sem estoque desabilitadas visualmente e botões clicáveis de variação no chat.
* **Controle do Usuário e Liberdade:** Alteração rápida de quantidades/remoção no drawer do carrinho, botão para limpar/reiniciar a conversa com a IA e modais de confirmação antes de ações irreversíveis (finalizar pedido ou excluir FAQ/produto).
* **Baixa Carga Cognitiva (Lei de Hick e Lei de Fitts):** Sugestões rápidas enxutas no início do chat, busca central destacada no topo e botões principais (Carrinho, Checkout e abertura do Chat) com alvos confortáveis e previsíveis.

---

## 6. Estrutura do Monorepo

```text
lumen-ecommerce/
├── docker-compose.yml
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── pytest.ini
│   ├── .env.example
│   ├── app/
│   │   ├── main.py
│   │   ├── core/            # config.py, database.py, exceptions.py
│   │   ├── models/          # entities.py (Product, Variant, Review, Cart, Faq, ChatMessage)
│   │   ├── schemas/         # Schemas Pydantic v2
│   │   ├── repositories/    # Queries SQLAlchemy Async + pgvector
│   │   ├── services/        # Regras de negócio, EmbeddingService (Gemini) e ChatService
│   │   ├── agent/           # graph.py (LangGraph + Gemini) e tools.py
│   │   ├── controllers/     # Routers FastAPI
│   │   └── scripts/         # seed.py (popula produtos e FAQs com embeddings)
│   └── tests/
│       └── test_services.py # Testes unitários da camada Service
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tailwind.config.ts
    └── src/
        ├── app/             # page.tsx (Loja), checkout/page.tsx, admin/page.tsx
        ├── components/      # Sidebar, TopHeader, HeroBento, ProductCard, Modal, CartDrawer, LumenChatWidget
        ├── context/         # StoreContext.tsx (Sessão, Carrinho e Toasts)
        ├── lib/             # api.ts e utils.ts
        └── types/           # Tipagem TypeScript estrita
```

---

## 7. Principais Endpoints da API

A documentação interativa completa (Swagger / OpenAPI) fica disponível em `http://localhost:8000/docs`.

| Recurso | Método e Rota | Descrição |
| :--- | :--- | :--- |
| **Saúde** | `GET /health` | Verifica status da API |
| **Produtos** | `GET /api/v1/products` | Lista catálogo com filtros `?category=` e `?search=` |
| **Produtos** | `POST /api/v1/products` | Cadastra produto e indexa embedding no `pgvector` |
| **Produtos** | `PATCH /api/v1/products/{id}` | Atualiza produto e reindexa embedding automaticamente |
| **Produtos** | `DELETE /api/v1/products/{id}` | Remove produto do catálogo |
| **Avaliações** | `GET /api/v1/products/{id}/reviews` | Lista avaliações de um produto |
| **Avaliações** | `POST /api/v1/products/{id}/reviews` | Registra avaliação (nota obrigatória `1..5`, comentário opcional) |
| **Carrinho** | `GET /api/v1/cart/{session_id}` | Retorna itens, quantidades e subtotal da sessão |
| **Carrinho** | `POST /api/v1/cart/{session_id}/items` | Adiciona variação ao carrinho validando estoque |
| **Carrinho** | `PATCH /api/v1/cart/{session_id}/items/{item_id}` | Atualiza quantidade ou remove item (`quantity: 0`) |
| **Checkout** | `POST /api/v1/cart/{session_id}/checkout` | Finaliza pedido e limpa o carrinho da sessão |
| **FAQs (RAG)** | `GET / POST / PATCH / DELETE /api/v1/faqs` | CRUD completo com reindexação automática no `pgvector` |
| **Agente IA** | `POST /api/v1/chat/stream` | Envia mensagem e recebe resposta via SSE |
| **Agente IA** | `GET / DELETE /api/v1/chat/sessions/{session_id}` | Consulta ou limpa histórico da conversa |

---

## 8. Como Executar com Docker Compose (Recomendado)

### Pré-requisitos
* **Docker Desktop** (com Docker Compose v2+)
* Uma chave de API gratuita do **Google AI Studio**: acesse [aistudio.google.com/apikey](https://aistudio.google.com/apikey) e crie sua `GEMINI_API_KEY`.

### Passo 1 — Configurar variáveis de ambiente
Na raiz do projeto, crie o arquivo `backend/.env` a partir do exemplo:

```bash
cp backend/.env.example backend/.env
```

Edite `backend/.env` e preencha sua chave do Gemini:

```env
DATABASE_URL=postgresql+asyncpg://lumen:lumen_secret@db:5432/lumen_db
GEMINI_API_KEY=sua-chave-do-google-ai-studio
GEMINI_CHAT_MODEL=gemini-3.5-flash-lite
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
CORS_ORIGINS=http://localhost:3000
```

> **Fallback de resiliência:** Caso a `GEMINI_API_KEY` não seja informada ou ocorra erro de cota durante o seed, o `EmbeddingService` utiliza um vetor local determinístico de 1536 dimensões para que o catálogo e a loja continuem funcionando sem derrubar o backend.

### Passo 2 — Subir toda a stack
```bash
docker compose up --build
```

Ao iniciar pela primeira vez, o backend cria automaticamente a extensão `vector` no PostgreSQL, gera as tabelas relacionais e executa `python -m app.scripts.seed` para popular 6 eletrônicos (com variações e estoque) e 3 FAQs iniciais já vetorizados.

### Passo 3 — Acessar a aplicação
* **Loja Lumen + Chat IA:** `http://localhost:3000`
* **Painel Admin (Catálogo & FAQs RAG):** `http://localhost:3000/admin`
* **Checkout:** `http://localhost:3000/checkout`
* **Documentação Swagger / OpenAPI:** `http://localhost:8000/docs`

> **Dica:** Se você subir o projeto primeiro sem chave e depois adicionar sua `GEMINI_API_KEY`, execute `docker compose down -v && docker compose up --build` para recriar o banco e gerar os embeddings reais do Gemini no seed inicial.

---

## 9. Como Executar Localmente (Sem Docker)

Caso prefira rodar Backend e Frontend diretamente na sua máquina (exigindo um PostgreSQL 16 com extensão `pgvector` acessível):

### Backend
```bash
cd backend
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows (PowerShell): .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python -m app.scripts.seed
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 10. Testes Unitários (Pytest)

Os testes em `backend/tests/test_services.py` validam as principais regras de negócio da camada `Service` de forma isolada com mocks assíncronos (validação de notas 1–5, bloqueio de produto inexistente, comentário opcional, validação de estoque no carrinho, busca semântica de similares e reindexação automática de embeddings em FAQs).

### Executando dentro do Docker
```bash
docker compose exec backend pytest -v
```

### Executando localmente
```bash
cd backend
python -m pytest -v
```