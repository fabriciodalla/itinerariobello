import type { Numeric } from '../types/domain'

export function numberValue(value: Numeric | null | undefined) {
  return Number(value ?? 0)
}

export function formatKm(value: Numeric | null | undefined) {
  return `${numberValue(value).toLocaleString('pt-BR', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })} km`
}

export function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return '-'
  }
  return new Intl.DateTimeFormat('pt-BR', {
    timeZone: 'America/Cuiaba',
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}
