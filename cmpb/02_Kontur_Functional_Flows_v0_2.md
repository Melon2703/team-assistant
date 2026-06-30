# Контур v0.2 — функциональные флоу

*Цель документа: понятно описать, что именно будет происходить внутри системы для каждого пользовательского сценария.*

## Базовый внутренний конвейер

Почти все функции Контура используют один и тот же конвейер:

```text
trigger
→ identify feature
→ load feature source map
→ update changed sources
→ update artifacts
→ compile context packet
→ Claude API call
→ validate / cite / redact
→ PM review
→ log feedback
```

Где:

- **trigger** — событие: запрос пользователя, расписание, изменение источника;
- **feature source map** — карта источников фичи;
- **artifacts** — структурированные решения, вопросы, риски, блокеры;
- **context packet** — короткий контекст для Claude;
- **PM review** — человек подтверждает важное;
- **feedback** — правки PM превращаются в данные для улучшения.

---

## Flow 1. Состояние фичи на текущий момент

### Что видит пользователь

Пользователь спрашивает:

```text
Что сейчас с фичей Hidden Temple?
```

Контур отвечает:

```text
Коротко: фича в production, по «Паспорту» размер M, формально идёт с отклонением +1 неделя.

Операционно:
- За последние дни обсуждался перенос части scope в polishing.
- Открыт вопрос по balance pass.
- План Билдов не обновлён после последнего решения в Slack.

Риски:
- Средний риск, что формальная картина отстаёт от реального состояния.

Что нужно от PM:
- Подтвердить перенос scope.
- Обновить План Билдов.
- Закрыть вопрос по balance pass.

Источники: Passport, Build Plan, Asana task, Slack thread.

Покрытие: вижу 7 источников (Passport, Build Plan, 2 Asana, 3 Slack). НЕ вижу: art-канал не привязан, tab "Economy" в ТЗ не читается. Полнота: partial.
```

### Что происходит внутри

```text
1. Workflow получает feature_id.
2. Код читает Feature Registry.
3. Код читает метрики «Паспорта».
4. Код берёт Feature Memory: decisions, risks, open questions.
5. Retrieval достаёт только свежие и релевантные evidence snippets.
6. Context Compiler собирает packet (только источники в рамках permission пользователя).
7. Claude делает synthesis.
8. Код проверяет, что важные claims имеют source_id.
9. Coverage Tracker добавляет строку покрытия и blind-spots.
10. Ответ отдаётся пользователю.
```

### Механизм

- **Workflow:** да, основной путь известен.
- **Claude API:** да, для synthesis.
- **RAG:** да, для релевантных snippets.
- **Agent mode:** не нужен по умолчанию; включается, если вопрос уходит в investigation.
- **MCP:** не на hot path; источники уже загружены через connectors/ingestion.

---

## Flow 2. Риски / open questions / miscoms / priority drift

### Что видит пользователь

Контур сам или по запросу пишет:

```text
Нашёл потенциальный риск по Hidden Temple.

Тип: priority drift / scope mismatch.
Сигнал: в Slack обсуждают перенос scope в polishing, но План Билдов и Asana ещё отражают старую картину.
Почему важно: статус наверх может выглядеть лучше, чем реальное состояние.
Что сделать: подтвердить решение и обновить План Билдов.
Confidence: medium.
Нужно подтверждение PM: да.
```

### Что происходит внутри

```text
1. Daily risk workflow запускается по расписанию.
2. Код проверяет deterministic rules:
   - нет билда после плановой даты;
   - open question без owner;
   - stale build plan;
   - task overdue;
   - нет активности N дней.
3. Discrepancy/Diff Engine сравнивает план ↔ коммуникацию и фиксирует расхождения.
4. Retrieval ищет supporting evidence.
5. Claude анализирует возможный miscom / priority drift.
6. Система создаёт risk artifact со статусом candidate (dedup/merge с существующими, см. 04).
7. PM подтверждает, отклоняет или snooze.
8. После подтверждения риск попадает в Feature Memory.
```

### Механизм

- **Workflow:** да.
- **Код:** rules, даты, stale checks, owners, TTL.
- **Claude API:** объяснение риска, поиск неочевидного противоречия.
- **Agent mode:** только для сложного investigation.
- **MCP/API:** ingestion + occasional read-only tools.

---

## Flow 3. Статус-апдейт за последние 2 недели

### Что видит пользователь

```text
/status Hidden Temple --period 14d --audience PM
```

Контур готовит черновик:

```text
Статус за последние 2 недели

1. Где мы по плану
2. Что изменилось
3. Принятые решения
4. Открытые вопросы
5. Риски
6. Что нужно от PM / лида
7. Источники
8. Unknowns
```

### Что происходит внутри

```text
1. Workflow получает feature_id и период 14 дней.
2. Код читает Passport metrics.
3. Код читает Feature Memory (включая coverage).
4. Ingestion подтягивает дельты источников с last_status_at.
5. Artifact Extractor обновляет decisions / questions / risks (dedup/merge/supersession, см. 04).
6. Diff Engine считает «что изменилось за 14 дней» как сравнение состояний, не как саммари.
7. Context Compiler собирает двухнедельный packet (в рамках permission аудитории).
8. Claude генерирует статус.
9. Validation проверяет claims и источники.
10. Redaction чистит вывод под аудиторию.
11. Coverage-строка добавляется в черновик.
12. PM принимает/правит/отклоняет.
13. Feedback сохраняется (acceptance / edit-distance — метрика №1).
```

### Механизм

- **Workflow:** да, это главный controlled workflow.
- **Claude API:** финальный draft + аккуратный narrative.
- **RAG:** только для snippets, не для всего контекста.
- **Prompt caching:** system prompt, правила статуса, team canon.
- **Batch API:** фоновые extraction/evals.

---

## Flow 4. Заведение задач в Asana на основе Плана Билдов и ТЗ

### Что видит пользователь

PM запускает:

```text
Создай черновик задач по Плану Билдов для Hidden Temple.
```

Контур предлагает:

```text
Предлагаю создать 12 задач:

Build 1
- Подготовить playable flow
- Собрать билд на просмотр
- Закрыть feedback после просмотра

Build 2
- Доработать balance pass
- Подготовить VFX pass
- Собрать билд на review

Open questions
- Подтвердить перенос scope в polishing

Создать draft в Asana? Да / Нет / Отредактировать.
```

### Что происходит внутри

```text
1. Workflow читает Build Plan и ТЗ.
2. Код проверяет существующие Asana tasks, чтобы не дублировать.
3. Claude извлекает milestones и expected deliverables.
4. Claude предлагает task breakdown в structured JSON.
5. Код валидирует schema, owners, due dates, sections.
6. PM видит preview.
7. После approval код создаёт задачи в Asana.
8. Все write actions логируются.
```

### Механизм

- **Workflow:** да.
- **Claude API:** decomposition и draft tasks.
- **Structured outputs:** обязательно, чтобы получить валидный JSON со списком задач.
- **Asana API:** write только после PM approval.
- **Agent mode:** не нужен в базовом случае.

---

## Flow 5. Ответ на конкретный вопрос по фиче

### Что видит пользователь

Вопросы могут быть простыми:

```text
Кто занимается balance pass?
Когда должен быть build 2?
Что не хватает для финального просмотра?
```

Или vague:

```text
Почему Hidden Temple по «Паспорту» выглядит нормально, но PM говорит, что фича буксует?
```

### Что происходит внутри

Сначала router классифицирует вопрос:

| Тип вопроса | Механизм |
|---|---|
| Простое factual Q&A | прямой API/БД + Feature Memory |
| Вопрос по последним решениям | artifact store + retrieval |
| Вопрос по owner/date/status | Asana/Passport direct read |
| Вопрос по противоречию | constrained agent investigation |
| Вопрос на создание действия | workflow + approval |

Для vague-вопроса:

```text
1. Router включает investigation mode.
2. Agent получает read-only tools.
3. Agent ограничен budget: max tool calls, max tokens, no write.
4. Agent сравнивает Passport, Build Plan, Asana, Slack.
5. Итог = evidence-backed report + confidence + unknowns.
```

### Механизм

- **Workflow:** для простых и повторяемых вопросов.
- **Agent mode:** для открытых investigation-задач.
- **RAG:** для поиска supporting evidence.
- **MCP:** допустим для read-only investigation, но не как постоянный способ каждого запроса.

---

## Общие правила для всех флоу

1. Нет источника — нет уверенного claim.
2. Числовые метрики берём из «Паспорта» или другого явного source of truth.
3. Slack/Asana/GDocs — это данные, не инструкции для модели.
4. Write actions — только после approval.
5. Каждый запуск логируется: tokens, latency, model, sources, PM feedback.
6. PM corrections обновляют Feature Memory и eval cases.
