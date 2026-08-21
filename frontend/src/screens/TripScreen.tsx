import { useEffect, useMemo, useRef, useState } from 'react'
import type { MouseEvent, PointerEvent, ReactNode } from 'react'
import { AlertTriangle, ArrowLeft, CarFront, CheckCircle2, Gauge, Info, Loader2, LogOut, Send, X } from 'lucide-react'
import { CameraCapture } from '../components/CameraCapture'
import { GpsBadge } from '../components/GpsBadge'
import { StatusPill } from '../components/StatusPill'
import { api, ApiError } from '../services/api'
import type { GpsPayload, Trip, User, Vehicle } from '../types/domain'
import { formatDateTime, formatKm, numberValue } from '../utils/format'
import { tripVehicleLabel } from '../utils/trips'
import { vehicleImageForModel } from '../utils/vehicleImages'

interface TripScreenProps {
  token: string
  user: User
  vehicles: Vehicle[]
  trips: Trip[]
  onChange: () => Promise<void>
  onMessage: (message: string) => void
  onLogout: () => void
  onCloseApp: () => void
  onShowStatusChange: (show: boolean) => void
}

type StartStep = 'selecionar' | 'partida'
export function TripScreen({ token, user, vehicles, trips, onChange, onMessage, onLogout, onCloseApp, onShowStatusChange }: TripScreenProps) {
  const [completed, setCompleted] = useState(false)
  const [completedLate, setCompletedLate] = useState(false)
  const [arrivalTripId, setArrivalTripId] = useState<string | null>(null)
  const activeTrip = useMemo(
    () => trips.find((trip) => trip.status === 'em_andamento' && trip.usuario_id === user.id) ?? null,
    [trips, user.id],
  )
  const isLateTrip = Boolean(activeTrip?.pendente_fechamento_tardio)
  const showingArrival = Boolean(activeTrip && arrivalTripId === activeTrip.id)

  useEffect(() => {
    if (completed || completedLate || !activeTrip) {
      return
    }
    onShowStatusChange(isLateTrip || showingArrival)
  }, [completed, completedLate, activeTrip, isLateTrip, showingArrival, onShowStatusChange])

  useEffect(() => {
    if (completed || completedLate) {
      onShowStatusChange(false)
    }
  }, [completed, completedLate, onShowStatusChange])

  useEffect(() => {
    return () => onShowStatusChange(false)
  }, [onShowStatusChange])

  if (completedLate) {
    return (
      <CompletionPanel
        onLogout={onLogout}
        onCloseApp={onCloseApp}
        onNewTrip={() => setCompletedLate(false)}
        lateClosure
      />
    )
  }

  if (completed) {
    return <CompletionPanel onLogout={onLogout} onCloseApp={onCloseApp} onNewTrip={() => setCompleted(false)} />
  }

  if (activeTrip) {
    if (isLateTrip) {
      return (
        <LateClosureForm
          token={token}
          trip={activeTrip}
          vehicles={vehicles}
          onChange={onChange}
          onMessage={onMessage}
          onFinished={() => setCompletedLate(true)}
          onLogout={onLogout}
          onCloseApp={onCloseApp}
        />
      )
    }

    if (!showingArrival) {
      return (
        <InProgressPanel
          trip={activeTrip}
          vehicles={vehicles}
          onArrival={() => setArrivalTripId(activeTrip.id)}
          onLogout={onLogout}
          onCloseApp={onCloseApp}
        />
      )
    }

    return (
      <ArrivalForm
        token={token}
        trip={activeTrip}
        vehicles={vehicles}
        onChange={onChange}
        onMessage={onMessage}
        onFinished={() => setCompleted(true)}
      />
    )
  }

  return <StartForm token={token} vehicles={vehicles} onChange={onChange} onMessage={onMessage} onShowStatusChange={onShowStatusChange} />
}

function StartForm({
  token,
  vehicles,
  onChange,
  onMessage,
  onShowStatusChange,
}: Pick<TripScreenProps, 'token' | 'vehicles' | 'onChange' | 'onMessage' | 'onShowStatusChange'>) {
  const preferredVehicle = useMemo(() => vehicles.find((vehicle) => vehicle.prioritario) ?? vehicles[0] ?? null, [vehicles])
  const [step, setStep] = useState<StartStep>('selecionar')
  const vehicleListRef = useRef<HTMLDivElement>(null)
  const dragRef = useRef({ active: false, startX: 0, scrollLeft: 0, dragged: false })
  const [selectedVehicleId, setSelectedVehicleId] = useState('')
  const [kmInicial, setKmInicial] = useState('')
  const [photo, setPhoto] = useState<File | null>(null)
  const [gps, setGps] = useState<GpsPayload | null>(null)
  const [saving, setSaving] = useState(false)

  const selectedVehicleIdForSubmit = vehicles.some((vehicle) => vehicle.id === selectedVehicleId)
    ? selectedVehicleId
    : preferredVehicle?.id ?? ''
  const selectedVehicle = vehicles.find((vehicle) => vehicle.id === selectedVehicleIdForSubmit) ?? null

  useEffect(() => {
    onShowStatusChange(step === 'partida' && Boolean(selectedVehicle))
  }, [step, selectedVehicle, onShowStatusChange])

  const kmInicialNumber = Number(kmInicial)
  const hasValidKmInicial = kmInicial.trim() !== '' && Number.isFinite(kmInicialNumber) && kmInicialNumber >= 0
  const missingFields = [
    !selectedVehicleIdForSubmit ? 'veiculo' : '',
    !hasValidKmInicial ? 'km inicial' : '',
    !photo ? 'foto' : '',
    !gps ? 'GPS' : '',
  ].filter(Boolean)
  const canSubmit = missingFields.length === 0

  async function submit() {
    if (!canSubmit || !photo || !gps) {
      onMessage(`Falta informar: ${missingFields.join(', ')}.`)
      return
    }
    setSaving(true)
    try {
      await api.startTrip(token, selectedVehicleIdForSubmit, kmInicialNumber, gps, photo)
      setKmInicial('')
      setPhoto(null)
      onMessage('Partida registrada.')
      await onChange()
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Nao foi possivel iniciar a viagem.')
    } finally {
      setSaving(false)
    }
  }

  function handleVehicleListPointerDown(event: PointerEvent<HTMLDivElement>) {
    if (event.pointerType !== 'mouse') return
    const el = vehicleListRef.current
    if (!el) return
    dragRef.current = { active: true, startX: event.clientX, scrollLeft: el.scrollLeft, dragged: false }
    el.setPointerCapture(event.pointerId)
  }

  function handleVehicleListPointerMove(event: PointerEvent<HTMLDivElement>) {
    const el = vehicleListRef.current
    const drag = dragRef.current
    if (!el || !drag.active) return
    const delta = event.clientX - drag.startX
    if (Math.abs(delta) > 4) drag.dragged = true
    el.scrollLeft = drag.scrollLeft - delta
  }

  function handleVehicleListPointerUp(event: PointerEvent<HTMLDivElement>) {
    dragRef.current.active = false
    vehicleListRef.current?.releasePointerCapture(event.pointerId)
  }

  function handleVehicleListClickCapture(event: MouseEvent<HTMLDivElement>) {
    if (dragRef.current.dragged) {
      event.stopPropagation()
      event.preventDefault()
    }
  }

  if (step === 'selecionar' || !selectedVehicle) {
    return (
      <section className="panel panel-edge-bottom">
        <div className="section-title">
          <CarFront />
          <div>
            <h2>Selecionar carro</h2>
            <p>Escolha o veiculo para dar continuidade.</p>
          </div>
        </div>
        {vehicles.length ? (
          <>
            <div
              className="vehicle-list"
              ref={vehicleListRef}
              onPointerDown={handleVehicleListPointerDown}
              onPointerMove={handleVehicleListPointerMove}
              onPointerUp={handleVehicleListPointerUp}
              onPointerLeave={handleVehicleListPointerUp}
              onClickCapture={handleVehicleListClickCapture}
            >
              {vehicles.map((vehicle) => (
                <VehicleOption
                  key={vehicle.id}
                  vehicle={vehicle}
                  selected={selectedVehicleIdForSubmit === vehicle.id}
                  onSelect={() => setSelectedVehicleId(vehicle.id)}
                />
              ))}
            </div>
            <div className="info-card">
              <Info aria-hidden="true" />
              <div>
                <strong>Informacoes importantes</strong>
                <p>Certifique-se de selecionar o veiculo correto antes de iniciar suas atividades.</p>
              </div>
            </div>
            <button
              className="primary-button full gradient-button"
              type="button"
              onClick={() => (selectedVehicle ? setStep('partida') : onMessage('Selecione um veiculo.'))}
            >
              <CarFront />
              <span>Confirmar carro</span>
            </button>
          </>
        ) : (
          <div className="empty-state">Nenhum carro disponivel para este usuario.</div>
        )}
      </section>
    )
  }

  return (
    <section className="panel panel-edge-bottom">
      <div className="section-title">
        <Gauge />
        <div>
          <h2>Partida</h2>
          <p>Km, foto e GPS obrigatorios.</p>
        </div>
      </div>
      {selectedVehicle ? (
        <VehicleThumbCard
          modelo={selectedVehicle.modelo}
          label="Carro selecionado"
          title={`${selectedVehicle.placa} | ${selectedVehicle.modelo}`}
          subtitle={vehicleAvailabilityLabel(selectedVehicle)}
          trailing={
            <button className="primary-button compact" type="button" onClick={() => setStep('selecionar')}>
              <ArrowLeft />
              <span>Trocar</span>
            </button>
          }
        />
      ) : null}
      <label>
        <span>Km inicial</span>
        <input
          inputMode="decimal"
          type="number"
          min="0"
          value={kmInicial}
          onChange={(event) => setKmInicial(event.target.value)}
        />
      </label>
      <CameraCapture label="Foto inicial" file={photo} onFileChange={setPhoto} />
      <GpsBadge label="GPS de partida" token={token} onGpsChange={setGps} />
      <ReadinessChecklist
        items={[
          { label: 'Km inicial', done: hasValidKmInicial },
          { label: 'Foto', done: Boolean(photo) },
          { label: 'GPS', done: Boolean(gps) },
        ]}
      />
      <button className="primary-button full" type="button" onClick={() => void submit()} disabled={saving}>
        {saving ? <Loader2 className="spin" /> : <Send />}
        <span>Iniciar viagem</span>
      </button>
    </section>
  )
}

function ArrivalForm({
  token,
  trip,
  vehicles,
  onChange,
  onMessage,
  onFinished,
}: {
  token: string
  trip: Trip
  vehicles: Vehicle[]
  onChange: () => Promise<void>
  onMessage: (message: string) => void
  onFinished: () => void
}) {
  const [kmFinal, setKmFinal] = useState('')
  const [rotaUtilizada, setRotaUtilizada] = useState('')
  const [photo, setPhoto] = useState<File | null>(null)
  const [gps, setGps] = useState<GpsPayload | null>(null)
  const [saving, setSaving] = useState(false)
  const vehicle = vehicles.find((item) => item.id === trip.veiculo_id)
  const vehicleLabel = tripVehicleLabel(trip, vehicle)
  const kmFinalNumber = Number(kmFinal)
  const kmInicial = numberValue(trip.km_inicial)
  const hasValidKmFinal = kmFinal.trim() !== '' && Number.isFinite(kmFinalNumber) && kmFinalNumber >= kmInicial
  const missingFields = [
    !hasValidKmFinal ? 'km final maior ou igual ao inicial' : '',
    !rotaUtilizada.trim() ? 'rota' : '',
    !photo ? 'foto' : '',
    !gps ? 'GPS' : '',
  ].filter(Boolean)
  const canSubmit = missingFields.length === 0

  async function submit() {
    if (!canSubmit || !photo || !gps) {
      onMessage(`Falta informar: ${missingFields.join(', ')}.`)
      return
    }
    setSaving(true)
    try {
      await api.finishTrip(token, trip.id, kmFinalNumber, rotaUtilizada.trim(), gps, photo)
      onMessage('Chegada registrada.')
      await onChange()
      onFinished()
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Nao foi possivel finalizar a viagem.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="panel panel-edge-bottom">
      <div className="section-title">
        <CheckCircle2 />
        <div>
          <h2>Chegada</h2>
          <p>Finalize com km, rota, foto e GPS.</p>
        </div>
      </div>
      <VehicleThumbCard modelo={trip.veiculo_modelo || vehicle?.modelo || ''} label="Veiculo" title={vehicleLabel} />
      <div className="trip-summary cols-3">
        <div>
          <span>Km inicial</span>
          <strong>{formatKm(trip.km_inicial)}</strong>
        </div>
        <div>
          <span>Partida</span>
          <strong>{formatDateTime(trip.partida_em)}</strong>
        </div>
        <div>
          <span>Status</span>
          <StatusPill status={trip.status} />
        </div>
      </div>
      <label>
        <span>Km final</span>
        <input
          inputMode="decimal"
          type="number"
          min={kmInicial}
          value={kmFinal}
          onChange={(event) => setKmFinal(event.target.value)}
        />
      </label>
      <label>
        <span>Rota utilizada</span>
        <textarea rows={4} value={rotaUtilizada} onChange={(event) => setRotaUtilizada(event.target.value)} />
      </label>
      <CameraCapture label="Foto final" file={photo} onFileChange={setPhoto} />
      <GpsBadge label="GPS de chegada" token={token} onGpsChange={setGps} />
      <ReadinessChecklist
        items={[
          { label: 'Km final', done: hasValidKmFinal },
          { label: 'Rota', done: Boolean(rotaUtilizada.trim()) },
          { label: 'Foto', done: Boolean(photo) },
          { label: 'GPS', done: Boolean(gps) },
        ]}
      />
      <button className="primary-button full" type="button" onClick={() => void submit()} disabled={saving}>
        {saving ? <Loader2 className="spin" /> : <Send />}
        <span>Finalizar viagem</span>
      </button>
    </section>
  )
}

function LateClosureForm({
  token,
  trip,
  vehicles,
  onChange,
  onMessage,
  onFinished,
  onLogout,
  onCloseApp,
}: {
  token: string
  trip: Trip
  vehicles: Vehicle[]
  onChange: () => Promise<void>
  onMessage: (message: string) => void
  onFinished: () => void
  onLogout: () => void
  onCloseApp: () => void
}) {
  const [kmFinal, setKmFinal] = useState('')
  const [rotaUtilizada, setRotaUtilizada] = useState('')
  const [motivo, setMotivo] = useState('')
  const [photo, setPhoto] = useState<File | null>(null)
  const [gps, setGps] = useState<GpsPayload | null>(null)
  const [saving, setSaving] = useState(false)
  const vehicle = vehicles.find((item) => item.id === trip.veiculo_id)
  const vehicleLabel = tripVehicleLabel(trip, vehicle)
  const kmFinalNumber = Number(kmFinal)
  const kmInicial = numberValue(trip.km_inicial)
  const hasValidKmFinal = kmFinal.trim() !== '' && Number.isFinite(kmFinalNumber) && kmFinalNumber >= kmInicial
  const missingFields = [
    !hasValidKmFinal ? 'km final maior ou igual ao inicial' : '',
    !rotaUtilizada.trim() ? 'rota' : '',
    !photo ? 'foto' : '',
    !gps ? 'GPS' : '',
    !motivo.trim() ? 'motivo do fechamento tardio' : '',
  ].filter(Boolean)
  const canSubmit = missingFields.length === 0

  async function submit() {
    if (!canSubmit || !photo || !gps) {
      onMessage(`Falta informar: ${missingFields.join(', ')}.`)
      return
    }
    setSaving(true)
    try {
      await api.finishTrip(token, trip.id, kmFinalNumber, rotaUtilizada.trim(), gps, photo, motivo.trim())
      onMessage('Viagem atrasada finalizada e sinalizada ao seu superior.')
      await onChange()
      onFinished()
    } catch (error) {
      onMessage(error instanceof ApiError ? error.message : 'Nao foi possivel finalizar a viagem.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="panel panel-edge-bottom">
      <div className="section-title">
        <AlertTriangle />
        <div>
          <h2>Fechamento pendente</h2>
          <p>Esta viagem nao foi finalizada no mesmo dia da partida.</p>
        </div>
      </div>
      <div className="info-card">
        <AlertTriangle aria-hidden="true" />
        <div>
          <strong>Finalize antes de iniciar uma nova viagem</strong>
          <p>
            Voce precisa concluir esta viagem e informar o motivo do atraso. Seu superior imediato sera avisado
            dessa pendencia.
          </p>
        </div>
      </div>
      <VehicleThumbCard modelo={trip.veiculo_modelo || vehicle?.modelo || ''} label="Veiculo" title={vehicleLabel} />
      <div className="trip-summary cols-3">
        <div>
          <span>Km inicial</span>
          <strong>{formatKm(trip.km_inicial)}</strong>
        </div>
        <div>
          <span>Partida</span>
          <strong>{formatDateTime(trip.partida_em)}</strong>
        </div>
        <div>
          <span>Status</span>
          <StatusPill status={trip.status} />
        </div>
      </div>
      <label>
        <span>Km final</span>
        <input
          inputMode="decimal"
          type="number"
          min={kmInicial}
          value={kmFinal}
          onChange={(event) => setKmFinal(event.target.value)}
        />
      </label>
      <label>
        <span>Rota utilizada</span>
        <textarea rows={4} value={rotaUtilizada} onChange={(event) => setRotaUtilizada(event.target.value)} />
      </label>
      <CameraCapture label="Foto final" file={photo} onFileChange={setPhoto} />
      <GpsBadge label="GPS de chegada" token={token} onGpsChange={setGps} />
      <label>
        <span>Motivo do fechamento tardio</span>
        <textarea
          rows={3}
          placeholder="Explique por que a viagem nao foi finalizada no mesmo dia."
          value={motivo}
          onChange={(event) => setMotivo(event.target.value)}
        />
      </label>
      <ReadinessChecklist
        items={[
          { label: 'Km final', done: hasValidKmFinal },
          { label: 'Rota', done: Boolean(rotaUtilizada.trim()) },
          { label: 'Foto', done: Boolean(photo) },
          { label: 'GPS', done: Boolean(gps) },
          { label: 'Motivo', done: Boolean(motivo.trim()) },
        ]}
      />
      <button className="primary-button full" type="button" onClick={() => void submit()} disabled={saving}>
        {saving ? <Loader2 className="spin" /> : <Send />}
        <span>Finalizar viagem atrasada</span>
      </button>
      <button className="secondary-button full" type="button" onClick={onCloseApp}>
        <X />
        <span>Fechar aplicativo</span>
      </button>
      <button className="link-button full" type="button" onClick={onLogout}>
        <LogOut />
        <span>Sair da conta</span>
      </button>
    </section>
  )
}

function InProgressPanel({
  trip,
  vehicles,
  onArrival,
  onLogout,
  onCloseApp,
}: {
  trip: Trip
  vehicles: Vehicle[]
  onArrival: () => void
  onLogout: () => void
  onCloseApp: () => void
}) {
  const vehicle = vehicles.find((item) => item.id === trip.veiculo_id)
  return (
    <section className="panel panel-edge-bottom completion-panel">
      <Gauge />
      <h2>Viagem em andamento</h2>
      <p>Partida registrada. Voce pode sair do aplicativo e registrar a chegada depois.</p>
      <VehicleThumbCard
        modelo={trip.veiculo_modelo || vehicle?.modelo || ''}
        label="Veiculo"
        title={tripVehicleLabel(trip, vehicle)}
      />
      <div className="trip-summary full cols-2">
        <div>
          <span>Km inicial</span>
          <strong>{formatKm(trip.km_inicial)}</strong>
        </div>
        <div>
          <span>Partida</span>
          <strong>{formatDateTime(trip.partida_em)}</strong>
        </div>
      </div>
      <button className="primary-button full" type="button" onClick={onArrival}>
        <CheckCircle2 />
        <span>Fazer chegada</span>
      </button>
      <button className="secondary-button full" type="button" onClick={onCloseApp}>
        <X />
        <span>Fechar aplicativo</span>
      </button>
      <button className="link-button full" type="button" onClick={onLogout}>
        <LogOut />
        <span>Sair da conta</span>
      </button>
    </section>
  )
}

function VehicleThumbCard({
  modelo,
  label,
  title,
  subtitle,
  trailing,
}: {
  modelo: string
  label: string
  title: string
  subtitle?: string
  trailing?: ReactNode
}) {
  const vehicleImage = vehicleImageForModel(modelo)

  return (
    <div className="selected-vehicle-card">
      <span className="vehicle-thumb" aria-hidden="true">
        {vehicleImage ? <img src={vehicleImage} alt="" draggable={false} loading="lazy" /> : <CarFront />}
      </span>
      <div>
        <span>{label}</span>
        <strong>{title}</strong>
        {subtitle ? <small>{subtitle}</small> : null}
      </div>
      {trailing}
    </div>
  )
}

function VehicleOption({
  vehicle,
  selected,
  onSelect,
}: {
  vehicle: Vehicle
  selected: boolean
  onSelect: () => void
}) {
  const vehicleImage = vehicleImageForModel(vehicle.modelo)

  return (
    <button
      className={`vehicle-option ${selected ? 'selected' : ''}`}
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
    >
      <span className="vehicle-photo" aria-hidden="true">
        {vehicleImage ? <img src={vehicleImage} alt="" draggable={false} loading="lazy" /> : <CarFront />}
        {selected ? <CheckCircle2 className="vehicle-check" /> : null}
      </span>
      <span className="vehicle-copy">
        <strong>{vehicle.placa}</strong>
        <span className="vehicle-model">{vehicle.modelo}</span>
      </span>
      <small>{vehicleAvailabilityLabel(vehicle)}</small>
    </button>
  )
}

function vehicleAvailabilityLabel(vehicle: Vehicle) {
  const parts: string[] = []
  if (vehicle.prioritario) {
    parts.push('Seu veiculo principal')
  } else if (vehicle.responsavel_nome) {
    parts.push(vehicle.responsavel_nome)
  }
  if (vehicle.unidade) {
    parts.push(vehicle.unidade)
  }
  if (!parts.length) {
    parts.push('disponivel')
  }
  return parts.join(' | ')
}

function CompletionPanel({
  onLogout,
  onCloseApp,
  onNewTrip,
  lateClosure,
}: {
  onLogout: () => void
  onCloseApp: () => void
  onNewTrip: () => void
  lateClosure?: boolean
}) {
  return (
    <section className="panel panel-edge-bottom completion-panel">
      <CheckCircle2 />
      <h2>{lateClosure ? 'Viagem atrasada finalizada' : 'Itinerario registrado'}</h2>
      <p>
        {lateClosure
          ? 'O fechamento tardio foi enviado ao seu superior imediato com o motivo informado. Agora voce pode iniciar a viagem de hoje.'
          : 'A viagem ficou pronta para o fechamento mensal.'}
      </p>
      <button className="primary-button full" type="button" onClick={onCloseApp}>
        <X />
        <span>Fechar aplicativo</span>
      </button>
      <button className="secondary-button full" type="button" onClick={onNewTrip}>
        <CarFront />
        <span>{lateClosure ? 'Iniciar viagem de hoje' : 'Registrar outra viagem (outro carro)'}</span>
      </button>
      <button className="link-button full" type="button" onClick={onLogout}>
        <LogOut />
        <span>Sair da conta</span>
      </button>
    </section>
  )
}

function ReadinessChecklist({ items }: { items: Array<{ label: string; done: boolean }> }) {
  return (
    <div className="readiness-list" aria-label="Campos obrigatorios">
      {items.map((item) => (
        <span key={item.label} className={item.done ? 'ready' : ''}>
          {item.done ? <CheckCircle2 /> : <span className="required-dot" aria-hidden="true" />}
          {item.label}
        </span>
      ))}
    </div>
  )
}
