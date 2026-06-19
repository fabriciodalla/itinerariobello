import { useEffect, useMemo, useState } from 'react'
import { Loader2, MapPin, RefreshCw } from 'lucide-react'
import { useGpsCapture } from '../hooks/useGpsCapture'
import { api } from '../services/api'
import type { GpsPayload } from '../types/domain'

interface GpsBadgeProps {
  label: string
  token: string
  onGpsChange: (gps: GpsPayload | null) => void
}

export function GpsBadge({ label, token, onGpsChange }: GpsBadgeProps) {
  const { gps, error, refresh, refreshing } = useGpsCapture()
  const [addressLookup, setAddressLookup] = useState<{
    key: string
    endereco: string | null
    enderecoExibicao: string | null
  }>({
    key: '',
    endereco: null,
    enderecoExibicao: null,
  })
  const gpsBlockedByOrigin = typeof window !== 'undefined' && !window.isSecureContext
  const visibleGps = gpsBlockedByOrigin ? null : gps
  const latitude = visibleGps?.latitude ?? null
  const longitude = visibleGps?.longitude ?? null
  const coordinateKey = latitude !== null && longitude !== null ? `${latitude.toFixed(6)},${longitude.toFixed(6)}` : ''
  const resolvedAddress = addressLookup.key === coordinateKey ? addressLookup.endereco : null
  const addressDisplay = addressLookup.key === coordinateKey ? addressLookup.enderecoExibicao : null
  const resolvingAddress = Boolean(coordinateKey && token && addressLookup.key !== coordinateKey)
  const gpsWithAddress = useMemo<GpsPayload | null>(() => {
    if (!visibleGps) {
      return null
    }
    return {
      ...visibleGps,
      endereco: resolvedAddress ?? visibleGps.endereco ?? null,
    }
  }, [resolvedAddress, visibleGps])

  useEffect(() => {
    if (!coordinateKey || latitude === null || longitude === null || !token) {
      return
    }

    const controller = new AbortController()
    let active = true

    api
      .reverseGeocode(token, latitude, longitude, controller.signal)
      .then((response) => {
        if (active) {
          setAddressLookup({
            key: coordinateKey,
            endereco: response.endereco ?? null,
            enderecoExibicao: response.endereco_exibicao ?? null,
          })
        }
      })
      .catch(() => {
        if (active) {
          setAddressLookup({ key: coordinateKey, endereco: null, enderecoExibicao: null })
        }
      })

    return () => {
      active = false
      controller.abort()
    }
  }, [coordinateKey, latitude, longitude, token])

  useEffect(() => {
    onGpsChange(gpsWithAddress)
  }, [gpsWithAddress, onGpsChange])

  return (
    <div className={`gps-row ${gpsWithAddress ? 'is-ready' : ''}`}>
      <span className="gps-status-icon" aria-hidden="true">
        <MapPin />
      </span>
      <div className="gps-copy">
        <div className="gps-heading">
          <span>{label}</span>
          {gpsWithAddress ? <span className="field-ok">capturado</span> : <span className="field-warn">pendente</span>}
        </div>
        {gpsWithAddress ? (
          <p>{gpsWithAddress.endereco || gpsStatusMessage(resolvingAddress, addressDisplay)}</p>
        ) : (
          <p>{gpsBlockedByOrigin ? 'GPS exige HTTPS no celular.' : gpsErrorMessage(error)}</p>
        )}
      </div>
      <button
        className="icon-button"
        type="button"
        onClick={() => void refresh()}
        aria-label="Atualizar GPS"
        disabled={gpsBlockedByOrigin}
      >
        {refreshing ? <Loader2 className="spin" /> : <RefreshCw />}
      </button>
    </div>
  )
}

function gpsStatusMessage(resolvingAddress: boolean, addressDisplay: string | null) {
  if (resolvingAddress) {
    return 'GPS capturado. Resolvendo endereco...'
  }
  return addressDisplay || 'GPS capturado. Endereco ainda nao resolvido.'
}

function gpsErrorMessage(error: GeolocationPositionError | null) {
  if (!error) {
    return 'Aguardando captura'
  }
  if (error.code === error.PERMISSION_DENIED) {
    return 'Permita a localizacao do celular.'
  }
  if (error.code === error.TIMEOUT) {
    return 'Tempo de captura do GPS esgotado.'
  }
  return 'Nao foi possivel capturar o GPS.'
}
