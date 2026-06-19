import { useEffect, useMemo, useState } from 'react'
import { CalendarDays, CarFront, Eye, Gauge, Search } from 'lucide-react'
import { StatusPill } from '../components/StatusPill'
import { ApiError, api } from '../services/api'
import type { PhotoEvidence, StatusViagem, Trip, User, Vehicle } from '../types/domain'
import { formatDateTime, formatKm } from '../utils/format'
import { photoEvidenceFromListItem, tripVehicleLabel } from '../utils/trips'

const FILTERS: Array<StatusViagem | 'todos'> = ['todos', 'em_andamento', 'concluida']
type TripPhotoEvidence = { inicial: PhotoEvidence | null; final: PhotoEvidence | null }

export function HistoryScreen({
  token,
  user,
  vehicles,
  trips,
  onMessage,
}: {
  token: string
  user: User
  vehicles: Vehicle[]
  trips: Trip[]
  onMessage: (message: string) => void
}) {
  const [filter, setFilter] = useState<StatusViagem | 'todos'>('todos')
  const [photoEvidenceByTripId, setPhotoEvidenceByTripId] = useState<Record<string, TripPhotoEvidence>>({})
  const ownTrips = useMemo(() => trips.filter((trip) => trip.usuario_id === user.id), [trips, user.id])
  const filteredTrips = useMemo(() => {
    return ownTrips.filter((trip) => filter === 'todos' || trip.status === filter)
  }, [filter, ownTrips])

  useEffect(() => {
    const tripsMissingEvidence = ownTrips.filter(
      (trip) => !trip.foto_hodometro_inicial && !trip.foto_hodometro_final && !photoEvidenceByTripId[trip.id],
    )
    if (!tripsMissingEvidence.length) {
      return
    }

    let cancelled = false
    async function loadPhotoEvidence() {
      const evidenceEntries = await Promise.all(
        tripsMissingEvidence.map(async (trip) => {
          try {
            const photos = await api.tripPhotos(token, trip.id)
            return [trip.id, photosByType(photos)] as const
          } catch {
            return [trip.id, { inicial: null, final: null }] as const
          }
        }),
      )
      if (cancelled) {
        return
      }
      setPhotoEvidenceByTripId((current) => {
        const next = { ...current }
        for (const [tripId, evidence] of evidenceEntries) {
          next[tripId] = evidence
        }
        return next
      })
    }

    void loadPhotoEvidence()
    return () => {
      cancelled = true
    }
  }, [ownTrips, photoEvidenceByTripId, token])

  async function openPhoto(downloadUrl: string) {
    const viewer = window.open('', '_blank')
    try {
      const blob = await api.photo(token, downloadUrl)
      const objectUrl = URL.createObjectURL(blob)
      if (viewer) {
        viewer.location.href = objectUrl
      } else {
        const link = document.createElement('a')
        link.href = objectUrl
        link.target = '_blank'
        link.rel = 'noopener noreferrer'
        link.click()
      }
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000)
    } catch (error) {
      viewer?.close()
      onMessage(error instanceof ApiError ? error.message : 'Nao foi possivel abrir a foto.')
    }
  }

  return (
    <section className="panel">
      <div className="section-title">
        <Search />
        <h2>Historico</h2>
      </div>
      <div className="segmented-control">
        {FILTERS.map((item) => (
          <button key={item} className={filter === item ? 'active' : ''} type="button" onClick={() => setFilter(item)}>
            {item === 'todos' ? 'Todos' : item.replaceAll('_', ' ')}
          </button>
        ))}
      </div>
      <div className="item-list">
        {filteredTrips.map((trip) => {
          const vehicle = vehicles.find((item) => item.id === trip.veiculo_id)
          const fallbackEvidence = photoEvidenceByTripId[trip.id]
          const initialPhoto = trip.foto_hodometro_inicial ?? fallbackEvidence?.inicial ?? null
          const finalPhoto = trip.foto_hodometro_final ?? fallbackEvidence?.final ?? null
          const isLoadingPhotos = !trip.foto_hodometro_inicial && !trip.foto_hodometro_final && !fallbackEvidence

          return (
            <article className="list-card" key={trip.id}>
              <div className="list-card-main">
                <div>
                  <strong>{formatDateTime(trip.partida_em)}</strong>
                  <span>
                    <CarFront /> {tripVehicleLabel(trip, vehicle)}
                  </span>
                </div>
                <StatusPill status={trip.status} />
              </div>
              <div className="metric-row">
                <span>
                  <Gauge /> {formatKm(trip.km_inicial)} inicial
                </span>
                <span>
                  <Gauge /> {trip.km_final ? `${formatKm(trip.km_final)} final` : 'chegada pendente'}
                </span>
                <span>
                  <CalendarDays /> {trip.chegada_em ? formatDateTime(trip.chegada_em) : 'em andamento'}
                </span>
              </div>
              <div className="metric-row">
                <span>{trip.rota_utilizada || 'Rota pendente'}</span>
              </div>
              <div className="evidence-row">
                {initialPhoto ? (
                  <button type="button" onClick={() => void openPhoto(initialPhoto.download_url)}>
                    <Eye />
                    Inicial
                  </button>
                ) : null}
                {finalPhoto ? (
                  <button type="button" onClick={() => void openPhoto(finalPhoto.download_url)}>
                    <Eye />
                    Final
                  </button>
                ) : null}
                {!initialPhoto && !finalPhoto ? (
                  <span>{isLoadingPhotos ? 'Carregando fotos...' : 'Fotos ainda indisponiveis'}</span>
                ) : null}
              </div>
            </article>
          )
        })}
      </div>
      {!filteredTrips.length ? <div className="empty-state">Nenhuma viagem encontrada.</div> : null}
    </section>
  )
}

function photosByType(photos: PhotoEvidence[]): TripPhotoEvidence {
  return photos.reduce<TripPhotoEvidence>(
    (evidence, photo) => {
      const photoWithUrl = photoEvidenceFromListItem(photo)
      if (photoWithUrl.tipo === 'inicial') {
        return { ...evidence, inicial: photoWithUrl }
      }
      if (photoWithUrl.tipo === 'final') {
        return { ...evidence, final: photoWithUrl }
      }
      return evidence
    },
    { inicial: null, final: null },
  )
}
