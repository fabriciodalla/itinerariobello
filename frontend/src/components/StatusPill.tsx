import type { StatusFechamento, StatusSolicitacaoCadastro, StatusViagem } from '../types/domain'

type KnownStatus =
  | StatusViagem
  | StatusFechamento
  | StatusSolicitacaoCadastro
  | 'motorista'
  | 'supervisor'
  | 'admin'
  | 'fechamento'
  | 'disponivel'
  | 'consulta'
  | 'em_rota'
  | 'fechamento_tardio'
  | 'pendente_tardio'
  | 'lancamento_manual'

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
  admin: 'Admin',
  fechamento: 'Fechamento',
  disponivel: 'Disponivel',
  consulta: 'Consulta',
  em_rota: 'Em rota',
  fechamento_tardio: 'Finalizada em outro dia',
  pendente_tardio: 'Aguardando fechamento (atrasada)',
  lancamento_manual: 'Lancamento manual',
}

export function StatusPill({ status }: { status: KnownStatus }) {
  return <span className={`status-pill status-${status}`}>{LABELS[status] ?? status}</span>
}
