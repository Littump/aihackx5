import { formatNumber, pluralize } from "@/shared/lib/format";

export function formatReceiptsCount(count: number): string {
  return `${formatNumber(count)} ${pluralize(count, ["чеку", "чекам", "чекам"])}`;
}

export function formatDiscountedItems(count: number): string {
  const noun = pluralize(count, ["позиция", "позиции", "позиций"]);
  return `${formatNumber(count)} ${noun} со скидкой`;
}
