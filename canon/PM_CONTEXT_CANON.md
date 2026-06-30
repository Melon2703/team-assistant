# PM Context Canon — `<TEAM>`

> **Living document.** Канон описывает устойчивые факты о роли PM: процессы, людей, инструменты, ритуалы.
> Оперативные данные (текущий фокус, дедлайны, риски) живут отдельно — в `current/focus.md`.
>
> **Это шаблон.** Скелет секций универсален, контент специфичен — заполните под свою команду.
> Значения в `<...>` и `[TBD: ...]` — placeholder'ы. Enum'ы / таблицы помечены «пример» там, где их нужно заменить.

## Как пользоваться

- AI: читай этот файл целиком в начале каждого нового PM-контекста.
- Если что-то противоречит наблюдаемой реальности — это сигнал обновить Канон, а не угадать.
- `[TBD]` — открытые вопросы; AI не реконструирует. `[Coda]` — формальный источник (приоритет). `[наблюдение]` — из Slack/Asana, может расходиться с формальным.

---

## 1. Scope & boundaries

**Я — `<PM_NAME>`, Project Manager `<TEAM>` в `<PROJECT>`.** Дата старта: `[TBD]`.

### За что я отвечаю `[TBD: уточнить из формального документа роли]`

Пример зон ответственности PM фиче-команды: планирование версий и майлстоунов; ведение Asana (проекты из шаблонов, актуализация дев-плана); дев-план (подготовка, презентация, поддержание); управление рисками + эскалация; межкомандная координация; контроль сроков; раздача задач; ретроспективы; поддержание базы знаний; status update.

### За что я НЕ отвечаю, но участвую

- Продуктовые решения — финальное слово за продюсером. Участвую в планировании.
- Качество фичи — за это отвечает QA-ответственный и GD.
- Концепты и ТЗ — пишет GD совместно с продюсером.
- Оценка специалистов — совместно с лидами, не единолично.

### Decision rights — где моё слово финальное

`[TBD]` — формальный документ. До его получения AI **спрашивает перед действиями**, которые могут быть выше уровня PM (scope changes, hiring, релизные решения).

### Грейд

`[TBD]`.

---

## 2. Work entities

### Структура Asana

| Тип | Назначение |
| --- | --- |
| **Hub-проект** `<HUB_PROJECT_NAME>` (GID `<HUB_PROJECT_GID>`) | Мастер-агрегатор всех задач команды. Оперативная работа — в feature-проектах. В hub живёт taxonomy и agg view через персональные дорожки. |
| **Feature-проекты** | Один проект на фичу. `[TBD: список активных feature-проектов с GID]`. |
| **Шаблоны** | Хранилище шаблонных задач (A/B-тест, трекинг в аналитике). При создании фичи копируются в feature-проект. |

### Проекты вне команды, с которыми пересекаемся `[Coda]`

Общая структура (значения GID убрать / заполнить под себя): Templates, Technical Tasks (assertions/crashes/tech debt — intake разбирает Tech Director, не команда), Technical Support (deploys, AB-launch, CI), Submit (submit-blocking по версиям), Builds Fails (CI auto-tasks), Support (тикеты), Incidents (postmortem'ы), status-проекты соседних команд.

### Lifecycle фичи

1. **Concept / preprod** — GD + продюсер пишут ТЗ; PM создаёт Asana-проект из шаблона.
2. **Development** — задачи декомпозированы по модулям/билдам.
3. **ОФБ** — Объединённый Финальный Билд (см. раздел 8). `[TBD: ваш аналог]`.
4. **RC → submit → 1% → 100% → soft → force release** (см. раздел 6).
5. **Post-release monitoring** — A/B holdout, crash rate, hotfixes.
6. **Handoff** — фича передаётся в Polishing Team или остаётся на саппорте.
7. **Wind-down** — feature-проект свёрнут, Slack-канал замолкает.

---

## 3. Asana taxonomy

> Имена полей и enum-значения ниже — **пример из исходной команды (Township)**. Для другой компании
> taxonomy может быть другой — замените под свою.

### Custom fields (пример)

| Поле | Назначение | Значения (пример) |
| --- | --- | --- |
| `TS. Status` | Статус в lifecycle | `В очереди`, `Передать в разработку`, `В работе`, `На доработку`, `Ждет фидбека/графику/ТЗ/ПР`, `Код-Ревью`, `QA`, `Готово`, `Приостановлено`, ... |
| `TS. Priority` | Приоритет / тип | `Критический`, `Высокий`, `Средний`, `Низкий`, `Фоновая задача`, `Регулярная задача` |
| `Issue Type` | Тип работы | `Bug`, `Task`, `Question`, `Suggestion`, `Incident`, `Improvement`, ... |
| `TS. Команда` | Дисциплина | `Management`, `Game Design`, `Programming`, `Technical Design`, `ART`, `VFX`, `Звуки`, `Тексты`, `QA team` |
| `TS. Fix Version` | Релизная версия | Числовые коды; шаг +100 мажорные, +10 промежуточные, +1 хотфиксы |
| `Build version` | Номер билда (build-skeleton фич) | `Build #1`…`Build #N` |
| `TS. Effort level` | Story points | Fibonacci-like; **фактически почти не используется** |

### Priority — операционная семантика

- **Критический**: блокирует разработку/тестирование или submit.
- **Высокий**: настоятельно желателен в версии; влияет на восприятие / метрики.
- **Средний**: желателен, но может быть перенесён.
- **Низкий**: можно отложить.

### Naming convention

`(VERSION) PREFIX. [SUBPREFIX.] GOAL` — критично: бот auto-routes задачи по `(VERSION)`. **Полные правила — `canon/asana-task-quality.md`.**

### Due Date — правила

Обязателен, когда выполнение влияет на сроки версии. Нет due date — исполнитель оценивает при старте. Не укладывается — немедленно уведомляет и согласует новую дату.

### Feature-проект — два варианта skeleton `[наблюдение]`

- **По стадиям workflow**: `Входящие → Ключевые → На контроле → Арт/VFX → Бэклог → Финальный этап → В QA → Завершено`. Когда фича в активной разработке проходит фазы готовности.
- **По билдам**: `Билд 1..Финальный билд` + регулярные / релизные. Когда фича делится на инкрементальные билды.

### Build tracking pilot для build-skeleton `[наблюдение]`

Flow: ТЗ → план билдов → критерии / expected state ближайшего билда → конкретные Asana-задачи с owner'ами → targeted Slack check-in → AI-анализ прогресса.

Ключевая норма: ожидание к билду должно быть проверяемым и привязанным к задаче / owner'у. Если expectation есть только в Slack или build-plan, но нет задачи / assignee / критерия — AI подсвечивает `orphan expectation` или `criteria unclear`.

---

## 4. Glossary

`[TBD: расшифровки аббревиатур вашей команды/компании]`. Примеры универсальных: **ОФБ** — Объединённый Финальный Билд; **RC** — Релиз Кандидат; **ТЗ** — Техническое Задание; **GD** — Game Designer; **PM** — Project Manager; **HUD** — game UI overlay.

Source-of-truth для glossary — формальная база знаний (Coda / wiki). Этот раздел — рабочая копия для AI-контекста.

---

## 5. Stakeholders & decision rights

> **Вынесено в `canon/team.md`** (высокая волатильность + частое обращение из skills). См. отдельный файл.

---

## 6. Workflow

### Релизный lifecycle (мажорная версия) `[Coda]`

**Cadence:** `[TBD]` (пример: раз в 6 недель).

| Веха | Когда (пример) |
| --- | --- |
| Final review | T-10 рабочих дней до submit |
| Merge в `stable` | T-5 |
| ОФБ | T-1 после старта pre-submit checks |
| RC testing | T-1 до submit |
| Submit | T-3 до 1% (не пятница) |
| 1% → 100% → Soft → Force | пошагово, не в пятницу |

### Версионирование

`+100` мажорные · `+10` промежуточные · `+1` пересборки/хотфиксы. `[TBD: ваша схема]`.

### Branching `[наблюдение]`

`dev/<team>/<feature>` · `ver/<version>` · `stable/<version>` · `tmp/...`. **Custodian веток:** `<LEAD_PROGRAMMER>` — постит объявления мержей/веток в feature-каналы.

### Routing — раздельные flow `[Coda]`

1. **Feature/PM coordination** — задачи разработки → feature-проект → assigned по дисциплинам. Cross-team координация — через `<CROSS_TEAM_PM>`.
2. **Technical task intake** — asserts/crashes/tech debt → technical-tasks проект, разбирает Tech Director.
3. **Production / live issue** — support tickets → support проект; incidents → lead programmer + PM немедленно + Slack.

### Recurring task patterns `[наблюдение]`

Playtest-driven bug intake (`✓ Плейтест версии. <ФИО>` с subtask-багами); CI PR review (auto); UI Kit pipeline; support escalations; hand-off sequences; background maintenance (crash monitoring, `Регулярная задача`); A/B test template; analytics tracking template. `[TBD: ваши паттерны]`.

---

## 7. Communication norms

> Карта каналов — **функция от стадии фичи и активных участников**, а не статичная роль.
> Заполните под свои каналы; placeholder'ы ниже.

### Карта Slack-каналов (скелет)

| Канал | ID | Реальная функция |
| --- | --- | --- |
| `<FEATURE_CHANNEL>` | `<ID>` | Feature canal. Функция зависит от стадии (preprod → decision-formation hub; polishing → QA-driven coordination). |
| `<TEAM_PROD_CHANNEL>` | `<ID>` | Гибрид: strategic decisions formation + producer-driven status checks + process directives координатора. |
| `<TEAM_ART_CHANNEL>` | `<ID>` | Multi-voice art ↔ GD-design pipeline. |
| `<TEAM_VFX_CHANNEL>` | `<ID>` | VFX review-loop (syncsketch). Bursts перед ОФБ. |
| `<TEAM_CEREMONIAL_CHANNEL>` | `<ID>` | Mixed: ceremonial (welcome, retro) + PM-driven cross-functional coordination. |

### Stage-dependence: feature-канал меняет функцию по фазе `[наблюдение]`

| Фаза | Что доминирует в feature-канале |
| --- | --- |
| **Preprod / prototype** | Decision-formation hub. Архитектурные/product decisions, design iterations. |
| **Active development** | Operational coordination — кто что делает, daily merges, builds. |
| **Polishing / pre-OFB** | QA-driven release coordination. Driver — QA-engineer. |
| **Post-release** | Monitoring и hotfix-coordination. Низкая активность. |
| **Wind-down** | Silent. |

AI должен сначала определить фазу фичи (по `current/focus.md`), потом интерпретировать сигналы.

### Каналы-обманки `[наблюдение]`

Имена каналов часто не отражают реальное использование (например, `*-prod` может быть decision-hub, а не production-каналом). AI не должен делать выводы только по имени канала. `[TBD: отметьте свои каналы-обманки]`.

### Языки

Основной язык команды: `[TBD]`. AI-output по умолчанию на нём; технические термины — на оригинале.

---

## 8. Rituals & cadence

### ОФБ — Объединённый Финальный Билд `[Coda]` `[TBD: ваш аналог]`

Первый билд апдейта со всеми фичами всех команд. Cadence — раз в мажорную версию. Получатели — широкая stakeholder-группа. Правки после ОФБ — только по критическим замечаниям. Роль PM — readiness aggregation.

### Status update

**Cadence `[наблюдение]`:** `[TBD]` (в исходной команде — фактически bi-weekly, хотя формально требовался weekly — при анализе ориентироваться на фактический cadence).

**Реальный формат vs формальный template:** формальный template может описывать формат с маркерами ✅/⚠️/❗ и %-готовности, который **фактически не используется**. Зафиксируйте фактический формат. Полная спецификация — skill `status-update`.

### Daily / weekly meetings `[наблюдение]`

`[TBD: таблица реальных встреч из календаря — operational sync, 1-to-1, GD/Art-синки, intake-triage]`. Source of truth для cadence — Calendar (фактическое) + Coda (формальное); при расхождении показывать оба.

### Release rituals `[наблюдение]`

Branch creation / merge announcements (lead programmer); PM status check-in; build readiness check-in; ОФБ readiness aggregation; blocker list ritual; launch-day announcement; holdout opening ritual.

---

## 9. Quality bar examples

- **Хороший status update** — фактический формат (см. раздел 8 + skill `status-update`). Без маркеров ✅/⚠️/❗ и %-готовности, если они не используются командой.
- **Хорошая Asana-задача** — полные правила в `canon/asana-task-quality.md`. Кратко: name по convention; goal понятен без описания; обязательные fields заполнены; assignee + валидатор-collaborator; описание по template; AC observable.
- **Хороший Slack-thread** `[наблюдение]`: Bug — ссылка на задачу + @mention + контекст; Decision — описание + альтернативы + финал + кто принял; Status check-in — конкретный вопрос.

---

## 10. Source of truth map

### Иерархия источников `[приоритет]`

1. **Coda / wiki** — формальные роли, оргструктура, процессы, terminology, lifecycle.
2. **Asana** — task taxonomy, lifecycle задач, custom fields, текущая работа.
3. **Slack** — реальные ритуалы, decisions, communication norms.
4. **Google Docs** — ТЗ, концепции, планы билдов, status драфты (MCP `user-google` primary).
5. **Miro / Figma** — art iterations, UI Kit.
6. **Syncsketch** — VFX review.
7. **Аналитика (Amplitude и т.п.)** — метрики, A/B results.

### Когда источники конфликтуют

- **Coda vs наблюдаемая реальность (Slack/Asana)** — фиксируем оба, помечаем divergence (формальное vs фактическое). Не выбираем «правильное».
- **Coda устаревшая** — предпочесть наблюдение, но явно указать («в Coda иначе, но фактически…»).

---

## 11. Exceptions / anti-patterns

`[наблюдение]` — собираются по мере работы. Примеры из исходной команды:

- **Низкое Asana coupling на preprod-стадии** — норма, не bug: фича раскрывается через design-обсуждения, не task-level work. Риск: decisions из тредов не маппятся в задачи → orphan expectations.
- **Каналы-обманки** — имена не отражают использование; не делать выводы по имени.
- **Estimate / due_on поля заполняются единичными исполнителями, не системно** — это ограничивает statistics (см. раздел 13).

---

## 12. AI guardrails

### Read-only by default

AI **не должен** без явного подтверждения: писать в Slack от имени PM; создавать/изменять/перемещать/удалять задачи в Asana; публиковать комментарии; менять права доступа / sharing; делать writes в Coda; изменять Google Docs/Sheets.

### При неоднозначности

AI **должен спрашивать**, не угадывать. При конфликте источников — показывать оба. При расшифровке аббревиатур не из glossary — `[guess]` и спросить. При имени без формальной роли — спросить.

### Confidentiality

- Sensitive content (web-payments policy, A/B holdout parameters, release dates, commercial mechanics, HR signals) — не цитировать дословно во внешних артефактах.
- При summary — обобщать, без конкретных цифр и имён upstream stakeholders.

### Что AI делает без подтверждения

Читать данные из MCP (read-only); анализировать, обобщать, делать draft'ы; предлагать варианты; указывать неопределённости явно.

---

## 13. Estimate calibration baseline

> Snapshot исторической статистики по выполненным задачам, для risk-adjusted оценок и подсветки рисков
> просрочек. **Для PM-планирования рисков, не для performance review.**

### Метрики (3 поверхностных сигнала)

Метрика «actual / estimated ratio» обычно недоступна (estimate-поля не заполняются). Работаем с тремя сигналами: **Velocity** (`completed_at − created_at`, P50/P80/P95); **Deadline slip** (`completed_at − due_on`); **QA return rate** (% возвратов на доработку). Сегментация: `assignee × discipline × issue_type`, MIN_SAMPLE = 5.

### Где живёт

`canon/estimates/` (README + raw snapshot + calibration JSON), `scripts/calibrate_estimates.py`. Детально — `canon/estimates/README.md`.

### Sensitivity policy

Персональные коэффициенты **не цитировать в публичных артефактах**. При формулировке для upstream — обобщать на уровне команды/сегмента. При 1-to-1 с исполнителем — его собственные данные в нейтральном формате («тебе проще закладывать буфер N дней»), не «ты плохо оцениваешь».

---

## Открытые вопросы (running list)

`[TBD]` — собранные по ходу, требуют уточнения у конкретных людей:

1. Decision rights PM — формальный документ.
2. Грейд PM.
3. `[TBD: ваши открытые вопросы]`.

---

## История версий

- **v1.0 (шаблон)** — обезличенный скелет, собран из FT1 Township PM-проекта. Заполните под свою команду.
