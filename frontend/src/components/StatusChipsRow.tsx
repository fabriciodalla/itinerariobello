import { MapPin, Wifi, WifiOff } from 'lucide-react'
import { useOnlineStatus } from '../hooks/useOnlineStatus'
import { useGpsPermissionState } from '../hooks/useGpsPermissionState'
import type { GpsPermissionState } from '../hooks/useGpsPermissionState'

interface StatusChipsRowProps {
  visible: boolean
}

export function StatusChipsRow({ visible }: StatusChipsRowProps) {
  const online = useOnlineStatus()
  const gpsState = useGpsPermissionState()
  const gpsOk = gpsState === 'granted'
  const gpsBlocked = gpsState === 'denied'

  if (!visible) {
    return <div className="status-chips-row status-chips-row-empty" />
  }

  return (
    <div className="status-chips-row status-chips-row-filled">
      <span className={`status-chip ${online ? 'ok' : 'warn'}`}>
        {online ? <Wifi /> : <WifiOff />}
        <span>{online ? 'Conectado' : 'Sem conexao'}</span>
      </span>
      <span className={`status-chip ${gpsOk ? 'ok' : gpsBlocked ? 'danger' : 'warn'}`}>
        <MapPin />
        <span>{gpsLabel(gpsState)}</span>
      </span>
    </div>
  )
}

function gpsLabel(state: GpsPermissionState) {
  if (state === 'granted') return 'GPS pronto'
  if (state === 'denied') return 'GPS bloqueado'
  if (state === 'unsupported') return 'GPS indisponivel'
  return 'GPS pendente'
}
