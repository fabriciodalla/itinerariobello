import { useCallback, useEffect, useState } from 'react'
import { CarFront, Edit3, KeyRound, Loader2, RefreshCw, Save, Search, Users, X } from 'lucide-react'
import { PasswordInput } from '../components/PasswordInput'
import { ApiError, api } from '../services/api'
import type { User, Vehicle } from '../types/domain'

interface UsersScreenProps {
  token: string
  onMessage: (message: string) => void
}

type EditTarget = { type: 'reset'; user: User } | { type: 'user'; user: User } | { type: 'vehicle'; vehicle: Vehicle }

export function UsersScreen({ token, onMessage }: UsersScreenProps) {
  const [users, setUsers] = useState<User[]>([])
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [tab, setTab] = useState<'users' | 'vehicles'>('users')
  const [editTarget, setEditTarget] = useState<EditTarget | null>(null)
  const [saving, setSaving] = useState(false)

  const [novaSenha, setNovaSenha] = useState('')
  const [confirmacao, setConfirmacao] = useState('')
  const [editSuperiorId, setEditSuperiorId] = useState('')
  const [editPerfil, setEditPerfil] = useState('')
  const [editAtivo, setEditAtivo] = useState(true)

  const [editVeiculoResponsavel, setEditVeiculoResponsavel] = useState('')
  const [editVeiculoDisponibilidade, setEditVeiculoDisponibilidade] = useState('')
  const [editVeiculoUnidade, setEditVeiculoUnidade] = useState('')
  const [editVeiculoAtivo, setEditVeiculoAtivo] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [u, v] = await Promise.all([api.users(token), api.allVehicles(token)])
      setUsers(u)
      setVehicles(v)
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Nao foi possivel carregar os dados.')
    } finally {
      setLoading(false)
    }
  }, [onMessage, token])

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0)
    return () => window.clearTimeout(timeout)
  }, [load])

  const filtered = tab === 'users'
    ? users.filter((u) => {
        if (!search.trim()) return true
        const term = search.toLowerCase()
        return u.nome.toLowerCase().includes(term) || u.email.toLowerCase().includes(term)
      })
    : vehicles.filter((v) => {
        if (!search.trim()) return true
        const term = search.toLowerCase()
        return v.placa.toLowerCase().includes(term) || v.modelo.toLowerCase().includes(term) || (v.unidade ?? '').toLowerCase().includes(term)
      })

  function closeModal() {
    setEditTarget(null)
    setNovaSenha('')
    setConfirmacao('')
  }

  function openReset(user: User) {
    setNovaSenha('')
    setConfirmacao('')
    setEditTarget({ type: 'reset', user })
  }

  function openEditUser(user: User) {
    setEditSuperiorId(user.superior_id ?? '')
    setEditPerfil(user.perfil)
    setEditAtivo(user.ativo)
    setEditTarget({ type: 'user', user })
  }

  function openEditVehicle(vehicle: Vehicle) {
    setEditVeiculoResponsavel(vehicle.usuario_responsavel_id ?? '')
    setEditVeiculoDisponibilidade(vehicle.tipo_disponibilidade)
    setEditVeiculoUnidade(vehicle.unidade ?? '')
    setEditVeiculoAtivo(vehicle.ativo)
    setEditTarget({ type: 'vehicle', vehicle })
  }

  async function handleReset() {
    if (!editTarget || editTarget.type !== 'reset') return
    if (!novaSenha || novaSenha.length < 8) { onMessage('Minimo 8 caracteres.'); return }
    if (novaSenha !== confirmacao) { onMessage('As senhas nao conferem.'); return }
    setSaving(true)
    try {
      await api.adminResetPassword(token, editTarget.user.id, novaSenha)
      onMessage(`Senha de ${editTarget.user.nome} redefinida.`)
      closeModal()
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Erro ao redefinir senha.')
    } finally { setSaving(false) }
  }

  async function handleSaveUser() {
    if (!editTarget || editTarget.type !== 'user') return
    setSaving(true)
    try {
      await api.patchUser(token, editTarget.user.id, {
        superior_id: editSuperiorId || null,
        perfil: editPerfil,
        ativo: editAtivo,
      })
      onMessage(`${editTarget.user.nome} atualizado.`)
      closeModal()
      await load()
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Erro ao atualizar usuario.')
    } finally { setSaving(false) }
  }

  async function handleSaveVehicle() {
    if (!editTarget || editTarget.type !== 'vehicle') return
    setSaving(true)
    try {
      await api.patchVehicle(token, editTarget.vehicle.id, {
        usuario_responsavel_id: editVeiculoResponsavel || null,
        tipo_disponibilidade: editVeiculoDisponibilidade,
        unidade: editVeiculoUnidade || null,
        ativo: editVeiculoAtivo,
      })
      onMessage(`Veiculo ${editTarget.vehicle.placa} atualizado.`)
      closeModal()
      await load()
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Erro ao atualizar veiculo.')
    } finally { setSaving(false) }
  }

  function userName(id: string | null) {
    if (!id) return '—'
    return users.find((u) => u.id === id)?.nome ?? '—'
  }

  return (
    <section className="panel">
      <div className="section-title">
        <Users />
        <div>
          <h2>Gerenciamento</h2>
          <p>Usuarios, veiculos e hierarquia</p>
        </div>
      </div>

      <div className="action-row">
        <button className="secondary-button" type="button" onClick={() => void load()} disabled={loading}>
          {loading ? <Loader2 className="spin" /> : <RefreshCw />}
          <span>Atualizar</span>
        </button>
      </div>

      <div className="tab-bar">
        <button className={tab === 'users' ? 'active' : ''} type="button" onClick={() => { setTab('users'); setSearch('') }}>
          <Users /> Usuarios ({users.length})
        </button>
        <button className={tab === 'vehicles' ? 'active' : ''} type="button" onClick={() => { setTab('vehicles'); setSearch('') }}>
          <CarFront /> Veiculos ({vehicles.length})
        </button>
      </div>

      <div className="search-bar">
        <Search />
        <input
          type="text"
          placeholder={tab === 'users' ? 'Buscar por nome ou email...' : 'Buscar por placa, modelo ou unidade...'}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {tab === 'users' ? (
        <div className="user-list">
          {(filtered as User[]).map((u) => (
            <div className="user-row" key={u.id}>
              <div className="user-row-info">
                <strong>{u.nome}</strong>
                <span className="user-row-email">
                  {u.cargo ?? u.perfil} {u.superior_id ? `| Sup: ${userName(u.superior_id).split(' ')[0]}` : ''}
                </span>
              </div>
              <div className="user-row-actions">
                <button className="user-row-btn" type="button" onClick={() => openEditUser(u)} aria-label="Editar">
                  <Edit3 />
                </button>
                <button className="user-row-btn" type="button" onClick={() => openReset(u)} aria-label="Redefinir senha">
                  <KeyRound />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="user-list">
          {(filtered as Vehicle[]).map((v) => (
            <div className="user-row" key={v.id}>
              <div className="user-row-info">
                <strong>{v.placa} | {v.modelo}</strong>
                <span className="user-row-email">
                  {v.responsavel_nome ?? '—'} | {v.unidade ?? '—'} | {v.ativo ? 'Ativo' : 'Inativo'}
                </span>
              </div>
              <div className="user-row-actions">
                <button className="user-row-btn" type="button" onClick={() => openEditVehicle(v)} aria-label="Editar veiculo">
                  <Edit3 />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {!filtered.length ? <div className="empty-state">Nenhum resultado encontrado.</div> : null}

      {editTarget?.type === 'reset' ? (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Redefinir senha</h3>
              <button className="icon-button" type="button" onClick={closeModal}><X /></button>
            </div>
            <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              {editTarget.user.nome}
            </p>
            <PasswordInput
              label="Nova senha"
              value={novaSenha}
              onChange={(e) => setNovaSenha(e.target.value)}
              placeholder="Minimo 8 caracteres"
              autoFocus
            />
            <PasswordInput
              label="Confirmar senha"
              value={confirmacao}
              onChange={(e) => setConfirmacao(e.target.value)}
              placeholder="Repita a nova senha"
            />
            <div className="action-row">
              <button className="primary-button compact" type="button" onClick={() => void handleReset()} disabled={saving}>
                {saving ? <Loader2 className="spin" /> : <KeyRound />} <span>Redefinir</span>
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {editTarget?.type === 'user' ? (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Editar usuario</h3>
              <button className="icon-button" type="button" onClick={closeModal}><X /></button>
            </div>
            <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              {editTarget.user.nome}
            </p>
            <label><span>Perfil</span>
              <select value={editPerfil} onChange={(e) => setEditPerfil(e.target.value)}>
                <option value="motorista">Motorista</option>
                <option value="supervisor">Supervisor</option>
                <option value="analista">Analista</option>
                <option value="admin">Admin</option>
              </select>
            </label>
            <label><span>Superior</span>
              <select value={editSuperiorId} onChange={(e) => setEditSuperiorId(e.target.value)}>
                <option value="">Sem superior</option>
                {users.filter((u) => u.id !== editTarget.user.id).map((u) => (
                  <option key={u.id} value={u.id}>{u.nome}</option>
                ))}
              </select>
            </label>
            <label className="checkbox-row">
              <input type="checkbox" checked={editAtivo} onChange={(e) => setEditAtivo(e.target.checked)} />
              <span>Ativo</span>
            </label>
            <div className="action-row">
              <button className="primary-button compact" type="button" onClick={() => void handleSaveUser()} disabled={saving}>
                {saving ? <Loader2 className="spin" /> : <Save />} <span>Salvar</span>
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {editTarget?.type === 'vehicle' ? (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Editar veiculo</h3>
              <button className="icon-button" type="button" onClick={closeModal}><X /></button>
            </div>
            <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              {editTarget.vehicle.placa} | {editTarget.vehicle.modelo}
            </p>
            <label><span>Responsavel</span>
              <select value={editVeiculoResponsavel} onChange={(e) => setEditVeiculoResponsavel(e.target.value)}>
                <option value="">Sem responsavel</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>{u.nome}</option>
                ))}
              </select>
            </label>
            <label><span>Disponibilidade</span>
              <select value={editVeiculoDisponibilidade} onChange={(e) => setEditVeiculoDisponibilidade(e.target.value)}>
                <option value="fixo">Fixo</option>
                <option value="alocado">Alocado</option>
              </select>
            </label>
            <label><span>Unidade</span>
              <input type="text" value={editVeiculoUnidade} onChange={(e) => setEditVeiculoUnidade(e.target.value)} />
            </label>
            <label className="checkbox-row">
              <input type="checkbox" checked={editVeiculoAtivo} onChange={(e) => setEditVeiculoAtivo(e.target.checked)} />
              <span>Ativo</span>
            </label>
            <div className="action-row">
              <button className="primary-button compact" type="button" onClick={() => void handleSaveVehicle()} disabled={saving}>
                {saving ? <Loader2 className="spin" /> : <Save />} <span>Salvar</span>
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  )
}
