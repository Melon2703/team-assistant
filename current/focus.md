# Current Focus — `<TEAM>`

> **Живая память.** Обновляется еженедельно (не реже).
> Last updated: `<YYYY-MM-DD>`
> Updated by: `<кто и на основании чего — транскрипты чатов, status-update drafts, backups>`
>
> **Это скелет-образец.** Замените содержимое на реальный фокус своей команды. Не держите здесь
> ничего «на будущее» — только то, что актуально сейчас.

## Текущая мажорная версия

- **Active fix version:** `<VERSION>` (`<основной фокус команды>`).
- `<доп. версии в работе / мониторинге>`.

## Активные фичи

### `<Фича A>` — `<VERSION>`

- **Stage:** `<preprod / active dev / polishing / post-release / wind-down>` + краткое состояние.
- **Asana:** `<project name>` (`<GID>`).
- **Slack:** `<#feature-channel>` (`<ID>`).
- **Активные потоки в работе:** `<верстка / VFX / контент / туториал / ...>`.
- **Open GD-решения** (см. `features/<feature>/decisions.md`):
  - `<Решение>` — Status: open/concept. Owner: `<кто>`.
- **Risks:** `<риск + impact + mitigation>`.
- **Next milestone:** `<DD.MM — что в скоупе>`.

### `<Фича B>` — `<VERSION>`

- **Stage:** ...

## Открытые решения этой недели

- **Решение:** `<...>` · **Owner:** `<...>` · **Status:** `<open / concept / decided>` · **Контекст:** `<ссылка>`.

## Текущие риски

- **Risk:** `<...>` · **Impact:** `<...>` · **Mitigation:** `<...>` · **Status:** `<open / monitoring / mitigated>`.

## Что я делал на этой неделе

- `<bullet>`

## Open items — мне нужно сделать

- `<bullet>`

---

## Как обновлять этот файл

**Раз в неделю:** обнови `Last updated`; пробеги по активным фичам (статус, milestone, risks); закрой decided решения (перенеси в `decisions.md` с датой и owner'ом); добавь новые открытые решения / риски; удали устаревшее.

**По ходу недели:** решение принято → в `decisions.md`; появился риск → сюда; изменился stage → обнови.

Self-update check (см. `.cursor/rules/00-bootstrap.mdc`) флагает, если `Last updated > 7 дней`.
