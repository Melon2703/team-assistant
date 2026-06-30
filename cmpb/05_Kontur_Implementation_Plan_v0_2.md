# Контур v0.2 — план реализации

*Цель документа: декомпозировать реализацию так, чтобы не раздувать MVP и при этом заложить правильную архитектуру экономии токенов.*

## 1. Принцип реализации

Идём вертикальным срезом:

```text
одна команда FT1
→ одна фича
→ одна карта источников
→ одна память фичи
→ пять основных функций
→ измерение пользы и стоимости
```

Не строим сразу платформу для всех команд.

## 1.5. Этап −1 — дешёвая валидация ценности до build, 2 недели

### Зачем

Managed-инфра (raw store, artifacts, freshness, governance) — это инженеро-месяцы и $43–72k (см. `06`). Глупо строить её до того, как доказана ценность и acceptance. А лёгкая версия Контура **уже существует**: текущий Cursor + MCP (Asana/Slack/Google) + skills + canon. На ней можно проверить tier-1 ценность и acceptance дёшево.

### Что сделать

```text
1. взять 1 фичу FT1, вручную привязать её источники;
2. прогнать 5 функций «руками» через текущий Cursor + MCP сетап;
3. замерить: gross-время до/после, realization factor, acceptance/edit-distance черновиков,
   частоту и severity реально пойманных рисков/miscom;
4. зафиксировать, какие флоу текущий сетап НЕ закрывает
   (обычно: status за 2 недели и dedup памяти — туда целить первый «настоящий» компонент).
```

### Гейт (решение «строить managed-систему / нет»)

```text
acceptance черновиков ≥ 0.6 (иначе экономики нет ни на каком масштабе, см. 06);
есть хотя бы 1 полезный пойманный риск/miscom;
понятно, какие дельты ценности НЕ закрываются дешёвым MCP-подходом;
есть базовые числа для economics-модели.
```

Если гейт не пройден — managed-инфру не строим, дорабатываем дешёвый сетап.

## 2. Этап 0 — рамка и доступы, 1–2 недели

### Цель

Снять блокеры до кода.

### Что сделать

1. Утвердить позиционирование: Контур = операционный контекст, не замена «Паспорта».
2. Определить владельца продукта и мандат.
3. Получить сервисные доступы или понять путь к ним.
4. Проверить доступность данных:
   - Passport DB/API/export;
   - Asana API;
   - Slack API / curated thread links;
   - Google Docs/Drive API;
   - AllBuilds, если нужен.
5. Выбрать первую фичу FT1.
6. Утвердить privacy/redaction baseline.
7. Утвердить экономические assumptions для пилота.

### Гейт

```text
есть source access;
есть первая фича;
есть владелец;
понятна граница с «Паспортом»;
понятно, что можно читать в Slack/GDocs/Asana;
governance закрыт как design constraint, НЕ как открытый вопрос (см. 07, D8):
  - что можно хранить в text snapshots, что нельзя вообще;
  - как несём permission_label и enforce на query time;
  - что делаем с личными DM;
  - где физически хранятся данные.
```

Governance здесь — блокер, а не «решим по ходу»: это новый агрегированный sensitive-стор, ретрофит permission-модели дорог. Без закрытого governance первый байт в Raw Evidence Store не пишем.

## 3. Этап 1 — data foundation, 2–4 недели

### Цель

Создать минимальный слой данных, чтобы Claude не ходил каждый раз по MCP.

> Оценка 2–4 недели, а не 1–2: основная работа здесь — **ingestion** (auth, rate limits, schema drift у 4 источников) и **permission_label propagation**. В v0.2 это недооценивалось как «попутно»; по факту это половина этапа.

### Deliverables

1. `features` / Feature Registry.
2. `feature_sources` / карта источников + `permission_label` на каждом.
3. `raw_evidence` / первые snapshots.
4. Ingestion для (закладывать как отдельную строку трудозатрат):
   - Passport metrics;
   - Asana root/project;
   - Google Build Plan;
   - curated Slack threads.
5. Hash/dedupe.
6. Freshness metadata + базовый propagation (source changed → mark dirty, см. `04`).
7. Coverage Tracker (linked_sources, blind_spots, completeness_hint).

### Гейт

```text
по одной фиче можно увидеть все источники;
сырые evidence-записи сохранены;
повторный запуск не дублирует данные;
понятно, какие источники stale/missing;
система честно показывает coverage и blind-spots по фиче.
```

## 4. Этап 2 — artifacts + feature memory, 2–3 недели

### Цель

Превратить сырой контекст в компактную память фичи. **Это make-or-break этап:** вся ценность течёт через качество extraction. Шумный экстрактор = поток кандидатов на триаж, который дороже чтения треда.

### Deliverables

1. Artifact extraction prompt/schema.
2. Structured outputs для:
   - decisions;
   - open questions;
   - risk signals;
   - miscommunications;
   - priority drift;
   - action items.
3. Таблица `artifacts` (+ поля `canonical_key`, `merged_source_ids`, `supersedes`, `superseded_by`).
4. Confidence threshold: low-confidence кандидаты не спамят PM (см. `04`).
5. Dedup / entity resolution / supersession артефактов (см. `04`).
6. PM confirmation flow.
7. Feature Memory builder (включая coverage).
8. Eval cases на extraction с **числовым таргетом**.

### Гейт

```text
из Slack/GDocs/Asana извлекаются полезные artifacts;
extraction precision на eval set ≥ целевого порога (откалибровать, напр. ≥0.8),
  чтобы PM не тонул в ложных кандидатах;
один decision из 3 источников = один artifact, а не три дубля;
PM может подтвердить/отклонить;
Feature Memory собирается без ручного копирования;
есть source references.
```

## 5. Этап 3 — пять основных функций, 2–3 недели

### 5.1. Состояние фичи

Workflow:

```text
load memory → retrieve relevant evidence → Claude synthesis → source check
```

### 5.2. Риски / open questions / miscoms

Workflow:

```text
rules scan + discrepancy/diff engine → retrieval → Claude explanation → PM confirmation
```

Diff-движок (см. `03`, 2.11) ловит расхождения план↔коммуникация и priority drift как сравнение, не как саммари.

### 5.3. Статус за 2 недели

Workflow:

```text
load deltas → update artifacts → compile packet → Claude draft → validation → redaction → PM review
```

### 5.4. Asana task scaffolding

Workflow:

```text
read Build Plan + ТЗ → compare existing Asana tasks → Claude structured task draft → PM preview → approved write to Asana
```

### 5.5. Вопрос по фиче

Router:

```text
simple factual → direct read / memory
semantic → RAG + Claude
vague investigation → constrained agent
write intent → workflow + approval
```

### Гейт

```text
все 5 функций работают на одной фиче;
PM видит экономию времени;
claims имеют sources;
write actions идут только через approval.
```

## 6. Этап 4 — экономия и качество, параллельно

### Что включить с первого дня

1. Workflow runs ledger:
   - tokens;
   - latency;
   - model;
   - prompt version;
   - sources used;
   - PM feedback;
   - accepted/edited/rejected.
2. Cost dashboard.
3. Eval suite:
   - factuality;
   - citation coverage;
   - stale context;
   - redaction;
   - usefulness;
   - task draft quality.
4. Prompt caching для stable prefixes.
5. Batch API для background extraction/evals.
6. Model routing:
   - cheaper model for extraction/classification;
   - stronger model for final synthesis/investigation.

## 7. Этап 5 — повторяемость, 4–6 недель

### Цель

Проверить, что это работает не только у автора.

### Что сделать

1. Добавить 2–3 добровольных PM.
2. Настроить team-specific canon.
3. Добавить isolation по командам.
4. Расширить curated Slack intake.
5. Настроить более широкую RAG-индексацию.
6. Собрать сравнение economics до/после.

### Гейт

```text
есть weekly pull без мандата;
есть принятие черновиков;
стоимость на PM/фичу понятна;
есть хотя бы один полезный риск или miscom;
нет redaction incidents.
```

## 8. Что отложить

- полный workspace Slack index;
- full knowledge graph;
- autonomous write-agent;
- local LLM platform;
- event sourcing всех источников;
- outcome/Amplitude/AB до доказанной PM-пользы;
- top-management dashboard до доверия команд.
