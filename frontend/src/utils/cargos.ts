export const CARGO_OPTIONS = [
  'SUPERVISOR',
  'COORDENADOR LOCAL',
  'COORDENADOR REGIONAL',
  'GERENTE',
] as const

export type Cargo = (typeof CARGO_OPTIONS)[number]
