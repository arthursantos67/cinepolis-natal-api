export const ptBrLocale = "pt-BR";

export function formatCurrency(value: number) {
  return new Intl.NumberFormat(ptBrLocale, {
    currency: "BRL",
    style: "currency",
  }).format(value);
}

export function formatDateTime(value: string | number | Date) {
  return new Intl.DateTimeFormat(ptBrLocale, {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "America/Fortaleza",
  }).format(new Date(value));
}
