const moneyFormatter = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 });
const dateFormatter = new Intl.DateTimeFormat("ru-RU", {
  day: "numeric",
  month: "long",
  timeZone: "Europe/Moscow",
});

export function formatMoney(amount: number): string {
  return `${moneyFormatter.format(amount)} ₽`;
}

export function formatSignedMoney(amount: number): string {
  const sign = amount > 0 ? "+" : amount < 0 ? "−" : "";
  return `${sign}${moneyFormatter.format(Math.abs(amount))} ₽`;
}

export function formatNumber(amount: number): string {
  return moneyFormatter.format(amount);
}

export function formatDeadline(isoDate: string): string {
  return dateFormatter.format(new Date(isoDate));
}
