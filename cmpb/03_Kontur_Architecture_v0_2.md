# Контур v0.2 — архитектура через Anthropic API

*Поверхностная архитектура без глубокого технического углубления. Цель: понять, где хранить данные, где использовать RAG, workflows, агентов, MCP, API и собственный код.*

## 1. TL;DR

Контур строится как **managed context system**:

```text
Connectors/API/MCP → Raw Evidence Store → Extracted Artifacts → Feature Memory → Context Compiler → Claude API → Validation/Redaction → PM Review
```

Claude не должен каждый раз заново читать всё через MCP. Его задача — анализ, извлечение смысла, формулировка статуса, объяснение рисков и ответы на сложные вопросы.

## 2. Главные компоненты

### 2.1. Connectors / API / MCP

Подключают источники:

- Asana;
- Slack;
- Google Docs / Google Drive;
- «Паспорт фичи»;
- AllBuilds;
- позже GitHub, Miro, Amplitude/AB.

**Правило:** для hot path лучше использовать managed connectors/API и локальное хранилище. MCP — для стандартизации tools и investigation mode, но не для того, чтобы Claude каждый раз с нуля обходил все системы.

### 2.2. Feature Registry

Карта фичи и её источников:

```text
feature_id
passport_id
asana_project_id
asana_root_task_id
gdoc_build_plan_id
slack_thread_ids
team_id
owner_pm
stage
```

Без Feature Registry система каждый раз будет тратить токены и tool calls на то, чтобы заново понять, где лежит фича.

### 2.3. Raw Evidence Store

Хранилище сырых источников:

```text
source_id
feature_id
source_type
source_url
raw_text_or_payload
created_at
updated_at
fetched_at
hash
permission_label
```

Это не «вся история навсегда». Это управляемый слой с retention, TTL, дедупликацией и архивированием.

### 2.4. Extracted Artifacts Store

Хранилище структурированного смысла:

```text
decision
open_question
risk_signal
miscommunication
priority_drift
blocker
scope_change
discrepancy
```

Artifacts — это то, что позволяет не перечитывать длинные треды каждый раз.

### 2.5. Feature Memory

Текущая рабочая память фичи:

```text
confirmed_decisions
candidate_decisions
open_questions
active_risks
recent_deltas
unknowns
stale_sources
coverage          # сколько источников видим и чего НЕ видим (см. 2.12)
last_status_summary
```

Feature Memory компактна и используется почти в каждом workflow.

### 2.6. Retrieval / RAG

RAG нужен, чтобы найти релевантные snippets из raw evidence и artifacts.

Важно: RAG не заменяет Feature Memory. Memory хранит уже известное состояние; RAG ищет supporting evidence или редкие факты.

### 2.7. Context Compiler

Собирает короткий context packet под задачу.

Пример для статус-апдейта:

```text
- правила формата;
- метрики из «Паспорта»;
- changes за 14 дней;
- confirmed decisions;
- open questions;
- active risks;
- source snippets;
- audience/redaction rules.
```

### 2.8. Claude API Layer

Используем Anthropic API в нескольких режимах:

- **direct Messages API** — когда context packet уже собран;
- **structured outputs** — когда нужен JSON: tasks, artifacts, risks;
- **tool use** — для ограниченного agent investigation;
- **prompt caching** — для стабильных инструкций и канона;
- **batch API** — для фоновой обработки и evals;
- **citations** — для grounded answers по переданным документам/snippets.

### 2.9. Workflow Runner

Запускает повторяемые процессы:

- feature state;
- risk scan;
- 2-week status update;
- Asana task scaffolding;
- simple Q&A.

Workflow Runner лучше делать своим кодом. Он отвечает за порядок шагов, retries, permissions, logs, PM approval.

### 2.10. Agent Investigation Mode

Ограниченный режим для vague вопросов:

```text
read-only tools
max tool calls
max token budget
no write actions
all claims with sources
```

Нужен для вопросов, где путь заранее неизвестен.

### 2.11. Discrepancy / Diff Engine

Отдельный first-class компонент, а не «попутная логика в промпте». Самые ценные флоу — это по сути **diff-операции**, не суммаризация:

```text
- status «что изменилось за 2 недели» = diff(state_now, state_2w_ago);
- risk «план vs коммуникация»         = diff(build_plan, slack/asana evidence);
- priority drift                      = diff(зафиксированный scope, обсуждаемый scope);
- supersession                        = diff(старый decision, новый decision по тому же объекту);
- miscommunication                    = diff(source_A understanding, source_B understanding).
```

Движок комбинирует:

```text
- deterministic compare (даты, owners, статусы, scope-поля — код, не LLM);
- semantic compare (Claude — для «об одном ли объекте речь» и «противоречат ли смыслы»);
- выход: discrepancy artifact (тип, два source_ids, confidence, нужно ли PM-подтверждение).
```

Это место дифференцированной ценности Контура против «просто саммаризатора»: не «вот что есть», а «вот где источники расходятся и где картина наверху лучше реальности».

### 2.12. Coverage Tracker

Считает и держит покрытие источников по фиче (см. `04`, Feature Memory → coverage). Отвечает на вопрос «чего система НЕ видит» и отдаёт это в каждый ответ:

```text
- linked_sources, by_type, last_ingested_at;
- known_blind_spots (неподключённые каналы, нечитаемые tabs, access_lost);
- completeness_hint: full / partial / thin.
```

Без него synthesis может быть уверенно неполным. Honesty про blind-spots — часть продукта, а не сноска.

## 3. Где что использовать

| Задача | Механизм |
|---|---|
| Прочитать метрики «Паспорта» | прямой API/БД |
| Прочитать Asana/Slack/GDocs | managed connector/API/MCP на ingestion |
| Хранить сырые источники | Raw Evidence Store |
| Хранить решения/риски/вопросы | Extracted Artifacts Store |
| Хранить текущее состояние фичи | Feature Memory |
| Искать релевантное | hybrid RAG/search |
| Собирать статус | workflow + Claude API |
| Ловить простые риски | rules + Claude explanation |
| Считать «что изменилось» / расхождения | Discrepancy/Diff Engine (2.11) |
| Знать, чего НЕ видим | Coverage Tracker (2.12) |
| Разбирать сложные противоречия | constrained agent |
| Заводить задачи | workflow + structured output + approval + Asana API |
| Не хранить конфиденциальное | source-level sensitivity (не инжестить) + permission enforcement; redaction на выходе — второй слой |
| Экономить токены | context packets + prompt caching + batch + model routing |

## 4. Почему не «просто агент через MCP»

Просто агент через MCP хорош для прототипа, но плох для production hot path:

- каждый запрос повторно читает много сырого текста;
- стоимость становится непредсказуемой;
- трудно понять, какие sources использовались;
- сложнее контролировать freshness;
- сложнее сделать redaction и access control;
- сложнее тестировать и улучшать качество.

Правильнее:

```text
MCP/API для controlled ingestion и investigation
+ локальная память фичи
+ Claude для анализа подготовленного context packet
```

## 5. Предпочтительный стек MVP

### Backend

- **TypeScript / Node.js** — логично с учётом твоего опыта и SDK для Slack/Asana/Google.
- Альтернатива: Python, если команда будет ближе к data/LLM tooling.

### Storage

- **Postgres** — canonical data, workflow runs, artifacts, feature memory.
- **JSONB** — source payloads и flexible metadata.
- **Postgres full-text search** — keyword search.
- **pgvector** — semantic search, если нужен vector retrieval.
- **Object storage** — если raw payloads станут большими.

### AI layer

- Anthropic Claude API.
- Voyage AI embeddings или другой embedding provider, потому что Anthropic не даёт собственную embedding-модель.
- Langfuse или аналог для tracing/evals/cost.

### Orchestration

- На MVP можно начать с собственного workflow runner.
- LangGraph уместен позже, если появятся сложные stateful workflows, human-in-the-loop и retry logic.

## 6. Минимальная MVP-схема БД

```text
features
feature_sources
raw_evidence
artifacts
feature_memory
workflow_runs
pm_feedback
eval_cases
```

### Permission enforcement — design constraint, не «потом»

`permission_label` несётся по всей цепочке `feature_sources → raw_evidence → artifacts → context packet` и проверяется на query time, а не только при ingestion. То есть synthesis для пользователя собирается **только из источников, которые этот пользователь имеет право видеть**; evidence из чужого приватного канала не подмешивается в ответ. Это надо заложить в схему и в Context Compiler с самого начала — ретрофитить permission-модель в готовую систему дорого и опасно (см. `07`, D8).

## 7. Модель оптимизации стоимости

Главные рычаги:

1. не отправлять raw context каждый раз;
2. хранить artifacts и feature memory;
3. использовать prompt caching для стабильных инструкций;
4. использовать batch для фоновой extraction/evals;
5. использовать дешёвую модель для extraction/classification;
6. использовать сильную модель только для synthesis/investigation;
7. не прогонять через LLM то, что может сделать код.

## 8. Термины

**Hot path** — частый пользовательский путь, например статус-апдейт или Q&A.

**Cold path / background path** — фоновая обработка: extraction, backfill, evals, обновление памяти.

**Hybrid search** — сочетание фильтров, keyword search и vector search.

**Source of truth** — источник, которому доверяем для конкретного типа фактов. Например, «Паспорт» для метрик, Slack/GDocs/Asana для raw evidence, PM-confirmed artifacts для операционного состояния.
