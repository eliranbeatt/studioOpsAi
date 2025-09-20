# NEWPLAN.md: A Strategic Pivot to an AI-Powered Personal Assistant

## 1. Project Vision & Goals

The project will be refocused to create a sophisticated, AI-powered personal assistant. The primary goal is to develop a chatbot that serves as a "second brain," capable of recalling past conversations and documents, and acting as an intelligent project planning partner.

The core mission is to solve a major pain point: the manual, time-consuming process of breaking down ideas into actionable project plans. The assistant will streamline this by transforming conversational input into structured tasks, which can then be visually edited and exported directly to a Trello board.

Supporting features, like vendor and material management, will be integrated to enrich the assistant's knowledge base, enabling it to generate more realistic and data-driven plans in the future.

## 2. Core Features & Requirements

### Functional Requirements

**FR1: Conversational AI & Memory**
- **FR1.1: Chat Interface:** A clean, intuitive, and responsive chat interface within the Next.js web application.
- **FR1.2: Conversation History:** All conversations with the AI must be saved and be retrievable.
- **FR1.3: Long-Term Memory:** The AI must have a mechanism to store and recall key information from conversations and uploaded documents (e.g., user preferences, project details, specific facts).
- **FR1.4: Retrieval-Augmented Generation (RAG):** The AI's responses must be informed by the user's specific knowledge base (history and documents), providing contextual and personalized answers.
- **FR1.5: Document Ingestion:** Users must be able to upload documents (e.g., PDFs, TXT, MD) to the system to expand the AI's knowledge base.

**FR2: AI-Powered Project Planning**
- **FR2.1: Idea-to-Plan Generation:** The AI must be able to take a high-level goal or idea from a conversation and break it down into a structured plan of tasks and sub-tasks.
- **FR2.2: Trello-Formatted Output:** The generated plan must be structured in a format compatible with Trello (e.g., Lists, Cards with descriptions).
- **FR2.3: Visual Plan Editor:** A new UI component in the web app that displays the generated plan in a visual, editable format (e.g., a tree or nested list).
- **FR2.4: Plan Refinement:** Users must be able to add, edit, delete, and reorder tasks and sub-tasks within the visual editor before exporting.

**FR3: Trello Integration**
- **FR3.1: Board Selection:** Users should be able to select an existing Trello board or specify a name for a new one.
- **FR3.2: One-Click Export:** A button ("Send to Trello") in the plan editor that sends the structured plan to the Trello API, creating the corresponding lists and cards on the selected board.
- **FR3.3: Authentication:** A secure mechanism to connect the user's Trello account using the API keys defined in the project configuration.

**FR4: Vendor & Material Management (MVP)**
- **FR4.1: Basic CRUD:** API endpoints and a simple UI for creating, reading, updating, and deleting vendor and material information (e.g., vendor name, contact, material name, price).
- **FR4.2: Data Accessibility:** The vendor and material data must be stored in the PostgreSQL database and be accessible to the AI's retrieval system.

### Non-Functional Requirements

- **NFR1: Usability:** The user interface for chat and planning must be intuitive and require minimal learning.
- **NFR2: Performance:** AI responses should be generated in a timely manner. The UI must remain responsive during AI processing.
- **NFR3: Scalability:** The architecture should handle a growing knowledge base and increasing user interaction without significant degradation in performance.
- **NFR4: Modularity:** The new features (Chat, Memory, Planning) should be built as distinct, loosely-coupled services to ensure maintainability.

## 3. Proposed System Design & Architecture

We will leverage the existing Next.js frontend, FastAPI backend, and PostgreSQL database. The new functionality will be built as new modules within this architecture.

![System Architecture Diagram](https://i.imgur.com/example.png)  *(Placeholder for a diagram showing the flow below)*

### Frontend (apps/web - Next.js)
1.  **Chat View (`/chat`):** A new route and component for the main conversational interface.
2.  **Plan Editor View (`/plan`):** A new route and component that takes a generated plan and renders it for visual editing. This will manage the state of the plan and provide the "Send to Trello" functionality.
3.  **API Client:** The frontend will communicate with the backend via RESTful API calls to the FastAPI server.

### Backend (apps/api - FastAPI)
The backend will house the core intelligence of the system.

1.  **Memory & Retrieval Service:**
    *   **Vector Store:** We will use the `pgvector` extension for PostgreSQL to store vector embeddings of documents and conversation snippets. This avoids adding a new database technology.
    *   **Embedding Model:** Use a sentence-transformer model to generate embeddings for all text ingested into the memory system.
    *   **RAG Pipeline:** When a user sends a message, the backend will first query the vector store for relevant context, then inject that context into the prompt sent to the LLM.

2.  **Chat Service:**
    *   A new set of API endpoints (`/chat`) to handle incoming messages.
    *   This service will orchestrate the RAG pipeline and call the LLM for response generation.
    *   It will also be responsible for saving conversations to the database.

3.  **Planning Service:**
    *   A new API endpoint (`/plan/generate`) that takes a conversational goal as input.
    *   This service will use a dedicated, structured prompt to instruct the LLM to break the goal down into a JSON object representing tasks and sub-tasks.

4.  **Trello Service (Enhancement of `apps/trello-mcp`):**
    *   Refactor or enhance the existing Trello-related code.
    *   A new endpoint (`/trello/export`) will receive the JSON plan from the frontend.
    *   This service will connect to the Trello API using the configured keys and create the board, lists, and cards.

5.  **Database (PostgreSQL with SQLAlchemy):**
    *   **New Tables:**
        *   `conversations`: To store chat history.
        *   `documents`: To store metadata about uploaded files.
        *   `memory_chunks`: To store text chunks and their vector embeddings for RAG.
        *   `vendors` & `materials`: For the vendor management feature.
    *   **Alembic Migrations:** All schema changes will be managed through new Alembic migration scripts.

## 4. Implementation Plan: Tasks & Sub-tasks

This plan breaks the work into logical epics.

### Epic 1: Foundational Setup & Memory System

*   **Task 1.1: Database Schema Update**
    *   Sub-task 1.1.1: Install and enable the `pgvector` extension in the PostgreSQL Docker container.
    *   Sub-task 1.1.2: Create Alembic migration scripts for the new tables: `conversations`, `documents`, `memory_chunks`, `vendors`, `materials`.
    *   Sub-task 1.1.3: Apply migrations to the development database.
*   **Task 1.2: Backend Memory Service**
    *   Sub-task 1.2.1: Implement SQLAlchemy models for the new tables.
    *   Sub-task 1.2.2: Create a `MemoryService` in the FastAPI backend to handle text embedding and storage in `memory_chunks`.
    *   Sub-task 1.2.3: Implement a document upload endpoint and service that splits files into chunks and uses `MemoryService` to store them.

### Epic 2: Conversational AI & Chat Interface

*   **Task 2.1: Backend Chat Service**
    *   Sub-task 2.1.1: Create API endpoints for sending/receiving chat messages.
    *   Sub-task 2.1.2: Implement the RAG pipeline: query vectors, construct prompt, call LLM.
    *   Sub-task 2.1.3: Implement conversation history storage.
*   **Task 2.2: Frontend Chat Interface**
    *   Sub-task 2.2.1: Create a new page and components for the chat interface in Next.js.
    *   Sub-task 2.2.2: Implement state management for the conversation.
    *   Sub-task 2.2.3: Connect the UI to the backend chat API endpoints.

### Epic 3: Project Planning & Visualization

*   **Task 3.1: Backend Planning Service**
    *   Sub-task 3.1.1: Develop a robust prompt for the LLM to generate a structured JSON plan from a user's goal.
    *   Sub-task 3.1.2: Create the `/plan/generate` endpoint that takes a goal and returns the structured JSON.
*   **Task 3.2: Frontend Plan Editor**
    *   Sub-task 3.2.1: Create a new page and components to render the plan JSON visually.
    *   Sub-task 3.2.2: Implement functionality to edit, add, delete, and reorder tasks in the UI.
    *   Sub-task 3.2.3: Add a button in the chat interface to trigger plan generation from the current conversation context.

### Epic 4: Trello Integration

*   **Task 4.1: Backend Trello Service**
    *   Sub-task 4.1.1: Review and refactor the existing `trello-mcp` app or create a new `TrelloService`.
    *   Sub-task 4.1.2: Implement the logic to take a plan JSON and create a board, lists, and cards via the Trello API.
    *   Sub-task 4.1.3: Create the `/trello/export` endpoint. ✅ Implemented and tested (apps/api/routers/trello.py; tests in apps/api/tests/integration/test_trello_export_api.py)
*   **Task 4.2: Frontend Trello Integration**
    *   Sub-task 4.2.1: Add UI elements for selecting a Trello board (or creating a new one).
    *   Sub-task 4.2.2: Wire the "Send to Trello" button in the plan editor to call the `/trello/export` backend endpoint.

## 5. Implementation Tracker

- Epic 0: Web Build Stabilization
  - Status: Done
  - Changes: Fixed Chat page missing state and closing tokens; refactored plan generation trigger; sanitized API client AbortController usage; corrected generic typing in `useApi`; removed stale `useApi().post` usage in pages; resolved build-breaking typos.
  - Validation: `apps/web` builds successfully (`npm run build`).

- Epic 4.1.3: Backend `/trello/export` endpoint
  - Status: Done (tested)
  - Tests: apps/api/tests/integration/test_trello_export_api.py; services tests updated; coverage >= 80%

- Epic 4.2.1-4.2.2: Frontend Trello integration
  - Status: Done (tested)
  - Changes: Added `trelloApi.exportPlan` in `apps/web/src/lib/api.ts`; added "Send to Trello" action in `PlanEditor`
  - Tests: Added unit test in `apps/web/src/components/PlanEditor.test.tsx`

- Epic 3.1.2: `/plans/generate` endpoint
  - Status: Done (tested)
  - Changes: Added `POST /plans/generate` in `apps/api/routers/plans.py` to produce structured JSON using pricing heuristics
  - Tests: `apps/api/tests/integration/test_plan_generate_api.py` (passes; API coverage still ≥ 80%)

- Epic 3.2.2: Plan editor enhancements
  - Status: Done (tested)
  - Changes: Added row reordering (Move up/down) in `apps/web/src/components/PlanEditor.tsx`
  - Tests: `apps/web/src/components/PlanEditor.test.tsx` updated to verify reorder

- Epic 2.1: Backend Chat Service
  - Status: Validated (tested)
  - Existing: `/chat/message` and `/chat/stream` endpoints integrate LLM + basic RAG/context
  - Tests: `apps/api/tests/integration/test_chat_api.py` patches context/RAG and asserts structured response and SSE stream

- Epic 3.2.3: Wire chat → plan generation
  - Status: Done (tested via unit harness)
  - Changes: Chat UI calls `POST /plans/generate`; Chat banner can trigger generation; passes result into `PlanEditor`
  - Files: `apps/web/src/components/Chat.tsx`, `apps/web/src/app/chat/page.tsx`, `apps/web/src/lib/api.ts`

### Epic 5: Vendor & Material Management (MVP)

*   **Task 5.1: Backend CRUD APIs**
    *   Sub-task 5.1.1: Create FastAPI routers and services for basic CRUD operations on the `vendors` and `materials` tables.
*   **Task 5.2: Frontend UI**
    *   Sub-task 5.2.1: Create a simple table-based UI for viewing and managing vendors and materials.
*   **Task 5.3: Integrate with Memory**
    *   Sub-task 5.3.1: Create a mechanism to periodically or manually ingest vendor/material data into the RAG system's vector store.
