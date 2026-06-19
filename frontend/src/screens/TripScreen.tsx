import { useMemo, useState } from 'react'
import { ArrowLeft, CarFront, CheckCircle2, Gauge, Loader2, LogOut, Send } from 'lucide-react'
import { CameraCapture } from '../components/CameraCapture'
import { GpsBadge } from '../components/GpsBadge'
import { StatusPill } from '../components/StatusPill'
import { api, ApiError } from '../services/api'
import type { GpsPayload, Trip, User, Vehicle } from '../types/domain'
import { formatDateTime, formatKm, numberValue } from '../utils/format'
import { tripVehicleLabel } from '../utils/trips'

interface TripScreenProps {
  token: string
  user: User
  vehicles: Vehicle[]
  trips: Trip[]
  onChange: () => Promise<void>
  onMessage: (message: string) => void
  onLogout: () => void
}

type StartStep = 'selecionar' | 'partida'
export function TripScreen({ token, user, vehicles, trips, onChange, onMessage, onLogout }: TripScreenProps) {
  const [completed, setCompleted] = useState(false)
  const [arrivalTripId, setArrivalTripId] = useState<string | null>(null)
  const activeTrip = useMemo(
    () => trips.find((trip) => trip.status === 'em_andamento' && trip.usuario_id === user.id) ?? null,
    [trips, user.id],
  )

  if (completed) {
    return <CompletionPanel onLogout={onLogout} onNewTrip={() => setCompleted(false)} />
  }

  if (activeTrip) {
    if (arrivalTripId !== activeTrip.id) {
      return (
        <InProgressPanel
          trip={activeTrip}
          vehicles={vehicles}
          onArrival={() => setArrivalTripId(activeTrip.id)}
          onLogout={onLogout}
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

  return <StartForm token={token} vehicles={vehicles} onChange={onChange} onMessage={onMessage} />
}

function StartForm({
  token,
  vehicles,
  onChange,
  onMessage,
}: Pick<TripScreenProps, 'token' | 'vehicles' | 'onChange' | 'onMessage'>) {
  const preferredVehicle = useMemo(() => vehicles.find((vehicle) => vehicle.prioritario) ?? vehicles[0] ?? null, [vehicles])
  const [step, setStep] = useState<StartStep>('selecionar')
  const [selectedVehicleId, setSelectedVehicleId] = useState('')
  const [kmInicial, setKmInicial] = useState('')
  const [photo, setPhoto] = useState<File | null>(null)
  const [gps, setGps] = useState<GpsPayload | null>(null)
  const [saving, setSaving] = useState(false)

  const selectedVehicleIdForSubmit = vehicles.some((vehicle) => vehicle.id === selectedVehicleId)
    ? selectedVehicleId
    : preferredVehicle?.id ?? ''
  const selectedVehicle = vehicles.find((vehicle) => vehicle.id === selectedVehicleIdForSubmit) ?? null
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

  if (step === 'selecionar' || !selectedVehicle) {
    return (
      <section className="panel">
        <div className="section-title">
          <CarFront />
          <div>
            <h2>Selecionar carro</h2>
            <p>Escolha o veiculo antes da partida.</p>
          </div>
        </div>
        <div className="step-strip" aria-label="Etapas da partida">
          <span className="active">1. Carro</span>
          <span>2. Partida</span>
        </div>
        {vehicles.length ? (
          <>
            <div className="vehicle-list">
              {vehicles.map((vehicle) => (
                <VehicleOption
                  key={vehicle.id}
                  vehicle={vehicle}
                  selected={selectedVehicleIdForSubmit === vehicle.id}
                  onSelect={() => setSelectedVehicleId(vehicle.id)}
                />
              ))}
            </div>
            <button
              className="primary-button full"
              type="button"
              onClick={() => (selectedVehicle ? setStep('partida') : onMessage('Selecione um veiculo.'))}
            >
              <CheckCircle2 />
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
    <section className="panel">
      <div className="section-title">
        <Gauge />
        <div>
          <h2>Partida</h2>
          <p>Km, foto e GPS obrigatorios.</p>
        </div>
      </div>
      <div className="step-strip" aria-label="Etapas da partida">
        <span>1. Carro</span>
        <span className="active">2. Partida</span>
      </div>
      {selectedVehicle ? (
        <div className="selected-vehicle-card">
          <div>
            <span>Carro selecionado</span>
            <strong>
              {selectedVehicle.placa} | {selectedVehicle.modelo}
            </strong>
            <small>{vehicleAvailabilityLabel(selectedVehicle)}</small>
          </div>
          <button className="secondary-button compact" type="button" onClick={() => setStep('selecionar')}>
            <ArrowLeft />
            <span>Trocar</span>
          </button>
        </div>
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
    <section className="panel">
      <div className="section-title">
        <CheckCircle2 />
        <div>
          <h2>Chegada</h2>
          <p>Finalize com km, rota, foto e GPS.</p>
        </div>
      </div>
      <div className="trip-summary">
        <div>
          <span>Veiculo</span>
          <strong>{vehicleLabel}</strong>
        </div>
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

function InProgressPanel({
  trip,
  vehicles,
  onArrival,
  onLogout,
}: {
  trip: Trip
  vehicles: Vehicle[]
  onArrival: () => void
  onLogout: () => void
}) {
  const vehicle = vehicles.find((item) => item.id === trip.veiculo_id)
  return (
    <section className="panel completion-panel">
      <Gauge />
      <h2>Viagem em andamento</h2>
      <p>Partida registrada. Voce pode sair do aplicativo e registrar a chegada depois.</p>
      <div className="trip-summary full">
        <div>
          <span>Veiculo</span>
          <strong>{tripVehicleLabel(trip, vehicle)}</strong>
        </div>
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
      <button className="secondary-button full" type="button" onClick={onLogout}>
        <LogOut />
        <span>Sair do aplicativo</span>
      </button>
    </section>
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
  return (
    <button
      className={`vehicle-option ${selected ? 'selected' : ''}`}
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
    >
      <span className="vehicle-option-main">
        <span className="vehicle-icon" aria-hidden="true">
          <CarFront />
        </span>
        <span className="vehicle-copy">
          <strong>{vehicle.placa}</strong>
          <span>{vehicle.modelo}</span>
        </span>
        {selected ? <CheckCircle2 className="vehicle-check" aria-hidden="true" /> : null}
      </span>
      <small>{vehicleAvailabilityLabel(vehicle)}</small>
    </button>
  )
}

function vehicleAvailabilityLabel(vehicle: Vehicle) {
  const ownership = vehicle.prioritario
    ? 'cadastrado para voce'
    : vehicle.tipo === 'empresa'
      ? 'empresa disponivel'
      : 'disponivel'
  return `${ownership} | ${vehicle.tipo_disponibilidade}`
}

function CompletionPanel({ onLogout, onNewTrip }: { onLogout: () => void; onNewTrip: () => void }) {
  return (
    <section className="panel completion-panel">
      <CheckCircle2 />
      <h2>Itinerario registrado</h2>
      <p>A viagem ficou pronta para o fechamento mensal.</p>
      <button className="primary-button full" type="button" onClick={onLogout}>
        <LogOut />
        <span>Sair do aplicativo</span>
      </button>
      <button className="secondary-button full" type="button" onClick={onNewTrip}>
        <CarFront />
        <span>Registrar outra viagem</span>
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
