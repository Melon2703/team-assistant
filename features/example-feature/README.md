# `<Название фичи>` (example-feature)

Entry point по фиче. Живой статус задач и обсуждений не дублируем локально: для оценки движения идти в Asana и Slack live. **ТЗ и план билдов — только live из Google Drive**, локальные копии не держим.

> Это образец feature-папки. Скопируйте под каждую активную фичу: `features/<feature-key>/`.

## Stage

`<preprod / active dev / polishing / post-release / wind-down>`

## Primary Sources

- Asana: [`<project name>`](`<asana-url>`)
- Slack: [`<#feature-channel>`](`<slack-url>`)
- ТЗ (live, source of truth): [Google Doc](`<doc-url>`)
- Концепция: [Google Doc](`<doc-url>`)
- План билдов (live, source of truth): [Google Doc](`<doc-url>`)
- Miro: [board](`<miro-url>`)

## Local Files

- `decisions.md` — решения по фиче и датированные фиксации оценок.

Локальных копий ТЗ или build-plan здесь нет и быть не должно — см. `Usage Rules`.

## Usage Rules

- **ТЗ, build-plan, концепция читаются ВСЕГДА live из Google Drive** через MCP `user-google` (см. skill `gdoc-fetch`) по ссылкам выше. Локальная копия молча протухает.
- Если встречен локальный файл `TS*.md`, `build-plan*.md`, `concept*.md` или аналог — это сигнал удалить файл и подтянуть live, а не использовать.
- Не создавать локальные snapshot-файлы Asana/Slack — быстро протухают.
- Для оценки движения использовать live Asana + Slack + Drive через MCP и skill `feature-weekly-state`.
- Когда фича уйдёт в wind-down — перенести папку в `features/archive/`.
