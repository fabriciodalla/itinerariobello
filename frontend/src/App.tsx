import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  CarFront,
  ClipboardCheck,
  History,
  KeyRound,
  Loader2,
  LogOut,
  RefreshCw,
  Route,
  ShieldCheck,
  UserPlus,
  Users,
} from 'lucide-react'
import { LoginScreen } from './screens/LoginScreen'
import { TripScreen } from './screens/TripScreen'
import { HistoryScreen } from './screens/HistoryScreen'
import { MonthlyClosureScreen } from './screens/MonthlyClosureScreen'
import { SignupRequestsScreen } from './screens/SignupRequestsScreen'
import { UsersScreen } from './screens/UsersScreen'
import { VehiclesInRouteScreen } from './screens/VehiclesInRouteScreen'
import { ChangePasswordModal } from './components/ChangePasswordModal'
import { InstallPromptButton } from './components/InstallPromptButton'
import { StatusPill } from './components/StatusPill'
import { ApiError, api } from './services/api'
import type { SignupRequestPayload, Trip, User, Vehicle, VehicleInRoute } from './types/domain'

type AppView = 'em_rota' | 'viagem' | 'historico' | 'fechamento' | 'cadastros' | 'usuarios'

const TOKEN_STORAGE_KEY = 'bello.itinerario.token'

function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_STORAGE_KEY) ?? '')
  const [user, setUser] = useState<User | null>(null)
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [vehiclesInRoute, setVehiclesInRoute] = useState<VehicleInRoute[]>([])
  const [trips, setTrips] = useState<Trip[]>([])
  const [view, setView] = useState<AppView>('viagem')
  const [loading, setLoading] = useState(Boolean(token))
  const [message, setMessage] = useState('')
  const [pendingCount, setPendingCount] = useState(0)

  const activeTrip = useMemo(
    () => trips.find((trip) => trip.status === 'em_andamento' && trip.usuario_id === user?.id) ?? null,
    [trips, user?.id],
  )

  const canReviewClosures = Boolean(
    user && (user.pode_aprovar || user.perfil === 'analista' || user.perfil === 'admin'),
  )
  const canRegisterTrips = Boolean(user && user.perfil === 'motorista')
  const canManageSignupRequests = user?.perfil === 'admin'
  const canSeeVehiclesInRoute = user?.email === 'admin@belloalimentos.com.br'

  const describeError = useCallback((error: unknown) => {
    if (error instanceof ApiError) {
      return error.message
    }
    return 'Nao foi possivel concluir a operacao.'
  }, [])

  const loadWorkspace = useCallback(
    async (currentToken: string) => {
      setLoading(true)
      setMessage('')
      try {
        const [currentUser, availableVehicles, currentVehiclesInRoute, currentTrips] = await Promise.all([
          api.me(currentToken),
          api.vehicles(currentToken),
          api.vehiclesInRoute(currentToken),
          api.trips(currentToken),
        ])
        setUser(currentUser)
        setVehicles(availableVehicles)
        setVehiclesInRoute(currentVehiclesInRoute)
        setTrips(currentTrips)
        if (currentUser.perfil === 'admin') {
          api.pendingSignupCount(currentToken).then((r) => setPendingCount(r.count)).catch(() => {})
        }
        const isMainAdmin = currentUser.email === 'admin@belloalimentos.com.br'
        setView(isMainAdmin ? 'em_rota' : 'viagem')
      } catch (error) {
        setMessage(describeError(error))
        localStorage.removeItem(TOKEN_STORAGE_KEY)
        setToken('')
        setUser(null)
      } finally {
        setLoading(false)
      }
    },
    [describeError],
  )

  useEffect(() => {
    if (token) {
      const timeout = window.setTimeout(() => void loadWorkspace(token), 0)
      return () => window.clearTimeout(timeout)
    }
  }, [loadWorkspace, token])

  async function handleLogin(email: string, senha: string) {
    setLoading(true)
    setMessage('')
    try {
      const response = await api.login(email, senha)
      localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token)
      setToken(response.access_token)
      await loadWorkspace(response.access_token)
    } catch (error) {
      setMessage(describeError(error))
      setLoading(false)
    }
  }

  async function handleForgotPassword(email: string) {
    setMessage('')
    await api.forgotPassword(email)
  }

  async function handleResetPassword(resetToken: string, novaSenha: string) {
    setMessage('')
    await api.resetPassword(resetToken, novaSenha)
  }

  async function handleSignupRequest(payload: SignupRequestPayload) {
    setMessage('')
    await api.createSignupRequest(payload)
  }

  const [showChangePassword, setShowChangePassword] = useState(false)

  function handleLogout() {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    setToken('')
    setUser(null)
    setVehicles([])
    setVehiclesInRoute([])
    setTrips([])
    setView('viagem')
  }

  async function refreshData() {
    if (token) {
      await loadWorkspace(token)
    }
  }

  const navItemCount = 1 + (canSeeVehiclesInRoute ? 1 : 0) + (canRegisterTrips ? 2 : 0) + (canManageSignupRequests ? 2 : 0)

  if (!token || !user) {
    return (
      <LoginScreen
        loading={loading}
        message={message}
        onLogin={handleLogin}
        onForgotPassword={handleForgotPassword}
        onResetPassword={handleResetPassword}
        onSignupRequest={handleSignupRequest}
      />
    )
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="topbar-user">
          <span className="brand-mark" aria-hidden="true">
            <Route />
          </span>
          <div>
            <span className="eyebrow">Itinerario Bello</span>
            <h1>{user.nome}</h1>
            <div className="topbar-meta">
              <StatusPill status={user.pode_aprovar ? 'fechamento' : user.perfil} />
              {canRegisterTrips ? (
                activeTrip ? (
                  <StatusPill status="em_andamento" />
                ) : (
                  <StatusPill status="disponivel" />
                )
              ) : (
                <StatusPill status="consulta" />
              )}
            </div>
          </div>
        </div>
        <div className="topbar-actions">
          <InstallPromptButton />
          <button className="icon-button" type="button" onClick={() => void refreshData()} aria-label="Atualizar">
            {loading ? <Loader2 className="spin" /> : <RefreshCw />}
          </button>
          <button className="icon-button" type="button" onClick={() => setShowChangePassword(true)} aria-label="Alterar senha">
            <KeyRound />
          </button>
          <button className="icon-button" type="button" onClick={handleLogout} aria-label="Sair">
            <LogOut />
          </button>
        </div>
      </header>

      {message ? <div className="alert">{message}</div> : null}

      <nav className="bottom-nav" style={{ gridTemplateColumns: `repeat(${navItemCount}, minmax(0, 1fr))` }} aria-label="Navegacao principal">
        {canSeeVehiclesInRoute ? (
          <button className={view === 'em_rota' ? 'active' : ''} type="button" onClick={() => setView('em_rota')}>
            <Route />
            <span>Em rota</span>
          </button>
        ) : null}
        {canRegisterTrips ? (
          <>
            <button className={view === 'viagem' ? 'active' : ''} type="button" onClick={() => setView('viagem')}>
              <CarFront />
              <span>Viagem</span>
            </button>
            <button className={view === 'historico' ? 'active' : ''} type="button" onClick={() => setView('historico')}>
              <History />
              <span>Historico</span>
            </button>
          </>
        ) : null}
        <button
          className={view === 'fechamento' ? 'active' : ''}
          type="button"
          onClick={() => setView('fechamento')}
        >
          {canReviewClosures ? <ShieldCheck /> : <ClipboardCheck />}
          <span>Fechamento</span>
        </button>
        {canManageSignupRequests ? (
          <>
            <button
              className={view === 'cadastros' ? 'active' : ''}
              type="button"
              onClick={() => setView('cadastros')}
            >
              <UserPlus />
              <span>Cadastros</span>
              {pendingCount > 0 ? <span className="nav-badge">{pendingCount}</span> : null}
            </button>
            <button
              className={view === 'usuarios' ? 'active' : ''}
              type="button"
              onClick={() => setView('usuarios')}
            >
              <Users />
              <span>Usuarios</span>
            </button>
          </>
        ) : null}
      </nav>

      <section className="content-area">
        {view === 'em_rota' && canSeeVehiclesInRoute ? <VehiclesInRouteScreen vehiclesInRoute={vehiclesInRoute} /> : null}

        {view === 'viagem' && canRegisterTrips ? (
          <TripScreen
            token={token}
            user={user}
            vehicles={vehicles}
            trips={trips}
            onChange={refreshData}
            onMessage={setMessage}
            onLogout={handleLogout}
          />
        ) : null}

        {view === 'historico' && canRegisterTrips ? (
          <HistoryScreen token={token} user={user} vehicles={vehicles} trips={trips} onMessage={setMessage} />
        ) : null}

        {view === 'fechamento' ? (
          <MonthlyClosureScreen token={token} user={user} onMessage={setMessage} />
        ) : null}

        {view === 'cadastros' && canManageSignupRequests ? (
          <SignupRequestsScreen token={token} onMessage={setMessage} />
        ) : null}

        {view === 'usuarios' && canManageSignupRequests ? (
          <UsersScreen token={token} onMessage={setMessage} />
        ) : null}
      </section>

      {showChangePassword ? (
        <ChangePasswordModal token={token} onClose={() => setShowChangePassword(false)} />
      ) : null}

      <footer className="app-footer">
        <Route />
        <span>API: {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}</span>
      </footer>
    </main>
  )
}

export default App
