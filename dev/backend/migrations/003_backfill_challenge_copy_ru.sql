UPDATE challenges
SET
    copy_title = 'Больше «' || labeled.label || '»',
    copy_body = 'Цель недели: ' || labeled.target_int || ' покупок в категории «' || labeled.label || '».',
    copy_explanation = 'Категория «' || labeled.label || '» — ' || labeled.share_percent
        || '% твоих покупок. Попробуй набрать ' || labeled.target_int || ' раз на этой неделе.'
FROM (
    SELECT
        id,
        CASE category
            WHEN 'dairy' THEN 'Молочное'
            WHEN 'bakery' THEN 'Выпечка'
            WHEN 'fruits_veg' THEN 'Овощи и фрукты'
            WHEN 'meat_fish' THEN 'Мясо и рыба'
            WHEN 'grocery' THEN 'Бакалея'
            WHEN 'snacks' THEN 'Снеки'
            WHEN 'drinks' THEN 'Напитки'
            WHEN 'alcohol' THEN 'Алкоголь'
            WHEN 'household' THEN 'Хозтовары'
            WHEN 'beauty' THEN 'Красота и уход'
            WHEN 'ready_food' THEN 'Готовая еда'
            WHEN 'other' THEN 'Другое'
            ELSE category
        END AS label,
        target::int AS target_int,
        round((rationale_features ->> 'share')::numeric * 100)::int AS share_percent
    FROM challenges
    WHERE type = 'category' AND copy_source = 'template'
) AS labeled
WHERE challenges.id = labeled.id;
