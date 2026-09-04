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

export function pluralize(count: number, forms: [string, string, string]): string {
  const teens = Math.abs(count) % 100;
  const tail = Math.abs(count) % 10;
  if (teens > 10 && teens < 20) return forms[2];
  if (tail === 1) return forms[0];
  if (tail > 1 && tail < 5) return forms[1];
  return forms[2];
}
