---
name: add-screen
description: Добавить новый экран или крупный компонент во frontend — feature-папка, api.ts на типах из контракта, hooks.ts на TanStack Query, экран под мобильную ширину, роут, тесты. Использовать на «сделай экран», «добавь страницу», «свёрстай Home/Challenge/League/Referral/PM», «фронт для …», «сделай вёрстку».
argument-hint: <имя экрана>
---

# add-screen — новый экран

## Шаги

1. **PRD.** Открыть раздел экрана в `docs/product-analysis/mechanics/PRD.md` (§4 «Основной интерфейс», §17 demo flow). Выписать, что показываем и какие действия есть.
2. **Контракт.** Найти ручки в `dev/contracts/openapi.yaml`. Если типов нет в `src/shared/api/schema.d.ts` — `make contract-types`. Если ручки нет — сначала скилл `update-api-contract`, экран пишется против контракта с моком.
3. **Папка.** `src/features/<name>/`: `api.ts` (функции `getX(userId)` через `shared/api/client.ts`, типы `paths["/api/v1/..."]["get"]["responses"]["200"]...` из `schema.d.ts`), `hooks.ts` (`useX(userId)` на `useQuery`, мутации на `useMutation` с инвалидацией), `<Name>Screen.tsx`, `components/`, `__tests__/`.
4. **Роут.** Добавить в `src/app/router.tsx`. Путь `/<name>`, `user_id` — из контекста демо.
5. **Вёрстка.** Ширина 360–430px, вертикальный скролл, нижняя навигация из `shared/ui`. Состояния: загрузка, ошибка, пусто. Всё, что в PRD «не показываем» (ФИО, адреса, чужие суммы) — не показывать даже если пришло.
6. **Тесты.** `__tests__/<Name>Screen.test.tsx`: рендер с моком API и проверка ключевых текстов; тест действия (клик → мутация → обновление); тест ошибки.
7. **Проверка.** `npm run check`, `npm run test`, глазами в браузере на ширине 390px.

## Шаблон hooks.ts

```ts
import { useQuery } from "@tanstack/react-query";
import { getHome } from "./api";

export function useHome(userId: number) {
  return useQuery({ queryKey: ["home", userId], queryFn: () => getHome(userId) });
}
```

## Чего не делать

- Не описывать типы ответов руками. Не хранить серверные данные в `useState`.
- Не тащить бизнес-логику (расчёт XP, savings) на фронт — всё приходит готовым.
