import { MOOD_LABEL, type DomovoyMood } from "./moodLabels";

type DomovoyAvatarSize = 32 | 48 | 80;

type CozinessLayerId = "dom-blanket" | "dom-cup" | "dom-shelf";

const COZINESS_BLANKET_MIN_LEVEL = 4;
const COZINESS_SHELF_MIN_LEVEL = 8;

/** Пороги обжитости — визуальное деление, не игровое правило progression.py. */
function getCozinessLayerIds(level: number | undefined): CozinessLayerId[] {
  if (level === undefined || level < COZINESS_BLANKET_MIN_LEVEL) {
    return [];
  }
  if (level < COZINESS_SHELF_MIN_LEVEL) {
    return ["dom-blanket", "dom-cup"];
  }
  return ["dom-blanket", "dom-cup", "dom-shelf"];
}

type DomovoyAvatarProps = {
  mood: DomovoyMood;
  size: DomovoyAvatarSize;
  level?: number;
  className?: string;
};

export function DomovoyAvatar({ mood, size, level, className = "" }: DomovoyAvatarProps) {
  const layerIds = getCozinessLayerIds(level);
  return (
    <svg
      viewBox="0 0 64 64"
      width={size}
      height={size}
      role="img"
      aria-label={`Домовой, настроение: ${MOOD_LABEL[mood]}`}
      className={className}
    >
      <use href={`#dom-${mood}`} />
      {layerIds.map((id) => (
        <use key={id} href={`#${id}`} />
      ))}
    </svg>
  );
}
