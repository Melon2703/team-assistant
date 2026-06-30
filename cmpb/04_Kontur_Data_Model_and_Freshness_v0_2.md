# Контур v0.2 — модель данных и актуальность

*Цель документа: снять вопросы про Raw Evidence Store, Extracted Artifacts Store, раздувание хранения и свежесть данных.*

## 1. Почему не достаточно RAG

RAG помогает найти релевантные куски текста. Но Контур должен не только искать, а поддерживать рабочее состояние фичи:

```text
какие решения подтверждены;
какие вопросы открыты;
какие риски активны;
где есть расхождение между планом и коммуникацией;
что изменилось за последние 2 недели.
```

Поэтому нужен не только RAG, а 4 слоя:

```text
Raw Evidence Store
→ Extracted Artifacts Store
→ Feature Memory
→ Retrieval / RAG Index
```

## 2. Raw Evidence Store

### Определение

**Raw Evidence Store** — хранилище сырых первичных источников с metadata.

Примеры:

- Slack thread;
- Asana task/comment;
- Google Doc section;
- Passport metric snapshot;
- AllBuilds status;
- GitHub signal later.

### Зачем он нужен

1. Не ходить в MCP/API каждый раз.
2. Иметь trace: откуда взялся вывод.
3. Делать дельты: что изменилось с прошлого запуска.
4. Переизвлекать artifacts новым prompt/model.
5. Строить evals и разбирать ошибки.
6. Обеспечить citations/source references.

### Не раздует ли хранилище?

Скорее всего, нет, если хранить текст и metadata разумно. Основная стоимость в такой системе обычно не storage, а повторная LLM-обработка большого сырого контекста.

Но Raw Evidence Store нельзя делать бесконтрольным. Нужны правила:

```text
- dedupe по source_url + hash;
- хранить только allowlisted sources;
- не индексировать весь Slack workspace на MVP;
- начинать с curated Slack threads;
- хранить old versions только там, где важна история;
- делать retention policies;
- архивировать старый raw в object storage;
- оставлять artifacts и source references в hot storage.
```

### Sensitivity на уровне источника, а не redaction на выходе

Raw Evidence Store — это новый агрегированный sensitive-стор: он собирает cross-channel контекст в одном месте и может обойти per-channel ACL. Пытаться чистить чувствительное regex'ом на выходе — слабо: перефразированный web-payments / A/B holdout / HR-сигнал regex не поймает.

Правильный порядок — **prevention > cleanup**:

```text
1. sensitivity классифицируется на уровне источника при привязке (channel/doc/project);
2. чувствительные источники не инжестятся вообще (не попадают в raw store);
3. permission_label несётся от source → raw_evidence → artifact → context packet;
4. enforcement на query time: что пользователь может прочитать как фичу,
   то и видит в evidence; чужой приватный канал не подмешивается в synthesis;
5. Claude-redaction на выходе остаётся как второй слой, не первый.
```

Это design constraint, который должен быть закрыт **до** первого байта в хранилище (см. `07`, D8).

## 3. Предлагаемая retention-политика

| Тип данных | Hot storage | Archive | Комментарий |
|---|---:|---:|---|
| Passport metrics snapshots | 12 месяцев | 24+ месяцев | лёгкие данные, важны для истории |
| Asana task metadata | 12 месяцев | 24+ месяцев | нужна история статусов и owners |
| Asana comments | 6–12 месяцев | 24 месяца | можно хранить text + source_url |
| Google Doc exported text | current + major versions | 24 месяца | не хранить каждую мелкую правку вечно |
| Slack curated threads | 6–12 месяцев | 24 месяца | только привязанные к фиче |
| Extracted artifacts | пока фича активна + 12 месяцев | 24+ месяцев | компактные и ценные |
| Feature Memory | current only + history | по фиче | это рабочее состояние |
| Workflow runs/traces | 6–12 месяцев | aggregated metrics | raw inputs можно чистить раньше |

## 4. Как следить за актуальностью

### Metadata на каждом source

```text
source_id
feature_id
source_type
source_url
created_at
updated_at
fetched_at
last_seen_at
hash
version
permission_label
freshness_status
```

### Freshness statuses

```text
fresh — источник свежий;
stale — истёк TTL;
missing — источник должен быть, но не найден;
changed — source hash изменился, нужно переизвлечение;
archived — источник ушёл в архив;
access_lost — потерян доступ;
conflict — источник противоречит другому источнику.
```

### TTL по источникам

| Источник | TTL на активной фиче | Почему |
|---|---:|---|
| Passport metrics | 1 день | метрики могут обновляться ежедневно |
| Asana project/task | 1 день или webhook | задачи меняются часто |
| Asana comments | 1 день или webhook | важны свежие решения |
| Google Build Plan | 1 день или change detection | План Билдов может измениться |
| Slack curated threads | 1–3 дня | важны новые реплаи |
| Feature Memory | пересборка при изменении artifacts | не должна жить отдельно от sources |

### Freshness propagation — триггер-граф пересборки

«Пересборка при изменении artifacts» — это не одна строка, а каскад. Без явного графа непонятно, когда Feature Memory протухает. Каскад такой:

```text
source changed (hash diff / webhook / TTL expired)
→ mark raw_evidence.freshness = changed
→ enqueue re-extraction для затронутого source (cold path, batch)
→ extractor выдаёт/обновляет artifacts → dedup/merge/supersession
→ если множество artifacts фичи изменилось → mark feature_memory.dirty = true
→ rebuild Feature Memory (компиляция из confirmed + candidate + passport + coverage)
→ инвалидировать кэш context packet'ов этой фичи
```

Правила:

```text
- hot path (запрос PM) НЕ ждёт re-extraction: отвечает на текущей памяти,
  но честно помечает stale_sources и coverage.completeness_hint;
- re-extraction идёт асинхронно (batch), чтобы не платить latency на каждом запросе;
- Feature Memory имеет built_at; если built_at старше последнего source change →
  показывать «память собрана N часов назад, есть необработанные изменения».
```

## 5. Extracted Artifacts Store

### Определение

**Extracted Artifact** — структурированный смысл, извлечённый из raw evidence.

Не summary всего документа, а отдельная сущность:

```text
decision
open_question
risk_signal
miscommunication
priority_drift
blocker
scope_change
discrepancy
action_item
```

### Пример

```json
{
  "artifact_type": "open_question",
  "feature_id": "hidden_temple",
  "text": "Нужно подтвердить, переносим ли часть scope в polishing",
  "source_ids": ["slack_thread_123", "asana_comment_456"],
  "status": "candidate",
  "confidence": "medium",
  "owner": "PM",
  "needs_pm_confirmation": true
}
```

### Зачем нужен Extracted Artifacts Store

Без него система каждый раз перечитывает длинные треды и гдоки.

С ним:

```text
Slack thread 20k tokens
→ один раз обработали
→ получили 3 decisions, 2 open questions, 1 risk
→ дальше в status-update кладём 500–1000 tokens artifacts, а не весь thread
```

### Статусы artifact

```text
candidate — предложено моделью;
confirmed — PM подтвердил;
rejected — PM отклонил;
stale — устарело;
superseded — заменено новым решением;
resolved — вопрос/риск закрыт.
```

### Почему это не «галлюцинации в БД»

Потому что artifact обязан иметь:

```text
source_ids;
confidence;
status;
who_confirmed;
confirmed_at;
needs_pm_confirmation;
```

То есть модель может предложить artifact, но важные operating facts становятся verified только после подтверждения или явного source evidence.

### Confidence threshold — чтобы не спамить PM

Extraction всегда возвращает confidence. Не всё показываем PM на подтверждение:

```text
confidence >= high   → показать PM как candidate сразу;
confidence = medium  → показать, но батчем (не прерывать), сгруппировав по типу;
confidence < medium  → не показывать, держать как silent candidate для retrieval;
                       поднять в видимые только если появился второй независимый source.
```

Смысл: precision важнее recall на входе к PM. Поток low-confidence кандидатов на триаж может стоить дороже, чем чтение исходного треда. Порог — input-переменная, калибруется по eval cases (см. `05`, этап 2).

### Dedup и entity resolution артефактов

Это отдельная задача от dedup raw evidence (там hash по `source_url`). Один и тот же decision, обсуждённый в 3 тредах и комментарии Asana, должен стать **одним** artifact с несколькими `source_ids`, а не четырьмя дублями.

Минимальный механизм на MVP:

```text
1. кандидат-artifact → нормализация (тип + ключевые сущности: feature, build, scope-объект);
2. поиск похожих существующих artifacts (same feature_id, same type, semantic similarity + overlap сущностей);
3. если match выше порога → merge: добавить source_id, обновить confidence, не плодить запись;
4. если конфликтует (тот же объект, противоположный смысл) → не merge, а пометить discrepancy.
```

Без этого Extracted Artifacts Store со временем превращается в дубль-свалку и убивает доверие.

### Supersession — отмена старого решения

Статус `superseded` бесполезен без механизма его проставить. Поддерживаем цепочку:

```text
artifact A (decision, confirmed)
→ позже appears artifact B по тому же объекту с другим исходом
→ система не удаляет A, а ставит A.status = superseded, A.superseded_by = B.id
→ B наследует ссылку supersedes = A.id
→ в Feature Memory попадает только B, но trace на A сохранён
```

Детектор supersession — это частный случай discrepancy-движка (см. `03`): «два artifact по одному объекту, более новый отменяет старый». На MVP supersession между **confirmed** артефактами всегда требует PM-подтверждения, не авто.

### Поля для dedup/supersession

К схеме artifact добавляются:

```text
canonical_key       — нормализованный ключ объекта (feature+type+entity) для матчинга;
merged_source_ids   — все источники, слитые в этот artifact;
supersedes          — id артефакта, который этот отменяет;
superseded_by       — id артефакта, который отменил этот.
```

## 6. Feature Memory

### Определение

**Feature Memory** — компактное текущее состояние фичи.

Она собирается из:

```text
Passport metrics;
confirmed artifacts;
candidate risk signals;
recent deltas;
stale/missing sources;
last status summary.
```

### Пример структуры

```json
{
  "feature_id": "hidden_temple",
  "current_stage": "production",
  "passport_summary": {"size": "M", "delivery_shift": "+1 week"},
  "confirmed_decisions": [],
  "open_questions": [],
  "active_risks": [],
  "recent_deltas": [],
  "unknowns": [],
  "stale_sources": [],
  "coverage": {
    "linked_sources": 7,
    "by_type": {"slack": 3, "asana": 2, "gdoc": 1, "passport": 1},
    "last_ingested_at": "2026-06-29T10:00:00Z",
    "known_blind_spots": ["#ft1-hidden-temple-art не привязан", "ТЗ tab 'Economy' не читается"],
    "completeness_hint": "partial"
  }
}
```

### Coverage / blind-spots — first-class, а не сноска

Линковка источников на MVP ручная (PM привязывает curated threads, см. `07`). Значит покрытие = «что PM вспомнил привязать», и главный риск честной картины — **решение в непривязанном треде**. Система будет уверенно неполной.

Поэтому coverage — обязательное поле Feature Memory и обязательная строка в любом ответе пользователю:

```text
- сколько источников привязано и каких типов;
- когда последний раз обновлялись;
- что система точно НЕ видит (неподключённые каналы, нечитаемые tabs, потерянный доступ);
- completeness_hint: full / partial / thin.
```

Честность про то, чего система не видит, ценнее самого synthesis. Лучше сказать «вижу 7 источников, не вижу art-канал», чем выдать уверенный вывод по неполной картине.

## 7. Retrieval / RAG Index

RAG-индекс строится поверх raw evidence и artifacts.

### Что индексируем

- normalized snippets из Slack/Asana/GDocs;
- extracted artifacts;
- latest summaries;
- source metadata.

### Что не надо искать через RAG

- точные метрики «Паспорта»;
- source map;
- workflow runs;
- permissions;
- due dates, если они есть в структурированном виде.

### Почему hybrid search

Контур должен уметь искать и по смыслу, и по точным полям:

```text
feature_id = Hidden Temple
source_type = Slack
created_at > last_status_at
contains = "build 2"
semantic_query = "обсуждали перенос scope"
```

Поэтому нужен hybrid search: filters + keyword + vector.

## 8. Минимальная схема таблиц

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

## 9. Главное правило хранения

> Не храним всё ради хранения. Храним то, что снижает повторное чтение, улучшает trust, даёт source trace или нужно для evals.
