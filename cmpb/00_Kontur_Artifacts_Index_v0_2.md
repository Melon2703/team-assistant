# Контур v0.2 — индекс артефактов

*Версия: 0.2. Цель: собрать рабочий пакет документов для обсуждения реализации Контура через Anthropic API.*

## Что такое Контур

**Контур** — операционный AI-слой вокруг фичи. Он собирает данные из Asana, Slack, Google Docs, «Паспорта фичи» и других источников, превращает их в проверяемый контекст и помогает PM в пяти задачах:

1. собрать состояние фичи на текущий момент;
2. подсветить риски, незакрытые вопросы, мискомы, неправильное понимание или смещение приоритетов;
3. сгенерировать статус-апдейт за последние 2 недели;
4. завести задачи в Asana на основе Плана Билдов, ТЗ и дополнительного контекста;
5. ответить на конкретный вопрос по фиче.

## Главная архитектурная ставка

Не строим «Claude-агента, который каждый раз сам заново ходит по MCP во все системы». Строим управляемую систему:

```text
источники → сырые evidence-записи → извлечённые артефакты → память фичи → context packet → Claude API → проверка → PM review
```

Claude используется там, где нужна смысловая работа: понять обсуждение, выделить риск, сформулировать статус, объяснить противоречие. Код используется там, где нужна точность, права доступа, свежесть, дедупликация, хранение, валидация и запуск workflow.

## Артефакты в пакете

1. `01_Kontur_PRD_v0_2.md` — обновлённый PRD с уточнённым набором функций.
2. `02_Kontur_Functional_Flows_v0_2.md` — подробные флоу: что видит пользователь и что происходит внутри.
3. `03_Kontur_Architecture_v0_2.md` — архитектура на понятном уровне: где API, где workflows, где агент, где MCP, где RAG.
4. `04_Kontur_Data_Model_and_Freshness_v0_2.md` — как хранить данные, зачем Raw Evidence Store, что такое Extracted Artifacts Store, как следить за актуальностью.
5. `05_Kontur_Implementation_Plan_v0_2.md` — план реализации с декомпозицией по этапам и гейтами.
6. `06_Kontur_Economics_Model_v0_2.md` — **ревизия**: честная модель с discount-факторами, COGS (build + maintenance) и break-even по числу PM. Деньги от сэкономленных часов — вторичный слой, главный кейс — предотвращённые риски и acceptance.
7. `07_Kontur_Decision_Log_and_Open_Questions_v0_2.md` — решения (включая D8–D12: governance, coverage, dedup/supersession, Phase −1, acceptance-метрика) и вопросы к закрытию.
8. `Kontur_Economics_Model_v0_2.xlsx` — редактируемая модель экономики (структуру брать из ревизованного `06`: inputs → discount → COGS → break-even; файла пока нет в папке).

## Короткий словарь

**Raw Evidence** — сырой первичный материал: Slack-тред, комментарий в Asana, секция Google Doc, запись из «Паспорта». Это не вывод модели, а исходная запись с ссылкой и временем получения.

**Extracted Artifact** — структурированный смысл, извлечённый из raw evidence: решение, риск, открытый вопрос, блокер, изменение scope, миском, расхождение.

**Feature Memory** — текущая рабочая память фичи: подтверждённые решения, открытые вопросы, активные риски, последние изменения, неизвестные места.

**Context Packet** — короткий пакет контекста под конкретную задачу, который отправляется в Claude. Например, для статус-апдейта туда попадают метрики, изменения за 2 недели, решения, вопросы, риски и правила формата.

**Workflow** — заранее заданный процесс из шагов. Например: собрать источники → обновить артефакты → собрать context packet → вызвать Claude → проверить → отдать PM.

**Agent / агентный режим** — режим, где модель сама выбирает, какие read-only tools вызвать и в каком порядке. Нужен для vague investigation-задач, но не для всех сценариев.

**RAG** — retrieval-слой: поиск релевантных источников или артефактов по запросу. В Контуре RAG не заменяет память фичи, а дополняет её.

**MCP** — протокол подключения AI-приложений к tools и источникам данных. В Контуре MCP полезен как слой коннекторов и для investigation-mode, но не должен быть единственным способом работы горячих workflow.

**Coverage / Blind-spots** — какие источники система видит по фиче и какие точно НЕ видит. First-class поле Feature Memory и обязательная строка в каждом ответе. Честность про непокрытое ценнее самого synthesis.

**Discrepancy / Diff Engine** — компонент, который считает расхождения (план↔коммуникация, было↔стало, source_A↔source_B), а не суммаризирует. Здесь дифференцированная ценность Контура.

**Phase −1** — дешёвая валидация ценности на текущем Cursor + MCP + skills сетапе до инвестиции в managed-инфру. Гейт к build: acceptance черновиков ≥ 0.6.

**COGS** — полная стоимость владения: one-time build (eng-months) + recurring maintenance + API. Учитывается в `06`; без неё окупаемость переоценена.

## Основные источники и референсы

- Anthropic — Claude API pricing: https://platform.claude.com/docs/en/about-claude/pricing
- Anthropic — prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Anthropic — batch processing: https://platform.claude.com/docs/en/build-with-claude/batch-processing
- Anthropic — tool use: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- Anthropic — effective context engineering: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic — building effective agents: https://www.anthropic.com/research/building-effective-agents
- MCP introduction: https://modelcontextprotocol.io/docs/getting-started/intro
- PostgreSQL full-text search: https://www.postgresql.org/docs/current/textsearch.html
- pgvector: https://github.com/pgvector/pgvector
- Langfuse observability: https://langfuse.com/docs/observability/overview
