import { useState } from 'react'
import type { FormEvent } from 'react'
import { CheckCircle, KeyRound, Loader2, X } from 'lucide-react'
import { ApiError, api } from '../services/api'

interface ChangePasswordModalProps {
  token: string
  onClose: () => void
}

export function ChangePasswordModal({ token, onClose }: ChangePasswordModalProps) {
  const [senhaAtual, setSenhaAtual] = useState('')
  const [novaSenha, setNovaSenha] = useState('')
  const [confirmacao, setConfirmacao] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  function handleOverlayClick(event: React.MouseEvent<HTMLDivElement>) {
    if (event.target === event.currentTarget) onClose()
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    if (novaSenha !== confirmacao) {
      setError('Nova senha e confirmacao nao conferem.')
      return
    }
    setLoading(true)
    try {
      await api.changePassword(token, senhaAtual, novaSenha)
      setSuccess(true)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nao foi possivel alterar a senha.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal-panel">
        <div className="modal-header">
          <div className="section-title">
            <KeyRound />
            <h2>Alterar Senha</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Fechar">
            <X />
          </button>
        </div>

        {success ? (
          <div className="success-box">
            <CheckCircle />
            <span>Senha alterada com sucesso.</span>
          </div>
        ) : (
          <form onSubmit={(event) => void submit(event)}>
            <label>
              <span>Senha atual</span>
              <input
                type="password"
                autoComplete="current-password"
                value={senhaAtual}
                onChange={(event) => setSenhaAtual(event.target.value)}
              />
            </label>
            <label>
              <span>Nova senha</span>
              <input
                type="password"
                autoComplete="new-password"
                value={novaSenha}
                onChange={(event) => setNovaSenha(event.target.value)}
              />
            </label>
            <label>
              <span>Confirmar nova senha</span>
              <input
                type="password"
                autoComplete="new-password"
                value={confirmacao}
                onChange={(event) => setConfirmacao(event.target.value)}
              />
            </label>
            {error ? <div className="inline-error">{error}</div> : null}
            <button
              className="primary-button full"
              type="submit"
              disabled={loading || !senhaAtual || !novaSenha || !confirmacao}
            >
              {loading ? <Loader2 className="spin" /> : <KeyRound />}
              <span>Alterar Senha</span>
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
