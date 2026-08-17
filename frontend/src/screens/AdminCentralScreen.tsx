import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  CarFront,
  ChevronDown,
  ChevronRight,
  Edit3,
  FileText,
  Filter,
  Inbox,
  KeyRound,
  Loader2,
  MoreVertical,
  Save,
  Search,
  Upload,
  UserPlus,
  X,
} from 'lucide-react'
import { PasswordInput } from '../components/PasswordInput'
import { StatusPill } from '../components/StatusPill'
import { ApiError, api } from '../services/api'
import type { User, Vehicle, VehicleInRoute } from '../types/domain'
import { CARGO_OPTIONS } from '../utils/cargos'
import { SignupRequestsScreen } from './SignupRequestsScreen'
import { RegisterDriverScreen } from './RegisterDriverScreen'
import { RegisterVehicleScreen } from './RegisterVehicleScreen'
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
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [vehicleTab, setVehicleTab] = useState(false)
  const [filterCargo, setFilterCargo] = useState('')
  const [filterUsuarioId, setFilterUsuarioId] = useState('')
  const [filterVeiculoId, setFilterVeiculoId] = useState('')
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [showInactive, setShowInactive] = useState(false)
  const [editTarget, setEditTarget] = useState<EditTarget | null>(null)
  const [actionsTarget, setActionsTarget] = useState<
    { type: 'user'; user: User } | { type: 'vehicle'; vehicle: Vehicle } | null
  >(null)
  const [saving, setSaving] = useState(false)
  const [cadastroView, setCadastroView] = useState<'pendentes' | 'novo' | 'novo_veiculo'>('pendentes')

  const [novaSenha, setNovaSenha] = useState('')
  const [confirmacao, setConfirmacao] = useState('')
  const [editEmail, setEditEmail] = useState('')
  const [editCargo, setEditCargo] = useState('')
  const [editSuperiorId, setEditSuperiorId] = useState('')
  const [editPerfil, setEditPerfil] = useState('')
  const [editPodeAprovar, setEditPodeAprovar] = useState(false)
  const [editAtivo, setEditAtivo] = useState(true)
  const [editInativarVeiculo, setEditInativarVeiculo] = useState(false)
  const [cnhArquivo, setCnhArquivo] = useState<File | null>(null)

  const [editVeiculoResponsavel, setEditVeiculoResponsavel] = useState('')
  const [editVeiculoDisponibilidade, setEditVeiculoDisponibilidade] = useState('')
  const [editVeiculoUnidade, setEditVeiculoUnidade] = useState('')
  const [editVeiculoAtivo, setEditVeiculoAtivo] = useState(true)
  const [editVeiculoPrincipal, setEditVeiculoPrincipal] = useState(false)
  const [apoliceArquivo, setApoliceArquivo] = useState<File | null>(null)
  const [uploadingDoc, setUploadingDoc] = useState(false)

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
    if (!showInactive) {
      list = list.filter((u) => u.ativo)
    }
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
    if (!showInactive || filterCargo || filterUsuarioId || filterVeiculoId || search.trim()) {
      const validIds = new Set(applyUserFilters(users).map((u) => u.id))
      return pruneHierarchy(hierarchy, validIds)
    }
    return hierarchy
  }, [hierarchy, filterCargo, filterUsuarioId, filterVeiculoId, users, vehicles, search, usuariosByCargo, showInactive])

  const filteredVehicles = useMemo(() => {
    let list = vehicles
    if (!showInactive) {
      list = list.filter((v) => v.ativo)
    }
    if (!search.trim()) return list
    const term = search.toLowerCase()
    return list.filter(
      (v) =>
        v.placa.toLowerCase().includes(term) ||
        v.modelo.toLowerCase().includes(term) ||
        (v.unidade ?? '').toLowerCase().includes(term),
    )
  }, [vehicles, search, showInactive])

  function closeModal() {
    setEditTarget(null)
    setNovaSenha('')
    setConfirmacao('')
    setCnhArquivo(null)
    setApoliceArquivo(null)
  }

  function closeActions() {
    setActionsTarget(null)
  }

  function openReset(u: User) {
    setNovaSenha('')
    setConfirmacao('')
    setEditTarget({ type: 'reset', user: u })
  }

  function openEditUser(u: User) {
    setEditEmail(u.email)
    setEditCargo(u.cargo ?? '')
    setEditSuperiorId(u.superior_id ?? '')
    setEditPerfil(u.perfil)
    setEditPodeAprovar(u.pode_aprovar)
    setEditAtivo(u.ativo)
    setEditInativarVeiculo(false)
    setCnhArquivo(null)
    setEditTarget({ type: 'user', user: u })
  }

  function openEditVehicle(vehicle: Vehicle) {
    setEditVeiculoResponsavel(vehicle.usuario_responsavel_id ?? '')
    setEditVeiculoDisponibilidade(vehicle.tipo_disponibilidade)
    setEditVeiculoUnidade(vehicle.unidade ?? '')
    setEditVeiculoAtivo(vehicle.ativo)
    setEditVeiculoPrincipal(vehicle.principal)
    setApoliceArquivo(null)
    setEditTarget({ type: 'vehicle', vehicle })
  }

  async function openDocument(downloadUrl: string | null) {
    if (!downloadUrl) {
      onMessage('Nenhum arquivo anexado ainda.')
      return
    }
    try {
      const blob = await api.photo(token, downloadUrl)
      window.open(URL.createObjectURL(blob), '_blank', 'noopener,noreferrer')
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Nao foi possivel abrir o arquivo.')
    }
  }

  async function handleUploadCnh() {
    if (!editTarget || editTarget.type !== 'user' || !cnhArquivo) return
    setUploadingDoc(true)
    try {
      const atualizado = await api.uploadUserCnh(token, editTarget.user.id, cnhArquivo)
      setEditTarget({ type: 'user', user: atualizado })
      setCnhArquivo(null)
      onMessage(`CNH de ${atualizado.nome} enviada.`)
      await load()
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Erro ao enviar CNH.')
    } finally {
      setUploadingDoc(false)
    }
  }

  async function handleUploadApolice() {
    if (!editTarget || editTarget.type !== 'vehicle' || !apoliceArquivo) return
    setUploadingDoc(true)
    try {
      const atualizado = await api.uploadVehicleApolice(token, editTarget.vehicle.id, apoliceArquivo)
      setEditTarget({ type: 'vehicle', vehicle: atualizado })
      setApoliceArquivo(null)
      onMessage(`Apolice de ${atualizado.placa} enviada.`)
      await load()
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Erro ao enviar apolice.')
    } finally {
      setUploadingDoc(false)
    }
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
    if (!editEmail.trim()) { onMessage('Informe o e-mail do usuario.'); return }
    setSaving(true)
    try {
      await api.patchUser(token, editTarget.user.id, {
        email: editEmail.trim(),
        cargo: editCargo.trim() || null,
        superior_id: editSuperiorId || null,
        perfil: editPerfil,
        pode_aprovar: editPodeAprovar,
        ativo: editAtivo,
      })
      if (!editAtivo && editInativarVeiculo) {
        const veiculosVinculados = vehicles.filter(
          (v) => v.usuario_responsavel_id === editTarget.user.id && v.ativo,
        )
        for (const veiculo of veiculosVinculados) {
          await api.patchVehicle(token, veiculo.id, { ativo: false })
        }
      }
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
        principal: editVeiculoPrincipal,
      })
      onMessage(`Veiculo ${editTarget.vehicle.placa} atualizado.`)
      closeModal()
      await load()
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Erro ao atualizar veiculo.')
    } finally { setSaving(false) }
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

          <div className="toggle-row">
            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={showInactive}
                onChange={(e) => setShowInactive(e.target.checked)}
              />
              <span>Mostrar inativos</span>
            </label>
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
              {loading && !users.length ? (
                <div className="empty-state"><Loader2 className="spin" /> Carregando...</div>
              ) : (
                <>
                  {filteredHierarchy.map((node) => (
                    <HierarchyNodeView
                      key={node.user.id}
                      node={node}
                      level={0}
                      users={users}
                      onOpenActions={(u) => setActionsTarget({ type: 'user', user: u })}
                    />
                  ))}
                  {!filteredHierarchy.length ? (
                    <div className="empty-state">Nenhum usuario encontrado.</div>
                  ) : null}
                </>
              )}
            </div>
          ) : null}

          {vehicleTab ? (
            <>
              {loading && !vehicles.length ? (
                <div className="empty-state"><Loader2 className="spin" /> Carregando...</div>
              ) : (
                <>
                  <div className="user-list">
                    {filteredVehicles.map((v) => (
                      <div className="user-row" key={v.id}>
                        <div className="user-row-info">
                          <strong>{v.placa} | {v.modelo}{v.principal ? ' | Principal' : ''}</strong>
                          <span className="user-row-email">
                            {v.responsavel_nome ?? '—'} | {v.unidade ?? '—'} | {v.ativo ? 'Ativo' : 'Inativo'}
                          </span>
                        </div>
                        <div className="user-row-actions">
                          <button
                            className="user-row-btn"
                            type="button"
                            onClick={() => setActionsTarget({ type: 'vehicle', vehicle: v })}
                            aria-label="Mais opcoes"
                          >
                            <MoreVertical />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                  {!filteredVehicles.length ? <div className="empty-state">Nenhum resultado encontrado.</div> : null}
                </>
              )}
            </>
          ) : null}

          {/* Folha de acoes (usuario ou veiculo) */}
          {actionsTarget ? (
            <div className="modal-overlay" onClick={closeActions}>
              <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>
                    {actionsTarget.type === 'user'
                      ? actionsTarget.user.nome
                      : `${actionsTarget.vehicle.placa} | ${actionsTarget.vehicle.modelo}`}
                  </h3>
                  <button className="icon-button" type="button" onClick={closeActions} aria-label="Fechar">
                    <X />
                  </button>
                </div>
                <div className="action-sheet-list">
                  {actionsTarget.type === 'user' ? (
                    <>
                      <button
                        className="action-sheet-item"
                        type="button"
                        onClick={() => { openEditUser(actionsTarget.user); closeActions() }}
                      >
                        <Edit3 /> <span>Editar usuario</span>
                      </button>
                      <button
                        className="action-sheet-item"
                        type="button"
                        onClick={() => { openReset(actionsTarget.user); closeActions() }}
                      >
                        <KeyRound /> <span>Redefinir senha</span>
                      </button>
                      <button
                        className="action-sheet-item"
                        type="button"
                        onClick={() => { void openDocument(actionsTarget.user.cnh_download_url); closeActions() }}
                      >
                        <FileText /> <span>Ver CNH</span>
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="action-sheet-item"
                        type="button"
                        onClick={() => { openEditVehicle(actionsTarget.vehicle); closeActions() }}
                      >
                        <Edit3 /> <span>Editar veiculo</span>
                      </button>
                      <button
                        className="action-sheet-item"
                        type="button"
                        onClick={() => { void openDocument(actionsTarget.vehicle.apolice_download_url); closeActions() }}
                      >
                        <FileText /> <span>Ver apolice</span>
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
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
                <div className="modal-section-title">Dados</div>
                <label><span>E-mail</span>
                  <input
                    type="email"
                    value={editEmail}
                    onChange={(e) => setEditEmail(e.target.value)}
                  />
                </label>
                <label><span>Cargo</span>
                  <select value={editCargo} onChange={(e) => setEditCargo(e.target.value)}>
                    <option value="">Sem cargo</option>
                    {CARGO_OPTIONS.map((cargo) => (
                      <option key={cargo} value={cargo}>{cargo}</option>
                    ))}
                  </select>
                </label>
                <label><span>Perfil</span>
                  <select value={editPerfil} onChange={(e) => setEditPerfil(e.target.value)}>
                    <option value="motorista">Motorista</option>
                    <option value="supervisor">Supervisor</option>
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
                  <input
                    type="checkbox"
                    checked={editPodeAprovar}
                    onChange={(e) => setEditPodeAprovar(e.target.checked)}
                  />
                  <span>Pode fechar mensalmente (ve e fecha fechamento dos subordinados)</span>
                </label>
                <label className="checkbox-row">
                  <input type="checkbox" checked={editAtivo} onChange={(e) => setEditAtivo(e.target.checked)} />
                  <span>Ativo</span>
                </label>
                {(() => {
                  const veiculosVinculados = vehicles.filter(
                    (v) => v.usuario_responsavel_id === editTarget.user.id && v.ativo,
                  )
                  if (editAtivo || !veiculosVinculados.length) return null
                  return (
                    <label className="checkbox-row">
                      <input
                        type="checkbox"
                        checked={editInativarVeiculo}
                        onChange={(e) => setEditInativarVeiculo(e.target.checked)}
                      />
                      <span>
                        Inativar tambem o(s) veiculo(s) vinculado(s) ({veiculosVinculados.map((v) => v.placa).join(', ')})
                      </span>
                    </label>
                  )
                })()}
                <div className="action-row">
                  <button className="primary-button compact" type="button" onClick={() => void handleSaveUser()} disabled={saving}>
                    {saving ? <Loader2 className="spin" /> : <Save />} <span>Salvar</span>
                  </button>
                </div>

                <div className="modal-section-title">Documentos</div>
                <label><span>CNH do motorista</span>
                  <input
                    type="file"
                    accept="application/pdf,image/jpeg,image/png,image/webp"
                    onChange={(e) => setCnhArquivo(e.target.files?.[0] ?? null)}
                  />
                </label>
                <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                  {editTarget.user.cnh_download_url ? 'CNH ja anexada.' : 'Nenhuma CNH anexada ainda.'}
                </p>
                <div className="action-row">
                  <button
                    className="secondary-button compact"
                    type="button"
                    onClick={() => void openDocument(editTarget.user.cnh_download_url)}
                  >
                    <FileText /> <span>Ver CNH</span>
                  </button>
                  <button
                    className="primary-button compact"
                    type="button"
                    onClick={() => void handleUploadCnh()}
                    disabled={uploadingDoc || !cnhArquivo}
                  >
                    {uploadingDoc ? <Loader2 className="spin" /> : <Upload />}
                    <span>{editTarget.user.cnh_download_url ? 'Substituir CNH' : 'Enviar CNH'}</span>
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
                <div className="modal-section-title">Dados</div>
                <label><span>Responsavel</span>
                  <select
                    value={editVeiculoResponsavel}
                    onChange={(e) => {
                      setEditVeiculoResponsavel(e.target.value)
                      if (!e.target.value) setEditVeiculoPrincipal(false)
                    }}
                  >
                    <option value="">Sem responsavel</option>
                    {users
                      .filter((u) => u.ativo || u.id === editTarget.vehicle.usuario_responsavel_id)
                      .map((u) => (
                        <option key={u.id} value={u.id}>{u.nome}{!u.ativo ? ' | Inativo' : ''}</option>
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
                  <input
                    type="checkbox"
                    checked={editVeiculoPrincipal}
                    disabled={!editVeiculoResponsavel}
                    onChange={(e) => setEditVeiculoPrincipal(e.target.checked)}
                  />
                  <span>Veiculo principal do responsavel (aparece primeiro para o motorista)</span>
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

                <div className="modal-section-title">Documentos</div>
                <label><span>Apolice de seguro</span>
                  <input
                    type="file"
                    accept="application/pdf,image/jpeg,image/png,image/webp"
                    onChange={(e) => setApoliceArquivo(e.target.files?.[0] ?? null)}
                  />
                </label>
                <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                  {editTarget.vehicle.apolice_download_url ? 'Apolice ja anexada.' : 'Nenhuma apolice anexada ainda.'}
                </p>
                <div className="action-row">
                  <button
                    className="secondary-button compact"
                    type="button"
                    onClick={() => void openDocument(editTarget.vehicle.apolice_download_url)}
                  >
                    <FileText /> <span>Ver apolice</span>
                  </button>
                  <button
                    className="primary-button compact"
                    type="button"
                    onClick={() => void handleUploadApolice()}
                    disabled={uploadingDoc || !apoliceArquivo}
                  >
                    {uploadingDoc ? <Loader2 className="spin" /> : <Upload />}
                    <span>{editTarget.vehicle.apolice_download_url ? 'Substituir apolice' : 'Enviar apolice'}</span>
                  </button>
                </div>
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      {tab === 'cadastros' ? (
        <div className="screen-stack">
          <div className="segmented-control segmented-control-grid" aria-label="Modo de cadastro">
            <button
              type="button"
              className={cadastroView === 'pendentes' ? 'active' : ''}
              onClick={() => setCadastroView('pendentes')}
            >
              <Inbox />
              <span>Solicitacoes</span>
            </button>
            <button
              type="button"
              className={cadastroView === 'novo' ? 'active' : ''}
              onClick={() => setCadastroView('novo')}
            >
              <UserPlus />
              <span>Cadastro direto</span>
            </button>
            <button
              type="button"
              className={cadastroView === 'novo_veiculo' ? 'active' : ''}
              onClick={() => setCadastroView('novo_veiculo')}
            >
              <CarFront />
              <span>So veiculo</span>
            </button>
          </div>

          {cadastroView === 'novo' ? (
            <RegisterDriverScreen
              token={token}
              users={users}
              onMessage={onMessage}
              onBack={() => setCadastroView('pendentes')}
              onCreated={() => { setCadastroView('pendentes'); void load() }}
            />
          ) : cadastroView === 'novo_veiculo' ? (
            <RegisterVehicleScreen
              token={token}
              users={users}
              onMessage={onMessage}
              onBack={() => setCadastroView('pendentes')}
              onCreated={() => { setCadastroView('pendentes'); void load() }}
            />
          ) : (
            <SignupRequestsScreen token={token} onMessage={onMessage} />
          )}
        </div>
      ) : null}

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
  onOpenActions,
}: {
  node: HierarchyNode
  level: number
  users: User[]
  onOpenActions: (u: User) => void
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
          {u.perfil === 'supervisor' ? <StatusPill status={u.perfil} /> : null}
          <button className="user-row-btn" type="button" onClick={() => onOpenActions(u)} aria-label="Mais opcoes">
            <MoreVertical />
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
              onOpenActions={onOpenActions}
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
