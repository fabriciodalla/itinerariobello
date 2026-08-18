import { useCallback, useEffect, useMemo, useState } from 'react'
import { Loader2, Route, ShieldCheck, UserPlus, Users, X } from 'lucide-react'
import { LoginScreen } from './screens/LoginScreen'
import { DriverCentralScreen } from './screens/DriverCentralScreen'
import { MonthlyClosureScreen } from './screens/MonthlyClosureScreen'
import { AdminCentralScreen } from './screens/AdminCentralScreen'
import type { AdminTab } from './screens/AdminCentralScreen'
import { AppHeader } from './components/AppHeader'
import { StatusChipsRow } from './components/StatusChipsRow'
import { BottomNav, DRIVER_NAV_ITEMS } from './components/BottomNav'
import type { BottomNavItem, DriverTab, SupervisorTab } from './components/BottomNav'
import { SUPERVISOR_NAV_ITEMS } from './components/BottomNav'
import { MenuScreen } from './screens/MenuScreen'
import { api, ApiError } from './services/api'
import type { SignupRequestPayload, Trip, User, Vehicle, VehicleInRoute } from './types/domain'

function App() {
  const [token, setToken] = useState('')
  const [user, setUser] = useState<User | null>(null)
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [vehiclesInRoute, setVehiclesInRoute] = useState<VehicleInRoute[]>([])
  const [trips, setTrips] = useState<Trip[]>([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [pendingCount, setPendingCount] = useState(0)
  const [driverTab, setDriverTab] = useState<DriverTab>('carro')
  const [adminTab, setAdminTab] = useState<AdminTab>('usuarios')
  const [supervisorTab, setSupervisorTab] = useState<SupervisorTab>('fechamento')
  const [showStatusChips, setShowStatusChips] = useState(false)

  const canRegisterTrips = Boolean(user && user.perfil === 'motorista')
  const isAdmin = user?.perfil === 'admin'

  const adminNavItems = useMemo<Array<BottomNavItem<AdminTab>>>(
    () => [
      { id: 'usuarios', label: 'Usuarios', icon: Users },
      { id: 'cadastros', label: 'Cadastros', icon: UserPlus, badge: pendingCount },
      { id: 'em_rota', label: 'Em Rota', icon: Route, badge: vehiclesInRoute.length },
      { id: 'fechamento', label: 'Fechamento', icon: ShieldCheck },
    ],
    [pendingCount, vehiclesInRoute.length],
  )

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
      } catch {
        setToken('')
        setUser(null)
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  useEffect(() => {
    const timeout = window.setTimeout(() => void loadWorkspace(''), 0)
    return () => window.clearTimeout(timeout)
  }, [loadWorkspace])

  useEffect(() => {
    if (driverTab !== 'carro') {
      setShowStatusChips(false)
    }
  }, [driverTab])

  useEffect(() => {
    if (!message) return
    const timeout = window.setTimeout(() => setMessage(''), 6000)
    return () => window.clearTimeout(timeout)
  }, [message])

  async function handleLogin(email: string, senha: string, lembrarAcesso = true) {
    setLoading(true)
    setMessage('')
    try {
      const response = await api.login(email, senha)
      setToken(response.access_token)
      await loadWorkspace(response.access_token)
      if (!lembrarAcesso) {
        api.logout(response.access_token).catch(() => {})
      }
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

  async function handleSignupRequest(payload: SignupRequestPayload, cnhArquivo?: File | null, apoliceArquivo?: File | null) {
    setMessage('')
    await api.createSignupRequest(payload, cnhArquivo, apoliceArquivo)
  }

  function handleLogout() {
    api.logout(token).catch(() => {})
    setToken('')
    setUser(null)
    setVehicles([])
    setVehiclesInRoute([])
    setTrips([])
  }

  function handleCloseApp() {
    // Nao desloga: a sessao (cookie) continua valida, entao na proxima vez
    // que o app for aberto o usuario entra direto, sem digitar login de novo.
    // Navegadores/PWAs so permitem fechar via script janelas abertas por script,
    // entao isso funciona como um "atalho" quando suportado; nos demais casos
    // o aviso abaixo confirma que ja pode fechar manualmente com seguranca.
    window.close()
    setMessage('Pode fechar o aplicativo com seguranca. Na proxima vez voce entra direto, sem precisar logar novamente.')
  }

  async function refreshData() {
    await loadWorkspace(token)
  }

  if (loading && !user) {
    return (
      <main className="app-shell" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100dvh' }}>
        <Loader2 className="spin" size={40} />
      </main>
    )
  }

  if (!user) {
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
    <main className="app-shell app-shell-with-nav">
      <div className="topbar-card">
        <AppHeader token={token} user={user} onLogout={handleLogout} />
      </div>

      <StatusChipsRow visible={showStatusChips} />

      {message ? (
        <div className="alert">
          <span>{message}</span>
          <button className="alert-close" type="button" onClick={() => setMessage('')} aria-label="Fechar aviso">
            <X />
          </button>
        </div>
      ) : null}

      <section className="content-area">
        {isAdmin ? (
          <AdminCentralScreen
            token={token}
            user={user}
            vehiclesInRoute={vehiclesInRoute}
            tab={adminTab}
            onMessage={setMessage}
          />
        ) : canRegisterTrips ? (
          <DriverCentralScreen
            token={token}
            user={user}
            vehicles={vehicles}
            trips={trips}
            tab={driverTab}
            onChange={refreshData}
            onMessage={setMessage}
            onLogout={handleLogout}
            onCloseApp={handleCloseApp}
            onShowStatusChange={setShowStatusChips}
          />
        ) : supervisorTab === 'menu' ? (
          <MenuScreen token={token} user={user} onLogout={handleLogout} />
        ) : (
          <MonthlyClosureScreen token={token} user={user} onMessage={setMessage} />
        )}
      </section>

      {canRegisterTrips ? <BottomNav items={DRIVER_NAV_ITEMS} active={driverTab} onChange={setDriverTab} /> : null}
      {isAdmin ? <BottomNav items={adminNavItems} active={adminTab} onChange={setAdminTab} /> : null}
      {!canRegisterTrips && !isAdmin ? (
        <BottomNav items={SUPERVISOR_NAV_ITEMS} active={supervisorTab} onChange={setSupervisorTab} />
      ) : null}
    </main>
  )
}

export default App
