import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowLeft, AtSign, BarChart3, CheckCircle2, CircleCheck, LockKeyhole, Loader2, LogIn, Mail, MapPin, Send, ShieldCheck, UserPlus, UserRound } from 'lucide-react'
import { PasswordInput } from '../components/PasswordInput'
import type { SignupRequestPayload } from '../types/domain'

type LoginMode = 'login' | 'forgot' | 'reset' | 'signup'

interface LoginScreenProps {
  loading: boolean
  message: string
  onLogin: (email: string, senha: string, lembrarAcesso: boolean) => Promise<void>
  onForgotPassword: (email: string) => Promise<void>
  onResetPassword: (token: string, novaSenha: string) => Promise<void>
  onSignupRequest: (payload: SignupRequestPayload) => Promise<void>
}

const emptySignup: SignupRequestPayload = {
  nome: '',
  email: '',
  cargo: '',
  superior: '',
  veiculo_placa: '',
  veiculo_modelo: '',
  veiculo_marca: '',
  observacao: '',
}

export function LoginScreen({
  loading,
  message,
  onLogin,
  onForgotPassword,
  onResetPassword,
  onSignupRequest,
}: LoginScreenProps) {
  const resetTokenFromUrl = useMemo(() => new URLSearchParams(window.location.search).get('reset_token') ?? '', [])
  const [mode, setMode] = useState<LoginMode>(resetTokenFromUrl ? 'reset' : 'login')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [forgotEmail, setForgotEmail] = useState('')
  const [resetToken, setResetToken] = useState(resetTokenFromUrl)
  const [novaSenha, setNovaSenha] = useState('')
  const [confirmacao, setConfirmacao] = useState('')
  const [signup, setSignup] = useState<SignupRequestPayload>(emptySignup)
  const [localMessage, setLocalMessage] = useState('')
  const [localLoading, setLocalLoading] = useState(false)
  const [rememberAccess, setRememberAccess] = useState(true)

  const busy = loading || localLoading
  const visibleMessage = localMessage || (mode === 'login' ? message : '')
  const panelCopy = {
    login: {
      icon: <UserRound />,
      title: 'Bem-vindo(a)!',
      subtitle: 'Faça login para continuar',
    },
    forgot: {
      icon: <Mail />,
      title: 'Recuperar acesso',
      subtitle: 'Informe seu e-mail para receber o link',
    },
    reset: {
      icon: <LockKeyhole />,
      title: 'Nova senha',
      subtitle: 'Defina uma senha segura para sua conta',
    },
    signup: {
      icon: <UserPlus />,
      title: 'Solicitar cadastro',
      subtitle: 'Envie seus dados para análise',
    },
  }[mode]

  function backToLogin() {
    setMode('login')
    setLocalMessage('')
    if (resetTokenFromUrl) {
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  }

  async function submitLogin(event: FormEvent) {
    event.preventDefault()
    setLocalMessage('')
    if (!email.trim() || !senha) {
      setLocalMessage('Informe e-mail e senha.')
      return
    }
    await onLogin(email.trim(), senha, rememberAccess)
  }

  async function submitForgot(event: FormEvent) {
    event.preventDefault()
    setLocalMessage('')
    if (!forgotEmail.trim()) {
      setLocalMessage('Informe o e-mail.')
      return
    }
    setLocalLoading(true)
    try {
      await onForgotPassword(forgotEmail.trim())
      setLocalMessage('Se o e-mail estiver cadastrado, enviaremos um link de recuperacao.')
    } catch (error) {
      setLocalMessage(error instanceof Error ? error.message : 'Nao foi possivel enviar o link.')
    } finally {
      setLocalLoading(false)
    }
  }

  async function submitReset(event: FormEvent) {
    event.preventDefault()
    setLocalMessage('')
    if (!resetToken.trim() || !novaSenha || !confirmacao) {
      setLocalMessage('Informe token e nova senha.')
      return
    }
    if (novaSenha !== confirmacao) {
      setLocalMessage('Nova senha e confirmacao nao conferem.')
      return
    }
    setLocalLoading(true)
    try {
      await onResetPassword(resetToken.trim(), novaSenha)
      setNovaSenha('')
      setConfirmacao('')
      setMode('login')
      if (resetTokenFromUrl) {
        window.history.replaceState({}, document.title, window.location.pathname)
      }
      setLocalMessage('Senha redefinida. Entre com a nova senha.')
    } catch (error) {
      setLocalMessage(error instanceof Error ? error.message : 'Nao foi possivel redefinir a senha.')
    } finally {
      setLocalLoading(false)
    }
  }

  async function submitSignup(event: FormEvent) {
    event.preventDefault()
    setLocalMessage('')
    const required = [
      signup.nome,
      signup.email,
      signup.cargo,
      signup.superior,
      signup.veiculo_placa,
      signup.veiculo_modelo,
      signup.veiculo_marca,
    ]
    if (required.some((value) => !value.trim())) {
      setLocalMessage('Preencha os campos obrigatorios.')
      return
    }
    setLocalLoading(true)
    try {
      await onSignupRequest({
        ...signup,
        email: signup.email.trim(),
        veiculo_placa: signup.veiculo_placa.trim().toUpperCase(),
        observacao: signup.observacao?.trim() || null,
      })
      setSignup(emptySignup)
      setLocalMessage('Solicitacao enviada para aprovacao.')
    } catch (error) {
      setLocalMessage(error instanceof Error ? error.message : 'Nao foi possivel enviar a solicitacao.')
    } finally {
      setLocalLoading(false)
    }
  }

  function updateSignup<K extends keyof SignupRequestPayload>(key: K, value: SignupRequestPayload[K]) {
    setSignup((current) => ({ ...current, [key]: value }))
  }

  return (
    <main className="login-screen">
      <div className="login-phone">
        <section className="login-hero" aria-label="Controle de Itinerário Bello">
          <div className="login-blob login-blob-a" aria-hidden="true" />
          <div className="login-blob login-blob-b" aria-hidden="true" />
          <div className="login-map-grid" aria-hidden="true" />
          <div className="login-route" aria-hidden="true">
            <span className="route-dot route-dot-a" />
            <span className="route-dot route-dot-b" />
            <span className="route-pin">
              <MapPin />
            </span>
            <span className="route-badge route-badge-chart">
              <BarChart3 />
            </span>
            <span className="route-badge-check">
              <CircleCheck />
            </span>
          </div>
          <div className="login-hero-content">
            <div className="login-brand">
              <span className="login-brand-mark" aria-hidden="true">
                <img src="/bello-b.png" alt="" />
              </span>
              <img className="login-wordmark" src="/bello-logo.png" alt="Bello Alimentos" />
            </div>
            <h1>
              Controle de <span>Itinerário</span>
            </h1>
            <p>
              Registre suas rotas diárias, acompanhe seus itinerários e{' '}
              <span>impulsione suas vendas.</span>
            </p>
          </div>
          <div className="login-city" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>
        </section>

        <section className="login-panel">
          <div className="login-panel-heading">
            <span className="login-panel-icon" aria-hidden="true">
              {panelCopy.icon}
            </span>
            <div>
              <h2>{panelCopy.title}</h2>
              <p>{panelCopy.subtitle}</p>
            </div>
          </div>

        {mode === 'login' ? (
          <form onSubmit={(event) => void submitLogin(event)}>
            <label className="login-field">
              <span>E-mail</span>
              <div className="login-input-shell">
                <AtSign aria-hidden="true" />
                <input
                  type="email"
                  autoComplete="email"
                  placeholder="Digite seu e-mail"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </div>
            </label>
            <PasswordInput
              className="login-field"
              label="Senha"
              leadingIcon={<LockKeyhole aria-hidden="true" />}
              autoComplete="current-password"
              placeholder="Digite sua senha"
              value={senha}
              onChange={(event) => setSenha(event.target.value)}
            />
            {visibleMessage ? <div className="alert">{visibleMessage}</div> : null}
            <div className="login-form-row">
              <label className="login-remember">
                <input
                  type="checkbox"
                  checked={rememberAccess}
                  onChange={(event) => setRememberAccess(event.target.checked)}
                />
                <span>Lembrar meu acesso</span>
              </label>
              <button className="login-forgot-button" type="button" onClick={() => setMode('forgot')}>
                Esqueci minha senha
              </button>
            </div>
            <button className="primary-button full" type="submit" disabled={busy}>
              {busy ? <Loader2 className="spin" /> : <LogIn />}
              <span>Entrar</span>
            </button>
            <div className="login-divider">
              <span>ou continue com</span>
            </div>
            <div className="login-links">
              <button className="secondary-button full" type="button" onClick={() => setMode('signup')}>
                <UserPlus />
                <span>Solicitar cadastro</span>
              </button>
            </div>
            <div className="login-security-note">
              <span aria-hidden="true">
                <ShieldCheck />
              </span>
              <div>
                <strong>Segurança que você pode confiar</strong>
                <p>Seus dados estão protegidos com criptografia e boas práticas de segurança.</p>
              </div>
            </div>
            <footer className="login-footer">
              Bello Alimentos © 2025
              <span>Versão 1.0.0</span>
            </footer>
          </form>
        ) : null}

        {mode === 'forgot' ? (
          <form onSubmit={(event) => void submitForgot(event)}>
            <label className="login-field">
              <span>E-mail</span>
              <div className="login-input-shell">
                <AtSign aria-hidden="true" />
                <input
                  type="email"
                  autoComplete="email"
                  placeholder="Digite seu e-mail"
                  value={forgotEmail}
                  onChange={(event) => setForgotEmail(event.target.value)}
                />
              </div>
            </label>
            {visibleMessage ? <div className="alert">{visibleMessage}</div> : null}
            <button className="primary-button full" type="submit" disabled={busy}>
              {busy ? <Loader2 className="spin" /> : <Mail />}
              <span>Enviar link</span>
            </button>
            <button className="secondary-button full" type="button" onClick={backToLogin} disabled={busy}>
              <ArrowLeft />
              <span>Voltar</span>
            </button>
          </form>
        ) : null}

        {mode === 'reset' ? (
          <form onSubmit={(event) => void submitReset(event)}>
            {!resetTokenFromUrl ? (
              <label className="login-field">
                <span>Token</span>
                <div className="login-input-shell">
                  <CheckCircle2 aria-hidden="true" />
                  <input value={resetToken} onChange={(event) => setResetToken(event.target.value)} />
                </div>
              </label>
            ) : null}
            <PasswordInput
              className="login-field"
              label="Nova senha"
              leadingIcon={<LockKeyhole aria-hidden="true" />}
              autoComplete="new-password"
              value={novaSenha}
              onChange={(event) => setNovaSenha(event.target.value)}
            />
            <PasswordInput
              className="login-field"
              label="Confirmar nova senha"
              leadingIcon={<LockKeyhole aria-hidden="true" />}
              autoComplete="new-password"
              value={confirmacao}
              onChange={(event) => setConfirmacao(event.target.value)}
            />
            {visibleMessage ? <div className="alert">{visibleMessage}</div> : null}
            <button className="primary-button full" type="submit" disabled={busy}>
              {busy ? <Loader2 className="spin" /> : <Send />}
              <span>Redefinir senha</span>
            </button>
            <button className="secondary-button full" type="button" onClick={backToLogin} disabled={busy}>
              <ArrowLeft />
              <span>Voltar</span>
            </button>
          </form>
        ) : null}

        {mode === 'signup' ? (
          <form className="signup-form" onSubmit={(event) => void submitSignup(event)}>
            <label>
              <span>Nome</span>
              <input value={signup.nome} onChange={(event) => updateSignup('nome', event.target.value)} />
            </label>
            <label>
              <span>E-mail</span>
              <input
                type="email"
                autoComplete="email"
                value={signup.email}
                onChange={(event) => updateSignup('email', event.target.value)}
              />
            </label>
            <label>
              <span>Cargo</span>
              <input value={signup.cargo} onChange={(event) => updateSignup('cargo', event.target.value)} />
            </label>
            <label>
              <span>Superior</span>
              <input value={signup.superior} onChange={(event) => updateSignup('superior', event.target.value)} />
            </label>
            <div className="signup-grid">
              <label>
                <span>Placa</span>
                <input
                  value={signup.veiculo_placa}
                  maxLength={10}
                  onChange={(event) => updateSignup('veiculo_placa', event.target.value.toUpperCase())}
                />
              </label>
              <label>
                <span>Modelo</span>
                <input
                  value={signup.veiculo_modelo}
                  onChange={(event) => updateSignup('veiculo_modelo', event.target.value)}
                />
              </label>
            </div>
            <label>
              <span>Marca</span>
              <input
                value={signup.veiculo_marca}
                onChange={(event) => updateSignup('veiculo_marca', event.target.value)}
              />
            </label>
            <label>
              <span>Observacao</span>
              <textarea
                value={signup.observacao ?? ''}
                onChange={(event) => updateSignup('observacao', event.target.value)}
              />
            </label>
            {visibleMessage ? <div className="alert">{visibleMessage}</div> : null}
            <button className="primary-button full" type="submit" disabled={busy}>
              {busy ? <Loader2 className="spin" /> : <UserPlus />}
              <span>Enviar solicitacao</span>
            </button>
            <button className="secondary-button full" type="button" onClick={backToLogin} disabled={busy}>
              <ArrowLeft />
              <span>Voltar</span>
            </button>
          </form>
        ) : null}
        </section>
      </div>
    </main>
  )
}
