import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowLeft, Loader2, LogIn, Mail, Send, UserPlus } from 'lucide-react'
import { PasswordInput } from '../components/PasswordInput'
import type { SignupRequestPayload } from '../types/domain'

type LoginMode = 'login' | 'forgot' | 'reset' | 'signup'

interface LoginScreenProps {
  loading: boolean
  message: string
  onLogin: (email: string, senha: string) => Promise<void>
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

  const busy = loading || localLoading
  const visibleMessage = localMessage || (mode === 'login' ? message : '')

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
    await onLogin(email.trim(), senha)
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
      <section className="login-panel">
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true">
            <img className="brand-logo" src="/bello-b.png" alt="" />
          </span>
          <div>
            <span className="eyebrow">Bello Alimentos</span>
            <h1>Controle Itinerario</h1>
          </div>
        </div>

        {mode === 'login' ? (
          <form onSubmit={(event) => void submitLogin(event)}>
            <label>
              <span>E-mail</span>
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            <PasswordInput
              label="Senha"
              autoComplete="current-password"
              value={senha}
              onChange={(event) => setSenha(event.target.value)}
            />
            {visibleMessage ? <div className="alert">{visibleMessage}</div> : null}
            <button className="primary-button full" type="submit" disabled={busy}>
              {busy ? <Loader2 className="spin" /> : <LogIn />}
              <span>Entrar</span>
            </button>
            <div className="login-links">
              <button className="link-button" type="button" onClick={() => setMode('forgot')}>
                <Mail />
                <span>Esqueci minha senha</span>
              </button>
              <button className="link-button" type="button" onClick={() => setMode('signup')}>
                <UserPlus />
                <span>Solicitar cadastro</span>
              </button>
            </div>
          </form>
        ) : null}

        {mode === 'forgot' ? (
          <form onSubmit={(event) => void submitForgot(event)}>
            <label>
              <span>E-mail</span>
              <input
                type="email"
                autoComplete="email"
                value={forgotEmail}
                onChange={(event) => setForgotEmail(event.target.value)}
              />
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
              <label>
                <span>Token</span>
                <input value={resetToken} onChange={(event) => setResetToken(event.target.value)} />
              </label>
            ) : null}
            <PasswordInput
              label="Nova senha"
              autoComplete="new-password"
              value={novaSenha}
              onChange={(event) => setNovaSenha(event.target.value)}
            />
            <PasswordInput
              label="Confirmar nova senha"
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
    </main>
  )
}
