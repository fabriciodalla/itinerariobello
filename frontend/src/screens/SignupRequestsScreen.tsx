import { useCallback, useEffect, useState } from 'react'
import { Check, Loader2, UserPlus, X } from 'lucide-react'
import { PasswordInput } from '../components/PasswordInput'
import { StatusPill } from '../components/StatusPill'
import { ApiError, api } from '../services/api'
import type { PerfilUsuario, SignupRequest, TipoVeiculo, User } from '../types/domain'
import { formatDateTime } from '../utils/format'

interface SignupRequestsScreenProps {
  token: string
  onMessage: (message: string) => void
}

interface DecisionState {
  senhaTemporaria: string
  perfil: PerfilUsuario
  superiorId: string
  podeAprovar: boolean
  tipoVeiculo: TipoVeiculo
  motivo: string
  saving: boolean
}

function initialDecision(): DecisionState {
  return {
    senhaTemporaria: '',
    perfil: 'motorista',
    superiorId: '',
    podeAprovar: false,
    tipoVeiculo: 'proprio',
    motivo: '',
    saving: false,
  }
}

export function SignupRequestsScreen({ token, onMessage }: SignupRequestsScreenProps) {
  const [requests, setRequests] = useState<SignupRequest[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [decisions, setDecisions] = useState<Record<string, DecisionState>>({})

  const load = useCallback(async () => {
    try {
      const [pendingRequests, adminUsers] = await Promise.all([
        api.signupRequests(token, 'pendente'),
        api.users(token),
      ])
      setRequests(pendingRequests)
      setUsers(adminUsers)
      setDecisions((current) => {
        const next = { ...current }
        for (const request of pendingRequests) {
          next[request.id] = next[request.id] ?? initialDecision()
        }
        return next
      })
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Nao foi possivel carregar os cadastros.')
    }
  }, [onMessage, token])

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0)
    return () => window.clearTimeout(timeout)
  }, [load])

  function updateDecision(id: string, patch: Partial<DecisionState>) {
    setDecisions((current) => ({
      ...current,
      [id]: {
        ...(current[id] ?? initialDecision()),
        ...patch,
      },
    }))
  }

  async function approve(request: SignupRequest) {
    const decision = decisions[request.id] ?? initialDecision()
    if (!decision.senhaTemporaria.trim()) {
      onMessage('Informe a senha temporaria.')
      return
    }
    updateDecision(request.id, { saving: true })
    try {
      await api.approveSignupRequest(token, request.id, {
        senha_temporaria: decision.senhaTemporaria,
        perfil: decision.perfil,
        superior_id: decision.superiorId || null,
        pode_aprovar: decision.podeAprovar,
        tipo_veiculo: decision.tipoVeiculo,
      })
      onMessage('Solicitacao aprovada.')
      await load()
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Nao foi possivel aprovar a solicitacao.')
    } finally {
      updateDecision(request.id, { saving: false })
    }
  }

  async function reject(request: SignupRequest) {
    const decision = decisions[request.id] ?? initialDecision()
    if (!decision.motivo.trim()) {
      onMessage('Informe o motivo da recusa.')
      return
    }
    updateDecision(request.id, { saving: true })
    try {
      await api.rejectSignupRequest(token, request.id, decision.motivo.trim())
      onMessage('Solicitacao reprovada.')
      await load()
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Nao foi possivel reprovar a solicitacao.')
    } finally {
      updateDecision(request.id, { saving: false })
    }
  }

  return (
    <section className="panel panel-edge-bottom">
      <div className="section-title">
        <UserPlus />
        <div>
          <h2>Cadastros</h2>
          <p>Solicitacoes pendentes</p>
        </div>
      </div>

      <div className="item-list">
        {requests.map((request) => {
          const decision = decisions[request.id] ?? initialDecision()
          return (
            <article className="list-card" key={request.id}>
              <div className="list-card-main">
                <div>
                  <strong>{request.nome}</strong>
                  <span>{request.email}</span>
                </div>
                <StatusPill status={request.status} />
              </div>

              <div className="request-details">
                <span>{request.cargo}</span>
                <span>Superior: {request.superior}</span>
                <span>
                  {request.veiculo_placa} | {request.veiculo_marca} {request.veiculo_modelo}
                </span>
                <span>{formatDateTime(request.criado_em)}</span>
              </div>

              {request.observacao ? <div className="empty-state compact-state">{request.observacao}</div> : null}

              <div className="signup-decision-form">
                <div className="signup-grid">
                  <PasswordInput
                    label="Senha temporaria"
                    value={decision.senhaTemporaria}
                    onChange={(event) => updateDecision(request.id, { senhaTemporaria: event.target.value })}
                  />
                  <label>
                    <span>Perfil</span>
                    <select
                      value={decision.perfil}
                      onChange={(event) => updateDecision(request.id, { perfil: event.target.value as PerfilUsuario })}
                    >
                      <option value="motorista">Motorista</option>
                      <option value="supervisor">Supervisor</option>
                      <option value="analista">Analista</option>
                      <option value="admin">Admin</option>
                    </select>
                  </label>
                  <label>
                    <span>Superior</span>
                    <select
                      value={decision.superiorId}
                      onChange={(event) => updateDecision(request.id, { superiorId: event.target.value })}
                    >
                      <option value="">Sem superior</option>
                      {users.map((user) => (
                        <option key={user.id} value={user.id}>
                          {user.nome}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>Veiculo</span>
                    <select
                      value={decision.tipoVeiculo}
                      onChange={(event) => updateDecision(request.id, { tipoVeiculo: event.target.value as TipoVeiculo })}
                    >
                      <option value="proprio">Proprio</option>
                      <option value="alugado">Alugado</option>
                      <option value="empresa">Empresa</option>
                    </select>
                  </label>
                </div>

                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={decision.podeAprovar}
                    onChange={(event) => updateDecision(request.id, { podeAprovar: event.target.checked })}
                  />
                  <span>Pode fechar mensalmente</span>
                </label>

                <div className="action-row">
                  <button
                    className="primary-button compact"
                    type="button"
                    onClick={() => void approve(request)}
                    disabled={decision.saving}
                  >
                    {decision.saving ? <Loader2 className="spin" /> : <Check />}
                    <span>Aprovar</span>
                  </button>
                </div>

                <label>
                  <span>Motivo da recusa</span>
                  <textarea
                    value={decision.motivo}
                    onChange={(event) => updateDecision(request.id, { motivo: event.target.value })}
                  />
                </label>
                <button
                  className="secondary-button compact"
                  type="button"
                  onClick={() => void reject(request)}
                  disabled={decision.saving}
                >
                  <X />
                  <span>Reprovar</span>
                </button>
              </div>
            </article>
          )
        })}
      </div>

      {!requests.length ? <div className="empty-state">Nenhuma solicitacao pendente.</div> : null}
    </section>
  )
}
