import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  CarFront,
  ChevronDown,
  ChevronRight,
  Edit3,
  Filter,
  KeyRound,
  Loader2,
  Save,
  Search,
  X,
} from 'lucide-react'
import { PasswordInput } from '../components/PasswordInput'
import { StatusPill } from '../components/StatusPill'
import { ApiError, api } from '../services/api'
import type { User, Vehicle, VehicleInRoute } from '../types/domain'
import { SignupRequestsScreen } from './SignupRequestsScreen'
import { MonthlyClosureScreen } from './MonthlyClosureScreen'

export type AdminTab = 'usuarios' | 'cadastros' | 'em_rota' | 'fechamento'
type EditTarget = { type: 'reset'; user: User } | { type: 'user'; user: User } | { type: 'vehicle'; vehicle: Vehicle }

interface AdminCentralScreenProps {
  token: string
  user: User
  vehiclesInRoute: VehicleInRoute[]
  tab: AdminTab
  onMessage: (message: string) => void
}

interface HierarchyNode {
  user: User
  subordinados: HierarchyNode[]
}

function buildHierarchy(users: User[]): HierarchyNode[] {
  const nodeMap = new Map<string, HierarchyNode>()
  for (const u of users) {
    nodeMap.set(u.id, { user: u, subordinados: [] })
  }
  const roots: HierarchyNode[] = []
  for (const u of users) {
    const node = nodeMap.get(u.id)!
    if (u.superior_id && nodeMap.has(u.superior_id)) {
      nodeMap.get(u.superior_id)!.subordinados.push(node)
    } else {
      roots.push(node)
    }
  }
  return roots
}

const dateTimeFormatter = new Intl.DateTimeFormat('pt-BR', {
  timeZone: 'America/Cuiaba',
  day: '2-digit',
  month: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
})

export function AdminCentralScreen({ token, user, vehiclesInRoute, tab, onMessage }: AdminCentralScreenProps) {
  const [users, setUsers] = useState<User[]>([])
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [search, setSearch] = useState('')
  const [vehicleTab, setVehicleTab] = useState(false)
  const [filterCargo, setFilterCargo] = useState('')
  const [filterUsuarioId, setFilterUsuarioId] = useState('')
  const [filterVeiculoId, setFilterVeiculoId] = useState('')
  const [filtersOpen, setFiltersOpen] = useState(false)
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
    try {
      const [u, v] = await Promise.all([api.users(token), api.allVehicles(token)])
      setUsers(u)
      setVehicles(v)
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Nao foi possivel carregar os dados.')
    }
  }, [onMessage, token])

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0)
    return () => window.clearTimeout(timeout)
  }, [load])

  const hierarchy = useMemo(() => buildHierarchy(users), [users])

  const cargos = useMemo(() => {
    const set = new Set<string>()
    for (const u of users) {
      if (u.cargo) set.add(u.cargo)
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b, 'pt-BR'))
  }, [users])

  const usuariosByCargo = useMemo(() => {
    if (!filterCargo) return users.filter((u) => u.cargo)
    return users.filter((u) => u.cargo === filterCargo)
  }, [users, filterCargo])

  const veiculosByUsuario = useMemo(() => {
    if (filterUsuarioId) {
      return vehicles.filter((v) => v.usuario_responsavel_id === filterUsuarioId)
    }
    if (filterCargo) {
      const ids = new Set(usuariosByCargo.map((u) => u.id))
      return vehicles.filter((v) => v.usuario_responsavel_id && ids.has(v.usuario_responsavel_id))
    }
    return vehicles.filter((v) => v.usuario_responsavel_id)
  }, [vehicles, filterUsuarioId, filterCargo, usuariosByCargo])

  const activeFilterCount = [filterCargo, filterUsuarioId, filterVeiculoId].filter(Boolean).length

  useEffect(() => {
    if (filterCargo && filterUsuarioId) {
      const stillValid = usuariosByCargo.some((u) => u.id === filterUsuarioId)
      if (!stillValid) { setFilterUsuarioId(''); setFilterVeiculoId('') }
    }
  }, [filterCargo, filterUsuarioId, usuariosByCargo])

  useEffect(() => {
    if (filterUsuarioId && filterVeiculoId) {
      const stillValid = veiculosByUsuario.some((v) => v.id === filterVeiculoId)
      if (!stillValid) setFilterVeiculoId('')
    }
  }, [filterUsuarioId, filterVeiculoId, veiculosByUsuario])

  function applyUserFilters(list: User[]): User[] {
    if (filterUsuarioId) {
      list = list.filter((u) => u.id === filterUsuarioId)
    } else if (filterCargo) {
      list = list.filter((u) => u.cargo === filterCargo)
    }
    if (filterVeiculoId) {
      const vehicle = vehicles.find((v) => v.id === filterVeiculoId)
      if (vehicle?.usuario_responsavel_id) {
        list = list.filter((u) => u.id === vehicle.usuario_responsavel_id)
      }
    }
    if (search.trim()) {
      const term = search.toLowerCase()
      list = list.filter(
        (u) => u.nome.toLowerCase().includes(term) || u.email.toLowerCase().includes(term),
      )
    }
    return list
  }

  const filteredHierarchy = useMemo(() => {
    if (filterCargo || filterUsuarioId || filterVeiculoId || search.trim()) {
      const validIds = new Set(applyUserFilters(users).map((u) => u.id))
      return pruneHierarchy(hierarchy, validIds)
    }
    return hierarchy
  }, [hierarchy, filterCargo, filterUsuarioId, filterVeiculoId, users, vehicles, search, usuariosByCargo])

  const filteredVehicles = useMemo(() => {
    if (!search.trim()) return vehicles
    const term = search.toLowerCase()
    return vehicles.filter(
      (v) =>
        v.placa.toLowerCase().includes(term) ||
        v.modelo.toLowerCase().includes(term) ||
        (v.unidade ?? '').toLowerCase().includes(term),
    )
  }, [vehicles, search])

  function closeModal() {
    setEditTarget(null)
    setNovaSenha('')
    setConfirmacao('')
  }

  function openReset(u: User) {
    setNovaSenha('')
    setConfirmacao('')
    setEditTarget({ type: 'reset', user: u })
  }

  function openEditUser(u: User) {
    setEditSuperiorId(u.superior_id ?? '')
    setEditPerfil(u.perfil)
    setEditAtivo(u.ativo)
    setEditTarget({ type: 'user', user: u })
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

  useEffect(() => {
    setSearch('')
  }, [tab])

  return (
    <div className="screen-stack">
      {tab === 'usuarios' ? (
        <section className="panel panel-edge-bottom">
          <div className="segmented-control" aria-label="Visao de usuarios">
            <button
              type="button"
              className={!vehicleTab ? 'active' : ''}
              onClick={() => { setVehicleTab(false); setSearch('') }}
            >
              <ChevronRight />
              <span>Hierarquia</span>
            </button>
            <button
              type="button"
              className={vehicleTab ? 'active' : ''}
              onClick={() => { setVehicleTab(true); setSearch('') }}
            >
              <CarFront />
              <span>Veiculos</span>
            </button>
          </div>

          {!vehicleTab ? (
            <>
              <div className="filter-panel">
                <div className="filter-panel-header">
                  <button
                    className="filter-panel-toggle"
                    type="button"
                    onClick={() => setFiltersOpen((open) => !open)}
                    aria-expanded={filtersOpen}
                  >
                    <Filter />
                    <span>Filtros{activeFilterCount > 0 ? ` (${activeFilterCount})` : ''}</span>
                    {filtersOpen ? <ChevronDown /> : <ChevronRight />}
                  </button>
                  {activeFilterCount > 0 ? (
                    <button
                      className="link-button"
                      type="button"
                      onClick={() => { setFilterCargo(''); setFilterUsuarioId(''); setFilterVeiculoId('') }}
                    >
                      Limpar filtros
                    </button>
                  ) : null}
                </div>

                {filtersOpen ? (
                  <div className="filter-panel-grid">
                    <label>
                      <span>Cargo</span>
                      <select
                        value={filterCargo}
                        onChange={(e) => { setFilterCargo(e.target.value); setFilterUsuarioId(''); setFilterVeiculoId('') }}
                      >
                        <option value="">Todos</option>
                        {cargos.map((c) => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </label>

                    <label>
                      <span>Usuario</span>
                      <select
                        value={filterUsuarioId}
                        onChange={(e) => { setFilterUsuarioId(e.target.value); setFilterVeiculoId('') }}
                      >
                        <option value="">Todos</option>
                        {usuariosByCargo.map((u) => (
                          <option key={u.id} value={u.id}>{u.nome}</option>
                        ))}
                      </select>
                    </label>

                    <label>
                      <span>Veiculo</span>
                      <select
                        value={filterVeiculoId}
                        onChange={(e) => setFilterVeiculoId(e.target.value)}
                      >
                        <option value="">Todos</option>
                        {veiculosByUsuario.map((v) => (
                          <option key={v.id} value={v.id}>{v.placa} | {v.modelo}</option>
                        ))}
                      </select>
                    </label>
                  </div>
                ) : null}

                <div className="search-bar">
                  <Search />
                  <input
                    type="text"
                    placeholder="Buscar por nome ou email..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>
              </div>
            </>
          ) : (
            <div className="search-bar">
              <Search />
              <input
                type="text"
                placeholder="Buscar por placa, modelo ou unidade..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          )}

          {!vehicleTab ? (
            <div className="hierarchy-tree">
              {filteredHierarchy.map((node) => (
                <HierarchyNodeView
                  key={node.user.id}
                  node={node}
                  level={0}
                  users={users}
                  onEditUser={openEditUser}
                  onResetPassword={openReset}
                  userName={userName}
                />
              ))}
              {!filteredHierarchy.length ? (
                <div className="empty-state">Nenhum usuario encontrado.</div>
              ) : null}
            </div>
          ) : null}

          {vehicleTab ? (
            <>
              <div className="user-list">
                {filteredVehicles.map((v) => (
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
              {!filteredVehicles.length ? <div className="empty-state">Nenhum resultado encontrado.</div> : null}
            </>
          ) : null}

          {/* Modals */}
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
      ) : null}

      {tab === 'cadastros' ? <SignupRequestsScreen token={token} onMessage={onMessage} /> : null}

      {tab === 'em_rota' ? (
        <section className="panel panel-edge-bottom">
          <div className="closure-summary">
            <div>
              <span>Veiculos em rota</span>
              <strong>{vehiclesInRoute.length}</strong>
            </div>
          </div>

          {!vehiclesInRoute.length ? <div className="empty-state">Nenhum veiculo em rota agora.</div> : null}

          <div className="item-list">
            {vehiclesInRoute.map((item) => (
              <article className="list-card route-card" key={item.viagem_id}>
                <div className="list-card-main">
                  <div>
                    <strong>{item.placa} | {item.modelo}</strong>
                    <span>{item.motorista_nome}</span>
                  </div>
                  <StatusPill status="em_rota" />
                </div>
                <div className="metric-row">
                  <span>Inicio {dateTimeFormatter.format(new Date(item.partida_em))}</span>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {tab === 'fechamento' ? <MonthlyClosureScreen token={token} user={user} onMessage={onMessage} /> : null}
    </div>
  )
}

function HierarchyNodeView({
  node,
  level,
  users,
  onEditUser,
  onResetPassword,
  userName,
}: {
  node: HierarchyNode
  level: number
  users: User[]
  onEditUser: (u: User) => void
  onResetPassword: (u: User) => void
  userName: (id: string | null) => string
}) {
  const [expanded, setExpanded] = useState(level < 2)
  const hasChildren = node.subordinados.length > 0
  const u = node.user

  return (
    <div className="hierarchy-node">
      <div className="hierarchy-card">
        <div className="hierarchy-card-left">
          {hasChildren ? (
            <button
              className="hierarchy-toggle"
              type="button"
              onClick={() => setExpanded(!expanded)}
              aria-label={expanded ? 'Recolher' : 'Expandir'}
            >
              {expanded ? <ChevronDown /> : <ChevronRight />}
            </button>
          ) : (
            <span className="hierarchy-spacer" />
          )}
          <div className="hierarchy-info">
            <strong>{u.nome}</strong>
            <span className="hierarchy-meta">
              {u.cargo ?? u.perfil}
              {!u.ativo ? ' | Inativo' : ''}
              {hasChildren ? ` | ${node.subordinados.length} subordinado${node.subordinados.length > 1 ? 's' : ''}` : ''}
            </span>
          </div>
        </div>
        <div className="hierarchy-card-right">
          <StatusPill status={u.perfil} />
          <button className="user-row-btn" type="button" onClick={() => onEditUser(u)} aria-label="Editar">
            <Edit3 />
          </button>
          <button className="user-row-btn" type="button" onClick={() => onResetPassword(u)} aria-label="Redefinir senha">
            <KeyRound />
          </button>
        </div>
      </div>
      {hasChildren && expanded ? (
        <div className="hierarchy-children">
          {node.subordinados.map((child) => (
            <HierarchyNodeView
              key={child.user.id}
              node={child}
              level={level + 1}
              users={users}
              onEditUser={onEditUser}
              onResetPassword={onResetPassword}
              userName={userName}
            />
          ))}
        </div>
      ) : null}
    </div>
  )
}

function pruneHierarchy(nodes: HierarchyNode[], validIds: Set<string>): HierarchyNode[] {
  const result: HierarchyNode[] = []
  for (const node of nodes) {
    const prunedChildren = pruneHierarchy(node.subordinados, validIds)
    if (validIds.has(node.user.id) || prunedChildren.length > 0) {
      result.push({ user: node.user, subordinados: prunedChildren })
    }
  }
  return result
}
