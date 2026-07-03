import { CarFront, History, Menu as MenuIcon, PieChart } from 'lucide-react'
import type { ComponentType } from 'react'

export type DriverTab = 'carro' | 'historico' | 'fechamento' | 'menu'

export interface BottomNavItem<T extends string> {
  id: T
  label: string
  icon: ComponentType
  badge?: number
}

interface BottomNavProps<T extends string> {
  items: Array<BottomNavItem<T>>
  active: T
  onChange: (tab: T) => void
}

export function BottomNav<T extends string>({ items, active, onChange }: BottomNavProps<T>) {
  return (
    <nav className="bottom-nav" aria-label="Navegacao principal">
      {items.map(({ id, label, icon: Icon, badge }) => (
        <button
          key={id}
          type="button"
          className={active === id ? 'active' : ''}
          onClick={() => onChange(id)}
          aria-current={active === id ? 'page' : undefined}
        >
          <span className="bottom-nav-icon" aria-hidden="true">
            <Icon />
            {badge ? <span className="bottom-nav-badge">{badge}</span> : null}
          </span>
          <span>{label}</span>
        </button>
      ))}
    </nav>
  )
}

export const DRIVER_NAV_ITEMS: Array<BottomNavItem<DriverTab>> = [
  { id: 'carro', label: 'Carro', icon: CarFront },
  { id: 'historico', label: 'Historico', icon: History },
  { id: 'fechamento', label: 'Fechamento', icon: PieChart },
  { id: 'menu', label: 'Menu', icon: MenuIcon },
]
