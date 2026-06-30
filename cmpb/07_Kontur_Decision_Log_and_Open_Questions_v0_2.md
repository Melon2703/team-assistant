# Контур v0.2 — decision log и открытые вопросы

## 1. Решения, которые можно зафиксировать сейчас

### D1. Контур не заменяет «Паспорт»

**Решение:** «Паспорт» остаётся source of truth для проверенных метрик. Контур читает метрики и добавляет операционный context/evidence слой.

### D2. Anthropic API — целевой LLM backend

**Решение:** локальную LLM-платформу не строим. Claude используется как reasoning/synthesis engine.

### D3. Hot paths делаем через workflows

**Решение:** состояние фичи, статус-апдейт, risk scan и task scaffolding идут через controlled workflows, а не через свободного агента.

### D4. Agent mode нужен только для vague investigation

**Решение:** агентный режим включается для вопросов, где путь заранее неизвестен. Агент read-only, с budget, без autonomous write.

### D5. MCP не является основной архитектурой хранения

**Решение:** MCP/API используются для подключения источников. Но raw evidence, artifacts, feature memory и traces хранятся в Контуре.

### D6. Write actions только через approval

**Решение:** создание задач в Asana, постинг в Slack и изменение статусов требуют PM approval.

### D7. Начинаем с curated Slack threads

**Решение:** на MVP не индексируем весь Slack. PM привязывает важные треды к фиче; позже расширяемся.

### D8. Governance — design constraint, а не открытый вопрос

**Решение:** Raw Evidence Store — новый агрегированный sensitive-стор. Governance закрывается **до** первого байта в хранилище (гейт этапа 0), не «по ходу». Sensitivity классифицируется на уровне источника (чувствительные каналы не инжестятся вообще), `permission_label` несётся по цепочке и enforce'ится на query time, redaction на выходе — второй слой, не первый. Prevention > cleanup.

### D9. Контур честно показывает coverage / blind-spots

**Решение:** покрытие источников — first-class поле Feature Memory и обязательная строка в любом ответе. Система всегда сообщает, чего она НЕ видит. Уверенный вывод по неполной картине без пометки coverage — баг.

### D10. Artifacts дедуплицируются и поддерживают supersession

**Решение:** один смысл из нескольких источников = один artifact с несколькими source_ids. Старое решение не удаляется, а помечается superseded. Supersession между confirmed-артефактами — только через PM.

### D11. Сначала Phase −1 на дешёвом сетапе, потом managed-build

**Решение:** ценность и acceptance валидируются на текущем Cursor + MCP + skills сетапе до инвестиции в managed-инфру. Гейт перехода к build: acceptance черновиков ≥ 0.6 и ≥1 полезный пойманный риск (см. `05`, `06`).

### D12. Acceptance-rate черновиков — economics-метрика №1

**Решение:** acceptance / edit-distance — не quality-метрика, а главный драйвер окупаемости. При realization factor ниже порога экономики нет ни на каком масштабе (см. `06`).

## 2. Открытые вопросы этапа 0

> Governance-вопросы ниже больше не «обсудим», а **обязательные к закрытию на гейте этапа 0** (D8). Это чеклист, а не дискуссия.

### Access / governance (закрыть до ingestion — D8)

1. Какие сервисные аккаунты доступны?
2. Можно ли читать Slack threads сервисным приложением?
3. Можно ли хранить text snapshots Slack/Asana/GDocs?
4. Какие источники нельзя хранить вообще?
5. Что делаем с личными DM?
6. Где храним данные: внутренняя инфраструктура, облако, self-hosted?
7. Как enforce'им permission_label на query time (кто что видит в synthesis)?

### Feature identity

1. Что является стабильным feature_id?
2. Есть ли ID из «Паспорта»?
3. Как связать Passport, Asana project, root task, GDoc и Slack threads?

### Product scope

1. Какая первая фича FT1 подходит для пилота?
2. Какая первая аудитория: PM only, lead, топ?
3. Должен ли статус быть push в Slack или сначала web/markdown draft?

### Quality / evals

1. Какой PM edit считается «минимальной правкой»?
2. Какие риски считаем полезными?
3. Какие redaction rules критичны?
4. Какой gate перед добавлением второго PM?

### Economics

1. Какую internal hourly rate использовать?
2. Сколько PM реально тратит на статус сейчас?
3. Какой бюджет API допустим на одну фичу в месяц?
4. Сколько стоит разработка MVP в engineer-hours?

## 3. Риски решений

### Risk 1. Слишком много данных

**Симптом:** Raw Evidence Store превращается в свалку.

**Контроль:** curated sources, retention, dedupe, source ownership, TTL.

### Risk 2. Слишком много агентности

**Симптом:** Claude сам решает, что читать и что делать, стоимость и качество нестабильны.

**Контроль:** workflows, context packets, max tool calls, read-only agent mode.

### Risk 3. Недостаточно доверия

**Симптом:** PM не принимает черновики.

**Контроль:** source references, PM confirmation, evals, edit-distance tracking.

### Risk 4. Конфликт с «Паспортом»

**Симптом:** две системы спорят, где правда.

**Контроль:** domain-scoped source of truth: «Паспорт» для метрик, raw sources для evidence, PM-confirmed artifacts для operational truth.

### Risk 5. Шумный extraction

**Симптом:** PM тонет в low-confidence кандидатах, триаж дороже чтения треда.

**Контроль:** confidence threshold, числовой precision-таргет на eval set, dedup/merge артефактов (см. `04`, `05` этап 2).

### Risk 6. Ложная полнота (confident incompleteness)

**Симптом:** решение в непривязанном треде → система выдаёт уверенный, но неполный вывод.

**Контроль:** Coverage Tracker, обязательная строка blind-spots в каждом ответе, completeness_hint (D9).

### Risk 7. Не окупается на малом масштабе

**Симптом:** строим дорогую инфру, экономика отрицательна на 1–5 PM.

**Контроль:** Phase −1 на дешёвом сетапе до build, acceptance-gate ≥0.6, честная модель с COGS и break-even (D11, D12, `06`).
