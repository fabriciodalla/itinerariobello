import type { DriverTab } from '../components/BottomNav'
import { TripScreen } from './TripScreen'
import { HistoryScreen } from './HistoryScreen'
import { MonthlyClosureScreen } from './MonthlyClosureScreen'
import { MenuScreen } from './MenuScreen'
import type { Trip, User, Vehicle } from '../types/domain'

interface DriverCentralScreenProps {
  token: string
  user: User
  vehicles: Vehicle[]
  trips: Trip[]
  tab: DriverTab
  onChange: () => Promise<void>
  onMessage: (message: string) => void
  onLogout: () => void
  onShowStatusChange: (show: boolean) => void
}

export function DriverCentralScreen({
  token,
  user,
  vehicles,
  trips,
  tab,
  onChange,
  onMessage,
  onLogout,
  onShowStatusChange,
}: DriverCentralScreenProps) {
  return (
    <div className="screen-stack">
      {tab === 'carro' ? (
        <TripScreen
          token={token}
          user={user}
          vehicles={vehicles}
          trips={trips}
          onChange={onChange}
          onMessage={onMessage}
          onLogout={onLogout}
          onShowStatusChange={onShowStatusChange}
        />
      ) : null}

      {tab === 'historico' ? (
        <HistoryScreen token={token} user={user} vehicles={vehicles} trips={trips} onMessage={onMessage} />
      ) : null}

      {tab === 'fechamento' ? <MonthlyClosureScreen token={token} user={user} onMessage={onMessage} /> : null}

      {tab === 'menu' ? <MenuScreen token={token} user={user} onLogout={onLogout} onMessage={onMessage} /> : null}
    </div>
  )
}
