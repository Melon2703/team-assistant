---
name: asana-inbox-review
description: Проанализировать Asana Inbox PM-а и подсветить важное — @-mentions, blockers/задачи в "Ждет ...", due today / overdue. Output — ranked list с подсказкой что делать. Use when user asks "проверь инбокс в асане", "что в инбоксе", "что важного в Asana", "asana inbox", "проверь Asana".
---

# Asana Inbox Review

Анализирует то, что в Asana требует внимания PM-а — приближение к Asana Inbox через MCP-коннектор. Output — ranked list с короткой подсказкой по каждой задаче.

## Что это покрывает (и чего не покрывает)

Asana Inbox proper (stream of notifications: @-mentions, status changes, comments) **не имеет прямого API** в текущем MCP-коннекторе. Skill даёт **приближение** через комбинацию:

- Задачи, где PM assignee.
- Задачи, где PM follower (если коннектор это возвращает).
- Задачи с свежими комментариями / @-mentions PM-а (через `get_task` с `include_comments=true`).

**Caveat:** если skill ничего не нашёл по какой-то категории — не значит, что в Inbox пусто. Это значит, что через API не достать. Скажи это явно, не делай ложных выводов о «тишине».

## Что прочитать

1. `canon/PM_CONTEXT_CANON.md` — раздел про custom fields (особенно `TS. Status` enum).
2. `current/focus.md` — какие фичи активные (контекст «куда смотреть»).
3. **Asana** через коннектор:
   - `get_my_tasks(workspace=<gid>, completed_since="now")` — incomplete задачи PM-а. База.
   - Для каждой задачи в категории риска — `get_task(task_gid, include_subtasks=true, include_comments=true)`.
   - `search_tasks` с фильтрами `assignee=me`, `due_on.before=<today>`, priority=критический — для целевых поисков.

## Категории подсветки

Каждая задача может попадать в несколько категорий — пометь все применимые.

### 🔴 @-mentions / прямые вызовы

Условие: в комментариях задачи (последние 7 дней) есть @-mention PM-а, на который он ещё не ответил.

Детект через `get_task(include_comments=true)` → пройти по `stories` / `comments`: найти `<@<gid PM-а>>` в text, сверить с последующими комментами PM-а. Если ответа нет — `@-mention pending`.

Также: задачи, где PM assignee, creator — другой человек, и за 48ч добавлен комментарий — сигнал ожидания реакции.

### 🟡 Blockers / «ждёт»

Условие: `TS. Status` ∈ статусы ожидания (`Ждет фидбека/графику/информацию/ТЗ/переводы/ПР`, `На доработку`, `Приостановлено`) ИЛИ `TS. Priority` = `Критический`. `[TBD: подставьте свои enum-значения статусов ожидания]`.

Для каждой покажи: точный статус и сколько дней висит; чего ждёт (из комментов / описания); кто owner следующего шага.

### 🟠 Due today / overdue

Условие: `due_on` ≤ сегодня. Подкатегории: **Overdue** (критичнее), **Due today**, **Due tomorrow** (information). Для submit-blocking версии (см. focus.md `Active fix version`) — overdue отдельно, жёстче.

### 🔵 Recent status / assignee change

Условие: за последние 24-48ч изменился `TS. Status` или `assignee`. Менее критична. Включай только если ничего из 🔴/🟡/🟠 не блокирует.

## Ранжирование

1. 🔴 + 🟠 (overdue) — самое критичное.
2. 🔴 без overdue.
3. 🟠 (overdue) без 🔴.
4. 🟡 (Критический priority) без 🔴/🟠.
5. 🟡 (Ждёт ...) без 🔴/🟠.
6. 🟠 (due today).
7. 🟠 (due tomorrow) — отдельным information блоком.
8. 🔵 (recent change) — отдельный коротенький блок.

Внутри группы сортируй по feature priority (из focus.md → активная major version submit-blocking → next major), затем по due_on.

## Output

```markdown
# Asana Inbox Review — <дата>

**Source coverage:** <что покрыто / не покрыто>

## 🔴 + 🟠 — нужны срочно

### [(<version>) <prefix>. <name>](task_url)
- **Categories:** 🔴 mention / 🟠 overdue (<N дней>)
- **Status:** <TS. Status> · **Priority:** <TS. Priority> · **Fix Version:** <ver>
- **Что висит:** <короткое описание из последнего комментария / описания>
- **Подсказка:** <ответить / закрыть / переназначить / поднять с owner'ом>

## 🔴 — открытые @-mentions (без overdue)
## 🟠 — overdue без mentions
## 🟡 — критические / ждут
## 🔵 — недавно менялись (information only)

## Что я НЕ смог покрыть
- @-mentions в задачах, где PM не assignee и не follower — MCP не даёт полный stream notifications.
- <если был API error / лимит — отметь явно>
```

## Что НЕ делать

- Не отвечать в задачах от имени PM-а. Только показывать.
- Не менять `TS. Status` / `assignee` / `due_on` сам — это write, требует «ок».
- Не закрывать задачи без явного «ок» и двойного подтверждения для bulk.
- Не цитировать sensitive content дословно во внешних артефактах.
- Не делать ложных выводов о «тишине в Inbox» — если API не дал данных, скажи это явно.
- Не перегружать output: если задач 100+, показывай top-20 + «ещё <N> в категориях X/Y».

## Caveats

- `TS. Status` enum'ы могут расходиться по проектам — иногда «Ждет ПР» пишут вручную в комменте без смены статуса. Если в комменте есть «жду ПР» / «жду фидбек» / «висит на X» — учитывай как 🟡 даже без формального статуса.
- `get_my_tasks` возвращает only assigned задачи. Если PM follower (без assignment) — задача не покроется. Флагай.
- Если PM работает с `My Tasks` через приоритеты Asana (Today / Upcoming / Later) — это **другая** механика, чем `due_on`. Skill использует `due_on`.

## Формат запуска

- Утром каждого дня — что прилетело за ночь.
- Перед feature-weekly-state — не пропустить блокеры.
- После долгого отсутствия — catch-up по накопившемуся.
