---
name: feature-weekly-state
description: Собрать краткую PM-оценку общего состояния фичи за неделю по Asana feature project и Slack-сигналам. Use when user asks "состояние фичи", "как движется фича", "weekly state", "кого пинговать", "кому помочь", "обнови анализ по фиче" или похожие запросы про недельную картину конкретной фичи.
---

# Feature Weekly State

Собрать живую оценку движения фичи за неделю. Это не status update и не snapshot-файл: результат по умолчанию выдаётся в чат.

> В этом skill используются placeholder-роли (`<PRODUCER>`, `<GD_LEAD>`, `<QA_ENGINEER>`, `<LEAD_PROGRAMMER>`)
> и placeholder-каналы (`<FEATURE_CHANNEL>`, `<TEAM_PROD_CHANNEL>`, ...). Замените на свои в `canon/`.

## Входные параметры

- `feature` / feature folder — например `features/example-feature/`.
- `asana_project` — Asana project name или GID фичи.
- `feature_slack_channel` — Slack channel URL или ID фичи.
- `period` — по умолчанию последние 7 дней.

## Если параметры не заданы

1. Если в чате уже задействована feature-папка — используй её.
2. Иначе прочитай `current/focus.md`, найди активные фичи и спроси какую брать.
3. Не угадывай молча Asana project или Slack channel.

## Источники

1. `canon/PM_CONTEXT_CANON.md` — source-of-truth policy и канал-специфика.
2. `current/focus.md` — активные фичи, Asana/Slack IDs, stage, risks.
3. Feature folder, если есть:
   - `features/<feature>/README.md` — entry point: stage, ссылки на live-источники в Drive (ТЗ, build-plan, концепт), Asana, Slack, Miro.
   - `features/<feature>/decisions.md` — зафиксированные решения и датированные оценки.
   - **ТЗ и build-plan читаем live из Drive** через skill `gdoc-fetch`. Локальных копий быть не должно — если встречены, это сигнал удалить (см. `.cursor/rules/00-bootstrap.mdc`).
4. Asana feature project — задачи, вложенность, due dates, assignees, статусы, секции (`get_project`, `get_tasks`, `get_task` с `include_subtasks=true`, `search_tasks`).
5. Slack за период (channel ID — см. Канон, «Карта Slack-каналов»):
   - feature channel (`<FEATURE_CHANNEL>`);
   - `<TEAM_PROD_CHANNEL>` (decisions hub);
   - `<TEAM_ART_CHANNEL>`, `<TEAM_VFX_CHANNEL>`;
   - `<TEAM_CEREMONIAL_CHANNEL>`.

## Stage-aware чтение Slack (важно)

**Перед чтением определи фазу фичи.** Из `current/focus.md` или контекста. От этого зависит, что искать и как интерпретировать. Подробнее — Канон, секция «Stage-dependence».

### Определение стадии

- **Preprod / prototype** — секции `Подготовка к разработке`, `Билд 1`, `Разобрать`; архитектурные обсуждения в Slack, ТЗ дописывается.
- **Active development** — структура по билдам / workflow-секциям; задачи мигрируют; merges и build announcements ежедневно.
- **Polishing / pre-OFB** — задачи в `На контроле`, `В QA`, `Финальный этап`; QA-engineer — самый активный голос; acceptance reports.
- **Post-release** — `Регулярная задача` в мониторинге, A/B holdout active.
- **Wind-down** — проект свёрнут до 1-2 секций, канал silent.

### Канал-стратегия по стадиям

#### Preprod / prototype
- **Feature channel — главный decision-formation hub**. Читать всё за неделю с раскрытием тредов (там формируются архитектурные / product / process decisions).
- **`<TEAM_PROD_CHANNEL>`** — search по имени фичи, обычно мало.
- **`<TEAM_ART_CHANNEL>`** — если фича с UI, читать. Сигналы: design decisions `<PRODUCER>`, **но не игнорируй `<GD>`** — на препроде он active GD-participant.
- **`<TEAM_VFX_CHANNEL>`** — обычно мало; читать если фича VFX-heavy.

#### Active development
- **Feature channel** — operational coordination + builds. Читать всё.
- **`<TEAM_PROD_CHANNEL>`** — фильтровать decisions, status checks `<PRODUCER>`, schedule/risk signals.
- **`<TEAM_ART_CHANNEL>` / `<TEAM_VFX_CHANNEL>`** — по компонентам фичи.

#### Polishing / pre-OFB
- **Feature channel — QA-driven**. Driver — `<QA_ENGINEER>`. Читать всё; искать release-readiness signals.
- **`<TEAM_PROD_CHANNEL>`** — читать активно: status checks `<PRODUCER>`, фасилитация `<GD_LEAD>`, merge-announcements `<LEAD_PROGRAMMER>`.
- **`<TEAM_ART_CHANNEL>` / `<TEAM_VFX_CHANNEL>`** — bursts перед ОФБ.

#### Post-release
- **Feature channel** — silent / мониторинг. Read-only check.
- **`<TEAM_PROD_CHANNEL>`** — фильтровать incident signals по фиче.

#### Wind-down
- **Feature channel** — пометить «канал в wind-down с DD.MM», не имитировать активность. Остальные — игнорировать.

### Глубина чтения

- В выбранных каналах **обязательно раскрывать треды** через `slack_read_thread` для top-level сообщений с `Thread: N replies`. Сигналы decisions часто в реплаях.
- Объём может превысить context. Решение: писать большие ответы коннектора в файл и парсить через Bash + python с фильтром по дате.

## Что искать

**Spine оценки — раздел «Активный план» (или «Что ждём от билда») из live Drive build-plan.** AI идёт по нему пункт-в-пункт. Сам активный план в output **не пересказывается** — он internal spine.

Для каждого пункта проверь: есть ли задача в Asana (owner, due, статус); свежий сигнал в Slack за период; проверяемый факт в билде (билд-линк); расхождение Asana vs Slack vs build.

В output попадает только то, что:
- **Изменилось за период** — что появилось в билде, что прокомментировал producer / lead, что передано в работу, что переехало.
- **Стало проблемой** — блокер, гэп, риск, вопрос без ответа > 1-2 дней.
- **Требует действия PM** — пинг, помощь, передача задачи, заведение задачи под orphan expectation.

Закрытые и штатные пункты **не упоминаются**, кроме «PM-у важно знать, что не делать заново».

## Обязательный Asana deep pass

Для PM-оценки **недостаточно** только project-level задач. Делай рекурсивный обход релевантной зоны:

1. Получи project-level задачи и секции.
2. Определи релевантный scope: ближайшие due / overdue; активные build-секции; `На контроле`, `Проверка в QA`, `Разобрать`; статусы `Ждет...`, `Приостановлено`, `На доработку`, `В работе`; задачи упомянутые в Slack.
3. Для каждой релевантной задачи — `get_task` с `include_subtasks=true`, `include_comments=true`.
4. Раскрывай subtasks до нижнего уровня.
5. В выводе отделяй выводы из project-level от найденного в subtasks/comments.

Если полный обход большой — сначала критичный scope из п.2, явно скажи что не раскрыто.

## Формат output

Структура — четыре блока в этом порядке. Не переставляй, не добавляй своих секций.

```
<Фича> / <ближайший билд> — апдейт на DD.MM <утро|день|вечер>

Фактами на сейчас:
- 3–6 прозаических буллетов с НОВОСТЯМИ за период.
- Группировка по сюжетам (свежий билд → ревью producer'а → передано в работу → блокеры → закрытое-не-делать).
- Билд-линки и Asana-ссылки внутри буллета, если подкрепляют факт.

Критичные задачи:
- <Имя владельца> — короткая суть — полный Asana URL
- 4–5 задач, только срочные к ближайшему билду / просмотру.

Что еще нужно закрыть:
- Конкретный next check — действие или проверка.
- 3–5 буллетов.

Отдельный процессный сигнал: одной строкой, только если за период появился новый процессный сигнал.
```

### Жёсткие правила стиля

- **Активный план не пересказываем** — он internal spine.
- **Без маркеров ✅ 🟡 ⛔ и чек-боксов.** Прозаический стиль.
- **Без подсекций «Кого пинговать» / «Gap'ы» / «Orphan expectations»** — всё растворяется в четырёх блоках.
- **Asana-ссылки — всегда полный URL.** GID'ы для PM не читаемы.
- **Билд-линк — всегда живой URL.** Без него — гипотеза, переформулируй или опусти.
- **Длина буллета — 1–2 фразы.**
- **Имена — рабочие формы**, как реально называются в Slack/встречах.
- **Даты — `DD.MM` или относительные.**
- **Ссылок не больше 5–6 на отчёт. Нет таблиц.**

### Пример (структура; имена — placeholder)

```
<Фича> / Билд 2 — апдейт на DD.MM утро

Фактами на сейчас:
- В вечернем билде есть <модуль> и попытка <фичи>: <build-link>. На девайсе <нюанс> — <owner> ждёт следующий билд с правкой.
- <PRODUCER> прошёлся по билду и обновил активный план: добавил три крита для Билда 2.
- По <модулю>: <owner> обновил <X>. Остался нюанс — <Y> при <условии>.
- По <модулю> у <LEAD_PROGRAMMER> задача в очереди и не двигалась за неделю — к сборке скорее не успевает.

Критичные задачи:
- <owner> — <суть>: <asana-url>
- <owner> — <суть>: <asana-url>

Что еще нужно закрыть:
- Получить следующий билд с правкой <X>.
- Проверить, что <Y> работает.
- Подтвердить статус <Z> у <owner>.

Отдельный процессный сигнал: <PRODUCER> третий раз за неделю утром просит свежий билд — стоит ввести ежедневный вечерний билд, пока стадия активная.
```

## Фиксация оценки

- По умолчанию не писать в файлы.
- Если просят зафиксировать на момент — добавь dated assessment в `features/<feature>/decisions.md`.
- Перед записью проверь, нет ли там оценки за этот же период — обнови, не дублируй.
- Не создавай `status.md`, `asana-snapshot.md`, `slack-signals.md` и др. snapshot-файлы.

## Что НЕ делать

- Не делать write-операций без явного подтверждения.
- Не цитировать sensitive content дословно; перефразируй.
- Не выдавать transcript Slack. Группируй сигналы.
- Не считать все overdue задачи проблемой без учёта Slack-контекста и priority.
