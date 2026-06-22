export type PerfilUsuario = 'motorista' | 'supervisor' | 'analista' | 'admin'
export type StatusViagem = 'em_andamento' | 'concluida'
export type StatusFechamento = 'aberto' | 'fechado'
export type StatusSolicitacaoCadastro = 'pendente' | 'aprovada' | 'rejeitada'
export type TipoVeiculo = 'proprio' | 'alugado' | 'empresa'
export type TipoDisponibilidadeVeiculo = 'fixo' | 'alocado'
export type Numeric = number | string

export interface User {
  id: string
  nome: string
  email: string
  perfil: PerfilUsuario
  cargo: string | null
  superior_id: string | null
  pode_aprovar: boolean
  ativo: boolean
}

export interface Vehicle {
  id: string
  placa: string
  modelo: string
  marca: string | null
  unidade: string | null
  categoria: string | null
  tipo: TipoVeiculo
  tipo_disponibilidade: TipoDisponibilidadeVeiculo
  usuario_responsavel_id: string | null
  responsavel_nome: string | null
  ativo: boolean
  prioritario: boolean
}

export interface VehicleInRoute {
  viagem_id: string
  veiculo_id: string
  placa: string
  modelo: string
  motorista_id: string
  motorista_nome: string
  em_rota: boolean
  partida_em: string
}

export interface GpsPayload {
  latitude: number
  longitude: number
  precisao_metros: number | null
  endereco?: string | null
}

export interface ReverseGeocodeResponse {
  endereco: string | null
  endereco_resolvido: boolean
  endereco_exibicao: string
}

export interface Trip {
  id: string
  usuario_id: string
  usuario_nome: string
  veiculo_id: string
  veiculo_placa: string
  veiculo_modelo: string
  status: StatusViagem
  km_inicial: Numeric
  km_final: Numeric | null
  km_rodado: Numeric | null
  rota_utilizada: string | null
  partida_em: string
  chegada_em: string | null
  foto_hodometro_inicial: PhotoEvidence | null
  foto_hodometro_final: PhotoEvidence | null
}

export interface LoginResponse {
  access_token: string
  token_type: 'bearer'
}

export interface SignupRequestPayload {
  nome: string
  email: string
  cargo: string
  superior: string
  veiculo_placa: string
  veiculo_modelo: string
  veiculo_marca: string
  observacao?: string | null
}

export interface SignupApprovePayload {
  senha_temporaria: string
  perfil: PerfilUsuario
  superior_id: string | null
  pode_aprovar: boolean
  tipo_veiculo: TipoVeiculo
  tipo_disponibilidade?: TipoDisponibilidadeVeiculo | null
}

export interface SignupRequest extends SignupRequestPayload {
  id: string
  status: StatusSolicitacaoCadastro
  usuario_id: string | null
  veiculo_id: string | null
  processado_por_id: string | null
  processado_em: string | null
  motivo_recusa: string | null
  criado_em: string
  atualizado_em: string
}

export interface PhotoEvidence {
  id: string
  viagem_id: string
  tipo: 'inicial' | 'final'
  mime_type: string
  tamanho_bytes: number
  criado_em: string
  download_url: string
}

export interface GpsEvidence extends GpsPayload {
  id: string
  viagem_id: string
  tipo: 'partida' | 'chegada'
  endereco_resolvido: boolean
  endereco_exibicao: string
  capturado_em: string
}

export interface ReportItem {
  id: string
  usuario_id: string
  usuario_nome: string
  veiculo_id: string
  veiculo_placa: string
  veiculo_modelo: string
  partida_em: string
  chegada_em: string | null
  km_inicial: Numeric
  km_final: Numeric | null
  km_rodado: Numeric | null
  rota_utilizada: string | null
  foto_hodometro_inicial: PhotoEvidence | null
  foto_hodometro_final: PhotoEvidence | null
  gps_partida: GpsEvidence | null
  gps_chegada: GpsEvidence | null
  status: StatusViagem
  fechamento_mensal_id: string | null
  status_fechamento: StatusFechamento
  superior_id: string | null
  avaliado_em: string | null
  observacao_fechamento: string | null
}

export interface MonthlyClosure {
  id: string | null
  motorista_id: string
  motorista_nome: string
  ano: number
  mes: number
  status: StatusFechamento
  superior_id: string | null
  avaliado_em: string | null
  observacao: string | null
  total_viagens: number
  km_total: Numeric
}
