# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a full-stack Croatian events platform ("Kružna Karta Hrvatska") built as a monorepo with:
- **Frontend**: React 18 + TypeScript + Tailwind CSS + Vite
- **Backend**: FastAPI + Python + PostgreSQL + Redis
- **Infrastructure**: Docker, Nginx, monitoring with Uptime Kuma

The platform aggregates events from multiple Croatian websites through web scraping and provides a unified booking experience with integrated payments.

## Key Architecture

### Monorepo Structure
- `frontend/` - React TypeScript application
- `backend/` - FastAPI Python application  
- `docker/` - Docker configurations and infrastructure

### Technology Stack
- **Frontend**: React 18, TypeScript, Tailwind CSS, React Router, React Query, Leaflet maps
- **Backend**: FastAPI, SQLAlchemy, Alembic, Celery, Redis, Playwright (web scraping)
- **Database**: PostgreSQL with Redis for caching/sessions
- **Deployment**: Docker Compose, Nginx reverse proxy

## Development Commands

The project uses a comprehensive Makefile with 40+ commands. Key commands:

### Quick Start
```bash
make setup           # Initial project setup
make dev            # Start full development environment
make frontend-dev   # Frontend only
make backend-dev    # Backend only
```

### Daily Development
```bash
make logs           # View all logs
make frontend-logs  # Frontend logs only
make backend-logs   # Backend logs only
make db-shell      # PostgreSQL shell access
make redis-shell   # Redis CLI access
```

### Code Quality
```bash
make lint          # Run all linters
make test          # Run all tests
make frontend-test # Frontend tests only
make backend-test  # Backend tests with coverage
```

### Database Management
```bash
make migrate       # Run database migrations
make migration     # Create new migration
make db-reset     # Reset database with sample data
```

## Key Business Logic

### Web Scraping System
- Scrapes 8+ Croatian event websites using Playwright
- Located in `backend/app/scraping/`
- Handles multiple site structures and formats
- Stores events with deduplication logic

### Event Management
- Events stored with venue, pricing, and scheduling data
- Booking system with seat selection where applicable
- Integration with payment processors
- Platform commission of 5% applied to all bookings

### Multi-language Support
- Croatian (hr) and English (en) supported
- Translation files in `frontend/src/locales/`
- Backend API serves localized content

## Development Guidelines

### Frontend Patterns
- Components in `frontend/src/components/`
- Pages in `frontend/src/pages/`
- Hooks for API calls using React Query
- Tailwind for styling with custom theme
- TypeScript strict mode enabled

### Backend Patterns
- FastAPI with dependency injection
- SQLAlchemy ORM with Alembic migrations
- Pydantic models for API serialization
- Celery for background tasks (scraping, emails)
- JWT authentication with Redis sessions

### Environment Setup
- Frontend env: `frontend/.env` (API_URL, maps config)
- Backend env: `backend/.env` (database, Redis, secrets)
- Docker env: `docker/.env` (ports, volumes)

### Testing
- Frontend: Vitest + React Testing Library
- Backend: pytest with fixtures and database isolation
- Run `make test` for full test suite

### Database Migrations
- Use `make migration name="description"` to create migrations
- Always review generated migrations before applying
- Use `make migrate` to apply pending migrations

## Common Tasks

### Adding New Event Source
1. Create scraper in `backend/app/scraping/scrapers/`
2. Add URL patterns to scraper registry
3. Test with `make scrape-test`
4. Update documentation

### API Development
- Add routes in `backend/app/api/routes/`
- Use dependency injection for database access
- Add Pydantic schemas in `backend/app/schemas/`
- Follow existing patterns for error handling

### Frontend Components
- Use TypeScript interfaces for props
- Follow existing component structure
- Use React Query for data fetching
- Implement responsive design with Tailwind

## Infrastructure

### Local Development
- All services run via Docker Compose
- Frontend dev server proxies API calls
- Hot reload enabled for both frontend and backend
- PostgreSQL and Redis run in containers

### Production Deployment
- Docker Compose with production configurations
- Nginx reverse proxy handles routing
- SSL termination and static file serving
- Environment-specific configurations

## Troubleshooting

### Common Issues
- Port conflicts: Check `docker/.env` for port assignments
- Database connection: Ensure PostgreSQL container is running
- Migration failures: Check migration files and database state
- Scraping issues: Verify Playwright browser installation

### Useful Debug Commands
```bash
make shell          # Backend Python shell
make frontend-shell # Frontend container shell
make db-logs       # Database logs
make nginx-logs    # Nginx logs
```


# Rules for Backend Development

- **MUST** use appropriate AI libraries and avoid deprecated dependencies
- **MUST** put all the imports at the top of the file, and group them by standard library, third-party libraries, and local imports
- **MUST** include static code analysis using tools like pylint, flake8, or mypy
- **MUST** implement robust error handling, input validation, and fallback mechanisms for failures
- **MUST** implement proper data validation and preprocessing pipelines
- **MUST** choose efficient data structures (e.g. pandas DataFrames for tabular data, NumPy/PyTorch tensors for numerical data) to optimize AI workload performance and memory use.
- **MUST** follow PEP 8 style guidelines strictly
- **MUST** use type hints for all function parameters and return values
- **MUST** implement proper docstrings using Google or NumPy style
- **MUST** keep functions small and focused (single responsibility principle)
- **MUST** implement proper logging with appropriate log levels
- **MUST** implement efficient data loading and preprocessing
- **MUST** implement proper memory management for large datasets
- **MUST** avoid unnecessary computational overhead
- **MUST** profile AI code performance and identify bottlenecks

- **MUST** use **Pydantic** for data validation and serialization, which provides type safety, automatic validation, and easy serialization to JSON.
- **MUST** use **Pydantic Settings** which provide type-safe configuration management with automatic validation. Benefits: Type safety with automatic validation, Environment variable support with prefixes, Default values and required fields.
- **MUST** use **Pydantic BaseModel** for data validation and serialization, which provides type safety, automatic validation, and easy serialization to JSON.
- **MUST** use **Pydantic Field** for defining fields with validation rules, which provides type safety, automatic validation, and easy serialization to JSON.
- **MUST** use **Pydantic Config** for configuring Pydantic models, which provides type safety, automatic validation, and easy serialization to JSON.
- **MUST** use **Pydantic BaseSettings** for managing application settings, which provides type-safe configuration management with automatic validation.
- MUST use Pydantic for data validation and configuration (e.g. BaseModel for schemas, Field for validation, BaseSettings for config). Pydantic ensures type safety, automatic validation, environment variable support, and easy JSON serialization.

- **SHOULD** retrieve every configuration value exclusively through the CONFIG object defined in **components.py** to ensure type-safe, centralized access and avoid direct environment or file lookups.
- **SHOULD** implement proper **GPU memory management** for deep learning models
- **SHOULD** use meaningful **variable** and **function names**
- **SHOULD** use appropriate **optimization techniques** for AI workloads
- **SHOULD** provide **meaningful error messages** for debugging
- **SHOULD** log errors with sufficient context for troubleshooting
- **SHOULD** implement proper model **serialization** and **deserialization**
- **SHOULD** create **reproducible development environments** using Docker
- **SHOULD** implement proper model **monitoring** and **logging** when explicitly needed
- **SHOULD** consider **parallel processing** and **distributed computing** when appropriate

- **SUGGEST** proper **caching** **mechanisms** for **expensive** operations

- **FOLLOW** the RESTAPI code structuring examples

- **DO NOT** use DEAFULT calls like: legal_bert_config = **CONFIG.get**("models", {}).get("legal_bert", {})
- **DO NOT** use **load_dotenv**, loading env file inside of the project, we always get the env file from the config file
- **DO NOT** use **emojis** in any part of the code
- **DO NOT** use **print** statements in the code, we use **logging** instead
- **DO NOT** put any code inside of the **__init__.py** file, unless there is a specific reason to do so
- **DO NOT** use **global** variables, we use **class variables**
- **DO NOT** use **magic methods** like `__call__`, `__getattr__`, `__setattr__`, etc. unless there is a specific reason to do so
- **DO NOT** use **f-strings** in the code, we use **format** method instead
- **DO NOT** use relative imports in the code, we use absolute imports instead
- **DO NOT** import os, unless there is a specific reason to do so
- **DO NOT** "git add" or "git commit", just propose the commit message after a big update
- **DO NOT** hardcode credentials, API keys, passwords, or sensitive information in any code
- **DO NOT** create code that compiles but contains subtle logical errors
- **DO NOT** generate functions that handle most cases but fail on edge cases
- **DO NOT** produce code with off-by-one errors or boundary condition mistakes
- **DO NOT** create algorithms that work for simple inputs but fail for complex ones
- **DO NOT** generate code that lacks proper error checking or validation for edge cases.
- **DO NOT** create functions that miss essential validation steps
- **DO NOT** generate code based on assumptions about unclear specifications
- **DO NOT** create conditional logic that misaligns with stated requirements
- **DO NOT** implement features that contradict the intended business logic
- **DO NOT** generate code that solves a different problem than what was asked
- **DO NOT** suggest inappropriate data structures for the given use case
- **DO NOT** generate regex patterns that match different strings than intended
- **DO NOT** create sorting or searching algorithms with incorrect complexity
- **DO NOT** use synchronous operations where asynchronous ones are required
- **DO NOT** continue generating "fixes" after 3 failed attempts without changing approach
- **DO NOT** keep apologizing and making similar mistakes repeatedly
- **DO NOT** generate increasingly complex solutions when simple ones would work
- **DO NOT** create functions that are impossible to unit test
- **DO NOT** generate code that requires specific system states to function
- **DO NOT** create tightly coupled code that cannot be tested in isolation
- **DO NOT** create complex algorithms without explaining the approach
- **DO NOT** generate code with magic numbers or unexplained constants
- **DO NOT** create functions with unclear parameter requirements
- **DO NOT** generate code that future developers cannot understand or modify
- **DO NOT** create functions that violate the single responsibility principle
- **DO NOT** generate code with poor variable naming conventions
- **DO NOT** create tight coupling between unrelated components
- **DO NOT** present generated code as definitively correct without caveats
- **DO NOT** ignore potential edge cases or limitations in the solution
- **DO NOT** generate code without acknowledging areas of uncertainty
- **DO NOT** claim the code is production-ready without proper testing
- **DO NOT** generate code with unnecessary deeply nested conditions, loops or inefficient algorithms
- **DO NOT** create memory leaks or resource management issues
- **DO NOT** generate code that blocks threads unnecessarily
- **DO NOT** create database queries that could cause performance problems at scale
- **DO NOT** create code that uses excessive memory for simple operations
- **DO NOT** generate solutions that require unnecessary external dependencies
- **DO NOT** create code that makes redundant network calls or file operations
- **DO NOT** generate **CPU-intensive** operations without considering alternatives
- **DO NOT** generate code that **assumes** specific **libraries** without mentioning them
- **DO NOT** create functions that **depend** on **undefined** variables or imports
- **DO NOT** generate code that **conflicts** with existing codebase patterns
- **DO NOT** ignore **version compatibility issues** with dependencies
- **DO NOT** create **new bugs** while trying to fix existing ones

- **AUDIO ALERT**: Run `afplay /System/Library/Sounds/Glass.aiff` at the end of tasks or when input is needed

---

# FRONTEND RULES — React · Vite · TailwindCSS · TypeScript (v1.0)

> **Scope**  
> These rules govern all web-frontend code in this repository. They apply to React 18+, Vite 5+, TailwindCSS 3+, and TypeScript 5+.  
> Animations must follow the **GSAP (Tween / Timeline)** guidelines below; when other motion libraries are used, apply comparable constraints.

---

## 1 · MUST

### 1.1 Coding Standards & Style
- **MUST** enable **`"strict": true`** and all `noUnchecked` flags in `tsconfig.json`.
- **MUST** use **ESLint** with `@typescript-eslint` + **Prettier**; run in pre-commit and CI.  
- **MUST** write components as **function components** with **React hooks**; avoid legacy `class` components.
- **MUST** name files and symbols by intent:  
  - Components → `PascalCase.tsx` (`UserCard.tsx`)  
  - Hooks → `useDescriptiveThing.ts`  
  - Utilities → `camelCase.ts`
- **MUST** colocate component, test, and style files under a feature folder (`/features/user/UserCard.tsx`).
- **MUST** export a single default component per file; named exports for non-components.
- **MUST** add **JSDoc/TSDoc** to every public prop, hook parameter, and return value.

### 1.2 State & Data Flow
- **MUST** favour **React context + hooks** for cross-cutting state; prefer **Zustand** or **Redux Toolkit** only for complex, shared state.
- **MUST** treat server data as immutable; normalise and cache via **React Query** (TanStack Query) or SWR.
- **MUST** handle errors and loading states for every async request.

### 1.3 TailwindCSS
- **MUST** enable `content` paths correctly in `tailwind.config.js` to purge unused styles.
- **MUST** compose utility classes with **clsx / classnames** or Tailwind `@apply`; avoid long inline class strings in JSX.
- **MUST** extend the design system in `theme.extend` (colors, spacing, typography); **never** modify Tailwind core.

### 1.4 Accessibility
- **MUST** follow **WCAG 2.1 AA**: semantic HTML, keyboard navigation, focus outlines.
- **MUST** respect **`prefers-reduced-motion`** by disabling or simplifying animations.
- **MUST** add `aria-*` attributes and labels to interactive elements.

### 1.5 Animations & Motion
- **MUST** implement complex motion with **GSAP** timelines; wrap GSAP calls inside `useLayoutEffect` or custom hooks.
- **MUST** store animation targets via `useRef`; **never** query DOM with `document.querySelector`.
- **MUST** keep each animation < 200 ms for micro-interactions, < 500 ms for page-level transitions.
- **MUST** batch or debounce scroll/resize-based animations (GSAP `ScrollTrigger` or `requestAnimationFrame`).
- **MUST** pause / kill animations on component unmount (`ctx.revert()` or `gsap.killTweensOf`).

### 1.6 Build & Tooling
- **MUST** use **Vite** with `react`, `tsconfig-paths`, and `tailwindcss` plugins.
- **MUST** split vendor and common chunks via Vite’s `build.rollupOptions` → `manualChunks`.
- **MUST** enable HTTPS and HMR in local dev (`vite --https --open`).

### 1.7 Testing & QA
- **MUST** test UI logic with **React Testing Library** and hooks with **@testing-library/react-hooks**.
- **MUST** reach ≥ 90 % statement coverage on critical features.
- **MUST** run **axe-core** accessibility tests in CI.

---

## 2 · SHOULD

### 2.1 Performance & Optimisation
- **SHOULD** memoise heavy components (`React.memo`, `useMemo`, `useCallback`).
- **SHOULD** lazy-load routes (`React.lazy` + `Suspense`) and large assets (`import.meta.glob` in Vite).
- **SHOULD** enable **`react-refresh`** and **`vite-plugin-inspect`** for dev-time diagnostics.
- **SHOULD** compress SVG/PNG and serve modern formats (WebP/AVIF).

### 2.2 Advanced Motion
- **SHOULD** use **Framer Motion** or **@react-spring/web** for simple UI transitions if GSAP overhead is unjustified.
- **SHOULD** centralise timing and easing in a `motionTokens.ts` file.
- **SHOULD** coordinate page transitions with **React Router** `useNavigationType` + GSAP `context`.

### 2.3 Design & DX
- **SHOULD** abstract repetitive Tailwind patterns into **@/components/ui** primitives (Button, Card).
- **SHOULD** document components in **Storybook** with interactive controls.

### 2.4 Security
- **SHOULD** enable **Content Security Policy (CSP)** headers with `vite-plugin-csp`.
- **SHOULD** sanitise all user-generated HTML (use `dompurify`).

---

## 3 · SUGGEST

- Add **pre-commit** hooks (lint, prettier, test, type-check).
- Provide a **VS Code dev-container** with Node LTS, pnpm, and Cypress pre-installed.
- Integrate **Cypress** for E2E tests and visual regression (Percy, Loki, or Playwright-trace).

---

## 4 · DO NOT

### 4.1 Code Smells
- **DO NOT** store non-serialisable objects in React state.
- **DO NOT** mutate props or context.
- **DO NOT** dispatch Redux actions inside render.

### 4.2 Performance
- **DO NOT** trigger layout-thrashing animations; batch DOM reads/writes.
- **DO NOT** mount heavy GSAP timelines eagerly; lazy-initialise in the viewport.

### 4.3 Style
- **DO NOT** write plain CSS/Sass; use Tailwind utilities or `@apply`.
- **DO NOT** override Tailwind base styles in component files.

### 4.4 Security
- **DO NOT** interpolate raw user input into HTML without sanitising.
- **DO NOT** commit `.env` or secret keys.

### 4.5 Version Control
- **DO NOT** commit compiled `dist/` or `.turbo/` artefacts.
- **DO NOT** auto-run `git add` / `git commit`; output proposed messages only.

---

## 5 · AUDIO ALERT
Play a chime when long‐running front-end build or test tasks finish:  
```bash
afplay /System/Library/Sounds/Glass.aiff
```

