WITH catalog (category, names) AS (
    VALUES
        ('dairy', ARRAY['Молоко', 'Сыр', 'Сметана', 'Творог', 'Кефир', 'Йогурт']),
        ('bakery', ARRAY['Батон', 'Белый хлеб', 'Булочка', 'Багет', 'Круассан', 'Лаваш']),
        ('fruits_veg', ARRAY['Яблоки', 'Бананы', 'Огурцы', 'Помидоры', 'Картофель', 'Морковь']),
        ('meat_fish', ARRAY['Курица', 'Фарш', 'Свинина', 'Сёмга', 'Треска', 'Сосиски']),
        ('grocery', ARRAY['Гречка', 'Рис', 'Макароны', 'Сахар', 'Подсолнечное масло', 'Соль']),
        ('snacks', ARRAY['Чипсы', 'Шоколад', 'Печенье', 'Орешки', 'Сухарики', 'Мармелад']),
        ('drinks', ARRAY['Вода', 'Сок', 'Чай', 'Кофе', 'Лимонад', 'Морс']),
        ('alcohol', ARRAY['Пиво', 'Вино', 'Сидр', 'Игристое', 'Настойка', 'Ликёр']),
        ('household', ARRAY['Стиральный порошок', 'Средство для посуды', 'Губки', 'Пакеты',
            'Салфетки']),
        ('beauty', ARRAY['Шампунь', 'Зубная паста', 'Мыло', 'Гель для душа', 'Крем для рук',
            'Дезодорант']),
        ('ready_food', ARRAY['Салат «Цезарь»', 'Роллы', 'Пицца', 'Сэндвич', 'Суп', 'Курица гриль']),
        ('other', ARRAY['Батарейки', 'Зажигалка', 'Цветы', 'Открытка', 'Пакет', 'Свечи'])
),

legacy AS (
    SELECT
        id,
        category,
        row_number() OVER (PARTITION BY receipt_id, category ORDER BY id) AS position
    FROM receipt_items
    WHERE product_name ~ ' товар [0-9]+$'
)

UPDATE receipt_items
SET product_name = catalog.names[
    (legacy.position - 1) % array_length(catalog.names, 1) + 1
]
FROM legacy
INNER JOIN catalog ON catalog.category = legacy.category
WHERE receipt_items.id = legacy.id;
