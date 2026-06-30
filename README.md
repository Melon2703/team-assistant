# PM Cursor Template

Шаблон PM-контекста для работы с AI-агентом (Cursor) в роли Project Manager фиче-команды.

Это обезличенный каркас реального рабочего сетапа PM фиче-команды (Township / Playrix). Он показывает **подход**: как организовать always-on контекст, on-demand workflow (skills), safety-политику и живую память так, чтобы AI-агент полезно работал с Asana / Slack / Google Drive / Coda через MCP.

> Весь контент в `<...>` и `[TBD: ...]` — placeholder'ы. Реальных данных команды здесь нет.
> Это template для clone-and-customize. Порядок адаптации — в конце файла.

## Структура

```
.cursor/
  rules/                       # always-on инструкции AI
    00-bootstrap.mdc           # baseline + порядок чтения + self-update check
    01-actions-policy.mdc      # политика writes / safety (read-only by default)
    02-task-quality.mdc        # жёсткие правила заведения задач
  skills/                      # on-demand workflows; Cursor сам решает, когда применить
    feature-decomposition/     # декомпозиция одного билда фичи на задачи (draft)
    feature-weekly-state/      # PM-оценка движения фичи за период
    asana-inbox-review/        # приближение к Asana Inbox: @-mentions, blockers, overdue
    status-update/             # bi-weekly digest по фичам
    build-review-rollout/      # раскатать корневую задачу на просмотр билда
    gdoc-fetch/                # live-чтение Google Drive (helper)

canon/                         # стабильные факты — меняется редко
  PM_CONTEXT_CANON.md          # роль, Asana taxonomy, workflow, communication, ритуалы
  team.md                      # люди, decision rights, cross-team зависимости
  asana-task-quality.md        # правила заведения задач (полная версия)
  CHANGELOG.md                 # лог правок Канона
  estimates/
    README.md                  # методология risk-adjusted оценок (baseline собирается командой)

current/                       # живая память — обновляется еженедельно
  focus.md                     # текущий фокус: версия, активные фичи, риски
  decisions.md                 # лог значимых решений

features/                      # per-feature папки — entry point + decisions
  example-feature/
    README.md                  # entry point: stage, ссылки на live Drive / Asana / Slack / Miro
    decisions.md               # решения по фиче и датированные оценки

scripts/
  calibrate_estimates.py       # пересчёт estimate-baseline по raw_tasks.json
```

**ТЗ, build-plan, концепты не лежат локально** — single source of truth — Google Drive, читаем live через MCP по ссылкам из feature `README.md`. См. `.cursor/rules/00-bootstrap.mdc`.

## Как Cursor находит контекст

**Rules (`.cursor/rules/*.mdc`)** — always-on (`alwaysApply: true`). Cursor читает в начале каждой сессии: кто я и моя роль; что прочитать перед PM-запросом (Канон → team.md → focus.md); политику действий (read-only by default, writes — только после подтверждения); self-update check; tone, language, sensitive content rules.

**Skills (`.cursor/skills/<name>/SKILL.md`)** — on-demand. Cursor сам решает применить skill по описанию (`description` во frontmatter, формат `Use when...`). Можно вызвать вручную через slash (`/status-update` и т.д.) или описав запрос словами.

Это даёт баланс: baseline (Канон + team + focus + safety) всегда в контексте, специализированные workflow подгружаются только когда нужно.

## MCP в этом сетапе

| MCP | Используется для |
|---|---|
| Asana | Чтение / писание задач, custom fields, секций, проектов |
| Slack | Чтение каналов / тредов / @-mentions, search |
| Coda (опц.) | Read-only по формальной документации (writes — высокорисковая операция) |
| `user-google` | Live-чтение Google Docs / Sheets. Browser — fallback для картинок / Slides / PDF |

Каждый PM подключает MCP под свой workspace через стандартный Cursor MCP-флоу. Google Calendar MCP в этом сетапе не подключён — при запросах про календарь ориентироваться на данные от PM.

## Принципы (то, ради чего стоит смотреть этот шаблон)

1. **Read-only by default.** AI свободно читает из всех систем, но любой write (Asana / Slack / Coda / Drive) — только после явного «ок». Backup перед изменением Asana project state. См. `01-actions-policy.mdc`.
2. **Канон vs живая память.** Стабильные факты (`canon/`) отделены от еженедельно меняющегося (`current/focus.md`). Волатильная часть про людей вынесена в `canon/team.md`.
3. **Self-update check.** После каждой PM-задачи AI прогоняет диагностику «что в контексте устарело» — но не правит файлы сам, а показывает список.
4. **Source of truth — live.** ТЗ / build-plan / концепты не дублируются локально, читаются live из Drive. Локальная копия молча протухает.
5. **AI — draft, человек — решение.** Задачи в Asana AI не создаёт автоматически: только markdown-draft, финальная вычитка за человеком с feature-контекстом.
6. **Sensitive content.** Имена upstream stakeholders, коммерческие механики, A/B-параметры, HR-сигналы — не уходят в публичные артефакты. Скиллы `status-update` и estimates явно описывают, что обобщать.

## Что меняется как часто

| Файл | Когда |
|---|---|
| `canon/PM_CONTEXT_CANON.md` | Раз в 2-4 недели, накопив 5-10 правок |
| `canon/team.md` | По мере кадровых изменений / decision rights |
| `current/focus.md` | Раз в неделю + по ходу |
| `current/decisions.md` | По мере принятия значимых решений |
| `.cursor/skills/*` | Когда skill не справился — поправить description или тело |
| `.cursor/rules/*` | Очень редко — про safety/baseline |

## Slash-команды

`/feature-decomposition` · `/feature-weekly-state` · `/asana-inbox-review` · `/status-update` · `/build-review-rollout` · `/gdoc-fetch`. Если описать запрос словами — Cursor подберёт skill сам.

---

## Адаптация под свою команду

Гипотеза: PM из другой команды клонирует шаблон и за 1-2 рабочих дня доводит до своей специфики.

1. **Заполни `canon/team.md`** — leadership, peer PM, core team, decision rights, cross-team зависимости. Отметь контракторов. (15-30 мин)
2. **Заполни `canon/PM_CONTEXT_CANON.md`** — разделы 1 (роль), 2 (Asana-структура + GID), 3 (taxonomy под свою компанию), 7 (карта Slack-каналов), 8 (ритуалы, cadence). (1-2 часа)
3. **Заполни `canon/asana-task-quality.md`** — префиксы фич (3.2), обязательные custom fields, кто валидатор задач (`<TASK_REVIEWER>`). (30 мин)
4. **Заполни `current/focus.md`** под свои активные фичи. (30 мин)
5. **Заскаффолди feature-папки** — скопируй `features/example-feature/` под каждую активную фичу, заполни `README.md` ссылками на live Drive / Asana / Slack.
6. **Подключи MCP** в Cursor (Asana, Slack, Google Drive, опц. Coda) под свой workspace.
7. **(Опционально) Собери estimates baseline** — собери `canon/estimates/raw_tasks.json` через MCP Asana, запусти `python3 scripts/calibrate_estimates.py`. Шаг для тех, кто хочет risk-adjusted оценки.

Глобальная замена placeholder'ов, которые встречаются по всем файлам:

| Placeholder | Чем заменить |
|---|---|
| `<PM_NAME>` | Имя PM |
| `<COMPANY>` / `<PROJECT>` / `<TEAM>` | Компания / проект / команда |
| `<TASK_REVIEWER>` | Кто вычитывает задачи перед раздачей (GD-лид / тех-лид) |
| `<PRODUCER>` / `<GD_LEAD>` / `<LEAD_PROGRAMMER>` / `<QA_ENGINEER>` | Роли в команде |
| `<FEATURE_CHANNEL>` / `<TEAM_PROD_CHANNEL>` / `<TEAM_ART_CHANNEL>` / `<TEAM_VFX_CHANNEL>` / `<TEAM_CEREMONIAL_CHANNEL>` | Slack-каналы |
| `<HUB_PROJECT_GID>` / `<HUB_PROJECT_NAME>` | Hub-проект Asana |

## Приватность

`.gitignore` закрывает чувствительные артефакты на случай, если вы наполните проект реальными данными: `people/` и `mngmnt/` (HR / performance), `canon/estimates/*.json` (имена + времена), `current/status-update-*` (черновики с именами), `backups/` и `.tmp/` (снапшоты Asana/Slack с GID), `company_brain/` (внутренние стратегические документы). Скелеты `canon/` / `current/` / `features/` обезличены и коммитятся как образцы.

**Не коммить в публичный репозиторий реальные имена, email, GID, A/B-параметры, release-даты и HR-данные.**
