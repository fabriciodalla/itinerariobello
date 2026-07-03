import { useState } from 'react'
import { KeyRound, LogOut } from 'lucide-react'
import { ChangePasswordModal } from './ChangePasswordModal'
import type { User } from '../types/domain'
import { getInitials } from '../utils/format'

interface AppHeaderProps {
  token: string
  user: User
  onLogout: () => void
}

export function AppHeader({ token, user, onLogout }: AppHeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false)
  const [showChangePassword, setShowChangePassword] = useState(false)

  return (
    <header className="app-header">
      <span className="app-header-brand" aria-hidden="true">
        <img src="/bello-b.png" alt="" />
      </span>

      <div className="app-header-account">
        <button
          className="app-header-avatar"
          type="button"
          onClick={() => setMenuOpen((open) => !open)}
          aria-label="Conta"
          aria-haspopup="menu"
          aria-expanded={menuOpen}
        >
          {getInitials(user.nome)}
        </button>

        {menuOpen ? (
          <>
            <button className="app-header-menu-backdrop" type="button" aria-label="Fechar menu" onClick={() => setMenuOpen(false)} />
            <div className="app-header-menu" role="menu">
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setMenuOpen(false)
                  setShowChangePassword(true)
                }}
              >
                <KeyRound />
                <span>Trocar senha</span>
              </button>
              <button type="button" role="menuitem" onClick={onLogout}>
                <LogOut />
                <span>Sair</span>
              </button>
            </div>
          </>
        ) : null}
      </div>

      {showChangePassword ? <ChangePasswordModal token={token} onClose={() => setShowChangePassword(false)} /> : null}
    </header>
  )
}
