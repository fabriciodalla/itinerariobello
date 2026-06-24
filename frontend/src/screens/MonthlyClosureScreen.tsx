import { useCallback, useEffect, useMemo, useState } from 'react'
import { Calendar, CarFront, Check, Download, Edit2, Eye, FileText, Loader2, MapPin, ShieldCheck, UserRound, X } from 'lucide-react'
import { StatusPill } from '../components/StatusPill'
import { ApiError, api } from '../services/api'
import type { GpsEvidence, MonthlyClosure, ReportItem, User, Vehicle } from '../types/domain'
import { formatDateTime, formatKm, numberValue } from '../utils/format'

interface MonthlyClosureScreenProps {
  token: string
  user: User
  onMessage: (message: string) => void
}

interface TripEditState {
  kmInicial: string
  kmFinal: string
  rotaUtilizada: string
  saving: boolean
}

type ReportMode = 'motorista' | 'veiculo'

export function MonthlyClosureScreen({ token, user, onMessage }: MonthlyClosureScreenProps) {
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7))
  const [reports, setReports] = useState<ReportItem[]>([])
  const [closures, setClosures] = useState<MonthlyClosure[]>([])
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [reportMode, setReportMode] = useState<ReportMode>('motorista')
  const [selectedMotoristaId, setSelectedMotoristaId] = useState('')
  const [selectedVehicleId, setSelectedVehicleId] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [editingTripId, setEditingTripId] = useState<string | null>(null)
  const [editState, setEditState] = useState<TripEditState | null>(null)

  const [ano, mes] = month.split('-').map(Number)
  const canReview = user.pode_aprovar || user.perfil === 'analista' || user.perfil === 'admin'
  const canEditTrips = user.pode_aprovar || user.perfil === 'admin'
  const canReportByVehicle = user.perfil === 'admin'
  const isVehicleMode = reportMode === 'veiculo'

  const motoristas = useMemo(() => {
    const byId = new Map<string, string>()
    for (const item of reports) {
      byId.set(item.usuario_id, item.usuario_nome)
    }
    return Array.from(byId, ([id, nome]) => ({ id, nome }))
  }, [reports])

  const allocatedVehicles = useMemo(
    () => vehicles.filter((vehicle) => vehicle.tipo_disponibilidade === 'alocado'),
    [vehicles],
  )
  const selectedVehicle = allocatedVehicles.find((vehicle) => vehicle.id === selectedVehicleId) ?? null

  const selectedReports = selectedMotoristaId
    ? reports.filter((item) => item.usuario_id === selectedMotoristaId)
    : reports
  const visibleReports = isVehicleMode ? reports : selectedReports
  const selectedClosure = !isVehicleMode
    ? closures.find((item) => item.motorista_id === selectedMotoristaId) ?? null
    : null
  const kmTotal = visibleReports.reduce((total, item) => total + numberValue(item.km_rodado), 0)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      if (isVehicleMode && !selectedVehicleId) {
        setReports([])
        setClosures([])
        return
      }
      const [monthlyReports, monthlyClosures] = await Promise.all([
        api.monthlyReport(token, ano, mes, undefined, isVehicleMode ? selectedVehicleId : undefined),
        isVehicleMode ? Promise.resolve([]) : api.monthlyClosures(token, ano, mes),
      ])
      setReports(monthlyReports)
      setClosures(monthlyClosures)
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Nao foi possivel carregar o fechamento.')
    } finally {
      setLoading(false)
    }
  }, [ano, isVehicleMode, mes, onMessage, selectedVehicleId, token])

  useEffect(() => {
    if (!canReportByVehicle) {
      return
    }
    api
      .allVehicles(token)
      .then(setVehicles)
      .catch((error) => {
        onMessage(error instanceof ApiError ? error.message : 'Nao foi possivel carregar os veiculos.')
      })
  }, [canReportByVehicle, onMessage, token])

  useEffect(() => {
    if (!canReview) {
      return
    }
    const timeout = window.setTimeout(() => void load(), 0)
    return () => window.clearTimeout(timeout)
  }, [canReview, load])

  async function exportCsv() {
    if (isVehicleMode && !selectedVehicleId) {
      onMessage('Selecione um veiculo alocado para exportar o relatorio.')
      return
    }
    setSaving(true)
    try {
      const blob = await api.exportMonthly(
        token,
        ano,
        mes,
        isVehicleMode ? undefined : selectedMotoristaId || undefined,
        isVehicleMode ? selectedVehicleId : undefined,
      )
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      const prefix = isVehicleMode && selectedVehicle ? `relatorio-veiculo-${selectedVehicle.placa}` : 'relatorio'
      anchor.download = `${prefix}-${ano}-${String(mes).padStart(2, '0')}.pdf`
      anchor.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Nao foi possivel exportar o relatorio.')
    } finally {
      setSaving(false)
    }
  }

  async function openPhoto(downloadUrl: string) {
    try {
      const blob = await api.photo(token, downloadUrl)
      window.open(URL.createObjectURL(blob), '_blank', 'noopener,noreferrer')
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Nao foi possivel abrir a foto.')
    }
  }

  function startEdit(item: ReportItem) {
    setEditingTripId(item.id)
    setEditState({
      kmInicial: String(item.km_inicial ?? ''),
      kmFinal: String(item.km_final ?? ''),
      rotaUtilizada: item.rota_utilizada ?? '',
      saving: false,
    })
  }

  function cancelEdit() {
    setEditingTripId(null)
    setEditState(null)
  }

  function changeReportMode(mode: ReportMode) {
    setReportMode(mode)
    setSelectedMotoristaId('')
    setSelectedVehicleId('')
    setReports([])
    setClosures([])
  }

  async function saveEdit(tripId: string) {
    if (!editState) return
    setEditState((prev) => prev && { ...prev, saving: true })
    try {
      const kmInicial = editState.kmInicial !== '' ? Number(editState.kmInicial) : undefined
      const kmFinal = editState.kmFinal !== '' ? Number(editState.kmFinal) : undefined
      const rotaUtilizada = editState.rotaUtilizada.trim() || undefined
      await api.patchTrip(token, tripId, { km_inicial: kmInicial, km_final: kmFinal, rota_utilizada: rotaUtilizada })
      onMessage('Viagem atualizada.')
      setEditingTripId(null)
      setEditState(null)
      await load()
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Nao foi possivel salvar as alteracoes.')
      setEditState((prev) => prev && { ...prev, saving: false })
    }
  }

  if (!canReview) {
    return (
      <section className="panel">
        <div className="section-title">
          <ShieldCheck />
          <h2>Fechamento mensal</h2>
        </div>
        <div className="empty-state">Seu perfil visualiza apenas viagens proprias.</div>
      </section>
    )
  }

  return (
    <section className="panel">
      <div className="section-title">
        <FileText />
        <h2>Fechamento mensal</h2>
      </div>
      {canReportByVehicle ? (
        <div className="segmented-control" aria-label="Foco do relatorio">
          <button
            type="button"
            className={reportMode === 'motorista' ? 'active' : ''}
            onClick={() => changeReportMode('motorista')}
          >
            <UserRound />
            <span>Por motorista</span>
          </button>
          <button
            type="button"
            className={reportMode === 'veiculo' ? 'active' : ''}
            onClick={() => changeReportMode('veiculo')}
          >
            <CarFront />
            <span>Por veiculo</span>
          </button>
        </div>
      ) : null}
      <div className="filter-row">
        <label>
          <span>Mes</span>
          <input type="month" value={month} onChange={(event) => setMonth(event.target.value)} />
        </label>
        {isVehicleMode ? (
          <label>
            <span>Veiculo alocado</span>
            <select value={selectedVehicleId} onChange={(event) => setSelectedVehicleId(event.target.value)}>
              <option value="">Selecione</option>
              {allocatedVehicles.map((vehicle) => (
                <option key={vehicle.id} value={vehicle.id}>
                  {vehicle.placa} | {vehicle.modelo}
                </option>
              ))}
            </select>
          </label>
        ) : (
          <label>
            <span>Motorista</span>
            <select value={selectedMotoristaId} onChange={(event) => setSelectedMotoristaId(event.target.value)}>
              <option value="">Todos</option>
              {motoristas.map((motorista) => (
                <option key={motorista.id} value={motorista.id}>
                  {motorista.nome}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      <div className="closure-summary">
        <div>
          <span>Total viagens</span>
          <strong>{isVehicleMode ? visibleReports.length : selectedClosure?.total_viagens ?? visibleReports.length}</strong>
        </div>
        <div>
          <span>KM total</span>
          <strong>{formatKm(isVehicleMode ? kmTotal : selectedClosure?.km_total ?? kmTotal)}</strong>
        </div>
        {isVehicleMode ? (
          <div>
            <span>Veiculo</span>
            <strong>{selectedVehicle ? `${selectedVehicle.placa} | ${selectedVehicle.modelo}` : '-'}</strong>
          </div>
        ) : (
          <div>
            <span>Status mensal</span>
            <StatusPill status={selectedClosure?.status ?? 'aberto'} />
          </div>
        )}
      </div>

      <div className="action-row">
        <button className="secondary-button" type="button" onClick={() => void load()} disabled={loading}>
          {loading ? <Loader2 className="spin" /> : <Calendar />}
          <span>Consultar</span>
        </button>
        <button className="secondary-button" type="button" onClick={() => void exportCsv()} disabled={saving}>
          <Download />
          <span>Exportar</span>
        </button>
      </div>

      <div className="item-list">
        {visibleReports.map((item) => (
          <article className="list-card" key={item.id}>
            <div className="list-card-main">
              <div>
                <strong>
                  {isVehicleMode ? item.usuario_nome : `${item.veiculo_placa} | ${item.veiculo_modelo}`}
                </strong>
                <span>{isVehicleMode ? `${item.veiculo_placa} | ${item.veiculo_modelo}` : item.usuario_nome}</span>
              </div>
              <div className="list-card-actions">
                <StatusPill status={item.status} />
                {canEditTrips && item.status === 'concluida' && item.status_fechamento !== 'fechado' && editingTripId !== item.id ? (
                  <button
                    type="button"
                    className="icon-button"
                    title="Editar viagem"
                    onClick={() => startEdit(item)}
                  >
                    <Edit2 size={15} />
                  </button>
                ) : null}
              </div>
            </div>

            {editingTripId === item.id && editState ? (
              <div className="trip-edit-form">
                <div className="trip-edit-fields">
                  <label>
                    <span>Km inicial</span>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={editState.kmInicial}
                      onChange={(e) => setEditState((prev) => prev && { ...prev, kmInicial: e.target.value })}
                    />
                  </label>
                  <label>
                    <span>Km final</span>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={editState.kmFinal}
                      onChange={(e) => setEditState((prev) => prev && { ...prev, kmFinal: e.target.value })}
                    />
                  </label>
                  <label className="trip-edit-rota">
                    <span>Rota utilizada</span>
                    <input
                      type="text"
                      value={editState.rotaUtilizada}
                      onChange={(e) => setEditState((prev) => prev && { ...prev, rotaUtilizada: e.target.value })}
                    />
                  </label>
                </div>
                <div className="action-row">
                  <button
                    type="button"
                    className="primary-button compact"
                    onClick={() => void saveEdit(item.id)}
                    disabled={editState.saving}
                  >
                    {editState.saving ? <Loader2 className="spin" size={15} /> : <Check size={15} />}
                    <span>Salvar</span>
                  </button>
                  <button
                    type="button"
                    className="secondary-button compact"
                    onClick={cancelEdit}
                    disabled={editState.saving}
                  >
                    <X size={15} />
                    <span>Cancelar</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="metric-row">
                <span>{formatDateTime(item.partida_em)}</span>
                <span>{formatKm(item.km_rodado ?? 0)}</span>
                <span>{item.rota_utilizada || 'Rota pendente'}</span>
              </div>
            )}

            <div className="evidence-row">
              {item.foto_hodometro_inicial ? (
                <button type="button" onClick={() => void openPhoto(item.foto_hodometro_inicial!.download_url)}>
                  <Eye />
                  Inicial
                </button>
              ) : null}
              {item.foto_hodometro_final ? (
                <button type="button" onClick={() => void openPhoto(item.foto_hodometro_final!.download_url)}>
                  <Eye />
                  Final
                </button>
              ) : null}
            </div>
            <div className="location-list">
              <LocationEvidence label="Partida" gps={item.gps_partida} />
              <LocationEvidence label="Chegada" gps={item.gps_chegada} />
            </div>
          </article>
        ))}
      </div>
      {!visibleReports.length ? (
        <div className="empty-state">
          {isVehicleMode && !selectedVehicleId ? 'Selecione um veiculo alocado para consultar.' : 'Nenhum item no periodo.'}
        </div>
      ) : null}
    </section>
  )
}

function formatCoord(value: number) {
  return Number(value).toFixed(6)
}

function LocationEvidence({ label, gps }: { label: string; gps: GpsEvidence | null }) {
  if (!gps) {
    return (
      <div className="location-evidence">
        <span>
          <MapPin />
          {label}
        </span>
        <strong>Sem GPS</strong>
      </div>
    )
  }

  return (
    <div className="location-evidence">
      <span>
        <MapPin />
        {label}
      </span>
      <strong>{gps.endereco || gps.endereco_exibicao || 'Endereco nao resolvido'}</strong>
      <small className="gps-coords">
        {formatCoord(gps.latitude)}, {formatCoord(gps.longitude)}
      </small>
    </div>
  )
}
