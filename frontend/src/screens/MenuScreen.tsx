import { useState } from 'react'
import { Info, KeyRound, LogOut, Settings, User as UserIcon } from 'lucide-react'
import { ChangePasswordModal } from '../components/ChangePasswordModal'
import { InstallPromptButton } from '../components/InstallPromptButton'
import { StatusPill } from '../components/StatusPill'
import type { User } from '../types/domain'
import { getInitials } from '../utils/format'

interface MenuScreenProps {
  token: string
  user: User
  onLogout: () => void
}

const APP_VERSION = '1.1.0'

export function MenuScreen({ token, user, onLogout }: MenuScreenProps) {
  const [showChangePassword, setShowChangePassword] = useState(false)

  return (
    <div className="screen-stack">
      <section className="panel panel-edge menu-profile">
        <span className="driver-avatar" aria-hidden="true">
          {getInitials(user.nome)}
        </span>
        <div>
          <strong className="driver-name-dark">{user.nome}</strong>
          <div className="menu-profile-meta">
            <StatusPill status={user.pode_aprovar ? 'fechamento' : user.perfil} />
            <span>{user.email}</span>
          </div>
        </div>
      </section>

      <section className="panel panel-edge menu-list">
        <div className="section-title">
          <UserIcon />
          <div>
            <h2>Perfil</h2>
          </div>
        </div>
        <div className="menu-row menu-row-static">
          <span>Cargo</span>
          <strong>{user.cargo ?? '-'}</strong>
        </div>
      </section>

      <section className="panel panel-edge menu-list">
        <div className="section-title">
          <Settings />
          <div>
            <h2>Configuracoes</h2>
          </div>
        </div>
        <button className="menu-row" type="button" onClick={() => setShowChangePassword(true)}>
          <KeyRound />
          <span>Trocar senha</span>
        </button>
        <div className="menu-row menu-row-static">
          <span>Instalar aplicativo</span>
          <InstallPromptButton />
        </div>
        <div className="menu-row menu-row-static">
          <Info />
          <span>Versao {APP_VERSION}</span>
        </div>
      </section>

      <button className="secondary-button full" type="button" onClick={onLogout}>
        <LogOut />
        <span>Sair</span>
      </button>

      {showChangePassword ? <ChangePasswordModal token={token} onClose={() => setShowChangePassword(false)} /> : null}
    </div>
  )
}
