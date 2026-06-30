---
name: gdoc-fetch
description: Получить актуальное содержимое Google Doc / Sheet / Slides по ссылке или поиском, для использования как источника контекста. Use when user shares Google Doc/Sheet link, asks to "посмотреть актуальный план билдов", "сверить с ТЗ в Google Docs", "достань status update драфт", "что в концепции/ТЗ", "найди гуглодок про X", или когда любой skill ссылается на ТЗ / концепцию / план билдов / status update в Google Drive.
---

# Google Drive Fetch (через MCP `user-google`)

Получить актуальное содержимое документов из Google Drive — ТЗ, концепции, планы билдов, status update драфты, любые ссылки в `features/*/README.md` и Канон.

**Primary:** MCP `user-google` — read-only, без браузера, быстро.
**Fallback:** нативный Cursor browser — только когда MCP не покрывает формат или нужны embedded-картинки / блок-схемы.

## MCP-инструменты (`user-google`)

Перед вызовом проверь schema в MCP descriptors. Основные тулы:

| Tool | Когда |
|---|---|
| `Get_Google_Doc_Content` | Google Doc по `doc_id` |
| `Get_Google_Sheet_Content` | Google Sheet по `sheet_id` |
| `Search_Google_Docs` | Поиск документа по имени |
| `Search_Google_Sheets` | Поиск таблицы по имени |
| `List_Google_Drive_Files` | Листинг файлов в папке / root |

Вызов: `CallMcpTool(server="user-google", toolName="Get_Google_Doc_Content", arguments={"doc_id": "<ID>"})`.

## Извлечение ID из URL

- `https://docs.google.com/document/d/<DOC_ID>/edit...` → `doc_id`
- `https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit...` → `sheet_id`
- `https://docs.google.com/presentation/d/<ID>/edit...` → MCP не поддерживает → browser fallback
- `https://drive.google.com/file/d/<ID>/view...` → generic file (PDF, image) → browser fallback

Heading-anchors (`#heading=h.xxx`) в URL игнорируем при MCP-чтении — ищи нужный раздел по тексту в ответе MCP.

## Ограничения MCP (важно)

- **`Get_Google_Doc_Content` возвращает только текст.** Inline-картинки, блок-схемы, UI-mockup'ы, Google Drawings в Doc **не извлекаются** — в тексте будет дырка после заголовка.
- Для embedded-диаграмм: browser fallback (`browser_navigate` + `browser_take_screenshot`) **или** попроси приложить скрин / вынести схему в Miro.
- **Google Docs Tabs (фича 2024) НЕ ПОДДЕРЖИВАЮТСЯ.** Schema принимает только `doc_id`. Если документ использует табы (URL содержит `?tab=t.xxxxx`), MCP вернёт только содержимое основной части. Симптом: ответ MCP короткий на документе, где визуально гораздо больше контента. Это **не баг конкретного документа**, а общий gap MCP.
  - **Fallback:** (1) попросить скопировать содержимое нужного таба в чат; (2) попросить экспортировать таб в отдельный Doc без табов и дать новый `doc_id`; (3) browser fallback (`browser_navigate` на URL с `?tab=...` + `browser_snapshot`).
- **Google Slides** — MCP не покрывает → browser fallback.
- **PDF / scanned** — browser fallback; scanned OCR не поддерживается.
- MCP не отдаёт metadata вроде «Last edit was …» — укажи URL источника; свежесть подтверждает человек, если нужно.

## Когда использовать

- Прислана ссылка на Google Doc / Sheet и просьба что-то с ней сделать.
- Skill `feature-decomposition` / `feature-weekly-state` ссылается на ТЗ, концепцию или build-plan — нужен актуальный текст. **ТЗ / build-plan / концепты ВСЕГДА live из Drive, локальных копий не держим** (см. `.cursor/rules/00-bootstrap.mdc`). Точка входа — `features/<feature>/README.md` (`Primary Sources`).
- Просьба «посмотри что в плане билдов» без ссылки — сначала `features/<feature>/README.md`; если ссылки нет — `Search_Google_Docs` / спроси.
- Если в `features/<feature>/` встречен локальный `TS*.md` / `build-plan*.md` / `concept*.md` — не использовать, флагать на удаление.

## Алгоритм по типу запроса

### Тип A — прямая ссылка

1. Извлеки `doc_id` / `sheet_id` из URL.
2. **Если URL содержит `?tab=t.xxxxx` — это Google Docs Tabs.** MCP таб не прочитает. Предупреди: «URL ведёт на конкретный таб; MCP его не поддерживает. Скопируешь содержимое в чат, или дать `doc_id` без табов?»
3. `Get_Google_Doc_Content` или `Get_Google_Sheet_Content`.
4. **Sanity check ответа:** если ответ очень короткий (1-3 строки) для документа, где визуально больше — это может быть Tabs-gap. Проверь URL ещё раз.
5. Если нужен конкретный раздел — grep / search по тексту ответа.
6. В output: title (если виден), URL, summary / цитата.

### Тип B — найти документ по контексту фичи

1. `features/<feature>/README.md` → `Primary Sources`.
2. Если ссылки нет: сначала спроси прислать ссылку; если «поищи сам» → `Search_Google_Docs(query=...)`; покажи кандидатов, уточни какой брать.
3. Дальше как в Типе A.

### Тип C — ТЗ / build-plan / концепт по фиче

1. `features/<feature>/README.md` → `Primary Sources`.
2. MCP по соответствующей ссылке.
3. Live-контент в ответе + URL.
4. Локальные копии в feature-папке — не источник, флагать на удаление.

## Browser fallback (только когда MCP недостаточно)

Использовать **после** попытки MCP, не вместо: embedded-картинки / блок-схемы, Google Slides, PDF, ошибка auth.

- `browser_navigate(url)` → `browser_snapshot()` — текст из DOM.
- `browser_take_screenshot()` — диаграммы, сложные таблицы.
- `browser_search(text=...)` — прыжок к разделу в длинном Doc.

Browser должен быть залогинен в Google.

## Что НЕ делать

- Не использовать browser как primary для Doc/Sheet, если MCP доступен.
- Не модифицировать Google Doc / Sheet / Slides без явного «ок». Skill — read-only.
- Не цитировать sensitive content дословно (см. `.cursor/rules/01-actions-policy.mdc`).
- Не угадывать URL / file id.
- Не пересказывать длинный документ целиком — только релевантное.

## Output

- **«Что там в документе»** — summary, ключевые секции, TBD.
- **«Достань раздел»** — цитата + URL (+ heading anchor если есть).
- **«Найди документ»** — кандидаты из Search, спросить какой брать.

Всегда: title, ссылка на оригинал, пометка если использовался browser fallback для картинок.
