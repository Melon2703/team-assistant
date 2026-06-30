---
name: feature-decomposition
description: Декомпозировать конкретный билд фичи на задачи для Asana на основе build-plan и критериев приемки билда. Use when user asks "декомпозируй билд N фичи X", "что нужно завести под билд N", "набросай задачи на билд", "разложи build N на задачи".
---

# Feature Decomposition (build-level)

Декомпозировать **один конкретный билд** уже живущей фичи на задачи. Output — markdown draft, не запись в Asana.

Этот skill **не** делает декомпозицию новой фичи целиком (skeleton, prefix, верхнеуровневые секции). Если фича только заводится и feature-проекта в Asana ещё нет — скажи это явно, режима для этого здесь нет.

## Inputs

1. **Фича** — ключ из `features/<feature>/` (например `example-feature`). Если не указано — спроси.
2. **Билд** — номер целевого билда (например `Build 3`). Если не указано — спроси.

Опционально: целевая `Fix Version`, если отличается от версии билда по умолчанию.

Без обоих обязательных входов **не начинай декомпозицию**. Спроси.

## Что прочитать перед декомпозицией

В этом порядке:

1. `canon/asana-task-quality.md` — формальные правила заведения задач (naming, description template, anti-patterns, mini-checklist). **Это первичный источник для формы draft-задач** — не дублируй, ссылайся.
2. `canon/PM_CONTEXT_CANON.md` — раздел Asana taxonomy (custom fields, naming convention).
3. `features/<feature>/decisions.md` — архитектурные решения по фиче, влияющие на нарезку (пример: «spine делает аниматор — не включать в задачи программистам»).
4. `features/<feature>/README.md` — entry point с Drive-ссылками. **Не используй локальные `TS*.md` / `build-plan*.md` / `concept*.md`**, если они лежат — это сигнал удалить и читать live из Drive.
5. **Build-plan (live из Drive)** через skill `gdoc-fetch` (MCP `user-google`: `Get_Google_Doc_Content` по `doc_id` из ссылки `План билдов` в README). Найти раздел про целевой билд — source of truth для содержания и критериев приемки. **Если URL содержит `?tab=...` — MCP не прочитает таб; попроси скопировать таб или дать Doc без табов.**
6. **ТЗ (live из Drive)** через `gdoc-fetch` по ссылке `ТЗ` из README — таргетируй разделы по модулям целевого билда.
7. **Существующие задачи в Asana** под feature-проектом: `get_project(project_gid, include_sections=true)`, `get_tasks` / `search_tasks` по секции `Билд N` и сопредельным, `get_task` для деталей.
8. **Recent feature-канал в Slack** (за 3-5 дней) — чтобы draft не противоречил недавним решениям. Канал из README.

Если build-plan не открывается / не содержит целевого билда — **остановись** и сообщи. Декомпозиция без build-plan невозможна.

## Критичный gate: критерии приемки

После того как нашёл целевой билд в build-plan, **до** генерации задач:

1. Извлеки expected state билда — что должно быть готово / проверяемо.
2. Извлеки критерии приемки — observable outcomes.

Если критериев нет или они размытые («сделать UI» без observable outcome):

```markdown
**Критерии приемки билда не найдены / неполные:**
- ...
**Что нужно уточнить перед заведением задач:**
- ...
```

Если критерии есть, но видишь что стоит добавить — вынеси `**Предлагаю добавить критерии:**` до списка задач. После — можно дать draft, помечая задачи без чётких критериев как `criteria missing`.

## Маппинг expected state → существующие задачи

Перед предложением новых задач **сверь expected state со списком уже заведённых** — не плодить дубли, не пропустить расхождение.

По каждому пункту:

1. Поискать задачу по ключевым словам (модуль / окно / механика) — `search_tasks` или `get_tasks` в релевантных секциях.
2. Если матч **есть** — записать как existing (ссылка, секция, assignee, статус, версия). Отметь `status mismatch` / `version mismatch` / `criteria mismatch`.
3. Если матч **не найден** — оформить как draft новой задачи.
4. Если owner / дисциплина неочевидны — пометь `owner unclear`, не угадывай.

Обратное направление: задачи в секции билда, не покрытые expected state — `orphan task` (сигнал устаревания build-plan или лишней задачи).

## Naming convention для draft-задач

**Полные правила — `canon/asana-task-quality.md`.** Quick reference:

- Формат: `(VERSION) PREFIX. [SUBPREFIX.] GOAL`.
- `PREFIX` — устоявшаяся аббревиатура фичи. Если непоследовательный — не выбирай сам, флагай.
- `SUBPREFIX` (опц.) — `ART.`, `VFX.`, `GD.`, `QA.`, `TD.` и т.д.
- **UI и Programming разделяются на отдельные задачи** с blocked-by связью. Центральная норма build-skeleton фич — не нарушать.

## Custom fields для draft-задач

Заполнить где значение очевидно из build-plan / контекста. Где нет — пусто + пометка. `[TBD: адаптируйте набор полей под свою taxonomy]`. Пример:

- `TS. Status`: `В очереди` (по умолчанию).
- `TS. Priority`: `Средний` по дефолту; `Высокий`/`Критический` — только если явно из build-plan.
- `TS. Fix Version`: целевая версия из inputs.
- `TS. Команда`: дисциплина исполнителя.
- `Issue Type`: чаще `Task`.
- `Build version`: `Build #N`.
- `assignee`: **не назначай**. Можно предложить кандидата, финал — за PM.

## Output

```markdown
# Декомпозиция: <Фича> — <Build N>

**Feature:** <feature key> · **Build:** Build N · **Target Fix Version:** <VERSION>
**Build-plan:** <Drive ссылка> · **Asana feature project:** <ссылка>

## Критерии приемки билда (из build-plan)
- ...
[если критериев нет / неполные — блок `Критерии не найдены` и стоп до подтверждения]

## Expected state билда → existing Asana tasks
| Expected state | Asana task | Section | Status | Fix Version | Build version | Assignee | Заметки |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Draft задач для заведения

### (<VERSION>) <PREFIX>. <Goal>
- **Цель задачи (одно предложение):** ...
- **Acceptance criteria:**
  - [ ] <observable условие>
- **Источники:**
  - ТЗ: <ссылка с heading-anchor>
  - План билдов: <ссылка с heading-anchor>
  - Slack-решение: <ссылка, если есть>
- **Custom fields:** TS. Status / TS. Priority / TS. Fix Version / TS. Команда / Issue Type / Build version
- **Suggested assignee:** [TBD / кандидат по аналогии]
- **Collaborator:** <TASK_REVIEWER> — обязательно, для вычитки перед раздачей.
- **Mini-checklist (asana-task-quality.md):** прогнать перед заведением.

## Orphan задачи в секции «Билд N», не покрытые expected state
## Pending issues / уточнения
```

## Что НЕ делать

- **Не создавать задачи в Asana автоматически через `create_tasks`.** Output — markdown draft. Финальное заведение делает человек после построчной вычитки.
- Не декомпозировать без build-plan.
- Не пропускать gate по критериям приемки.
- Не угадывать prefix — бери из существующих задач.
- Не назначать assignee. Можно предложить.
- Не смешивать UI и Programming в одной задаче.
- Не копировать раздел ТЗ целиком — только ссылка + 2-3 буллета релевантного.
- Не включать пункты из чужой дисциплины (см. anti-patterns + `features/<feature>/decisions.md`).
- Не использовать локальные `TS*.md` / `build-plan*.md` / `concept*.md` — флагай на удаление.
- Не делать декомпозицию новой фичи целиком — режим не поддержан.

## Если билд большой

Не декомпозируй всё за один проход. Предложи: «сначала пройдёмся по expected state и сверим с существующими задачами, потом отдельно draft новых». Получи «ок» по маппингу прежде чем расписывать новые задачи.
