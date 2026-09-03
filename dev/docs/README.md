# Техническая документация «Домовой»

Продуктовая часть — в `docs/product-analysis/`. Здесь — как это построено и как по этому работать.

| Документ | Зачем читать |
|---|---|
| [architecture.md](architecture.md) | Слои, папки, поток обработки чека, границы модулей, кто кого зовёт |
| [domain-rules.md](domain-rules.md) | Все числа и формулы: XP, уровни, настроение, savings, economics, лига, антифрод, рефералы |
| [data-model.md](data-model.md) | Таблицы, колонки, индексы, владельцы |
| [api-contract.md](api-contract.md) | Список ручек и что их потребляет; сам контракт — `../contracts/openapi.yaml` |
| [dev-pipeline.md](dev-pipeline.md) | Как задача проходит от backlog до done, роли агентов, коммиты |
| [testing.md](testing.md) | Стратегия тестов, фикстуры, что обязательно |
| [local-setup.md](local-setup.md) | Поднять всё локально за 5 минут |
| [team.md](team.md) | Кто за что отвечает и как стыкуемся |
| [decisions.md](decisions.md) | Архитектурные решения и чем за них платим |
| [deploy.md](deploy.md) | Схема деплоя на Yandex Cloud VM, что нужно от владельца, порядок первого развёртывания |
| [design/README.md](design/README.md) | Дизайн-система: токены, правила контраста и вёрстки, компоненты; сам макет — `design/mockup.html` |
| [backlog/README.md](backlog/README.md) | Доска задач: эпики, статусы, порядок |

Правила для кода — `.claude/rules/`, рецепты — `.claude/skills/`, агенты — `.claude/agents/`. Корневой `CLAUDE.md` — точка входа для любого агента.
