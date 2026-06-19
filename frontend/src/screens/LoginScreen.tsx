import { useState } from 'react'
import type { FormEvent } from 'react'
import { Loader2, LogIn, ShieldCheck } from 'lucide-react'

interface LoginScreenProps {
  loading: boolean
  message: string
  onLogin: (email: string, senha: string) => Promise<void>
}

export function LoginScreen({ loading, message, onLogin }: LoginScreenProps) {
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [localMessage, setLocalMessage] = useState('')

  async function submit(event: FormEvent) {
    event.preventDefault()
    setLocalMessage('')
    if (!email.trim() || !senha) {
      setLocalMessage('Informe e-mail e senha.')
      return
    }
    await onLogin(email.trim(), senha)
  }

  return (
    <main className="login-screen">
      <section className="login-panel">
        <div className="brand-lockup">
          <ShieldCheck />
          <div>
            <span className="eyebrow">Bello Alimentos</span>
            <h1>Controle Itinerario</h1>
          </div>
        </div>

        <form onSubmit={(event) => void submit(event)}>
          <label>
            <span>E-mail</span>
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label>
            <span>Senha</span>
            <input
              type="password"
              autoComplete="current-password"
              value={senha}
              onChange={(event) => setSenha(event.target.value)}
            />
          </label>
          {(message || localMessage) ? <div className="alert">{localMessage || message}</div> : null}
          <button className="primary-button full" type="submit" disabled={loading}>
            {loading ? <Loader2 className="spin" /> : <LogIn />}
            <span>Entrar</span>
          </button>
        </form>
      </section>
    </main>
  )
}
