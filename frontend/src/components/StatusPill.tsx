import type { StatusFechamento, StatusSolicitacaoCadastro, StatusViagem } from '../types/domain'

type KnownStatus =
  | StatusViagem
  | StatusFechamento
  | StatusSolicitacaoCadastro
  | 'motorista'
  | 'supervisor'
  | 'analista'
  | 'admin'
  | 'fechamento'
  | 'disponivel'
  | 'consulta'

const LABELS: Record<KnownStatus, string> = {
  em_andamento: 'Em andamento',
  concluida: 'Concluida',
  aberto: 'Aberto',
  fechado: 'Fechado',
  pendente: 'Pendente',
  aprovada: 'Aprovada',
  rejeitada: 'Rejeitada',
  motorista: 'Motorista',
  supervisor: 'Supervisor',
  analista: 'Analista',
  admin: 'Admin',
  fechamento: 'Fechamento',
  disponivel: 'Disponivel',
  consulta: 'Consulta',
}

export function StatusPill({ status }: { status: KnownStatus }) {
  return <span className={`status-pill status-${status}`}>{LABELS[status] ?? status}</span>
}
