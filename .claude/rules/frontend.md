---
paths:
  - "dev/frontend/**"
---

# Frontend: React + TypeScript, mobile-first

## Структура

```
dev/frontend/src/
  app/
    App.tsx              # провайдеры, роутер, оболочка телефона
    router.tsx
    providers.tsx
  features/<name>/
    api.ts               # запросы к backend, типы из shared/api/schema.d.ts
    hooks.ts             # useQuery/useMutation обёртки
    <Name>Screen.tsx     # экран
    components/          # компоненты только этого feature
    __tests__/
  shared/
    api/
      client.ts          # fetch-обёртка, базовый URL, обработка ошибок
      schema.d.ts        # сгенерировано из openapi.yaml, руками не править
    ui/                  # кнопки, карточки, прогресс — без бизнес-логики
    lib/                 # форматирование чисел, дат
  styles/
```

## Правила

- Один экран = один `features/<name>/<Name>Screen.tsx`. Экраны из PRD: `home`, `challenge`, `league`, `referral`, `pm`.
- Типы API только из `shared/api/schema.d.ts`. Руками типы ответов не описывать. Изменился контракт — `make contract-types`.
- Данные — через TanStack Query в `hooks.ts`. В компонентах нет `fetch` и нет `useEffect` для загрузки.
- Состояние демо (текущий `user_id`) — в URL или в одном контексте в `app/`, не в localStorage.
- Mobile-first: вёрстка под ширину 360–430px, оболочка `app/` центрирует «телефон» на десктопе. Никаких горизонтальных скроллов.
- Tailwind для стилей. Без CSS-in-JS, без styled-components. Повторяющиеся куски — в `shared/ui`.
- Компонент — до 150 строк. Логика вне JSX — в хук.
- Никаких `any`. `unknown` + сужение типа.
- Доступность минимум: кнопки — `<button>`, картинки с `alt`, контраст читаемый.

## Тесты

- Vitest + Testing Library. На каждый экран — тест рендера с замоканным API и тест ключевого действия (нажали «Simulate purchase» — обновился прогресс).
- Мок API — через `msw` или через мок `shared/api/client.ts`. Не мокать хуки.

## Инструменты

- ESLint (flat config) + Prettier. `npm run check` зелёный перед коммитом, pre-commit это проверяет.
- Зависимости через `npm install <pkg>`. Не править `package.json` руками ради версий.
