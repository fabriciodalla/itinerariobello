import { AlertTriangle, OctagonX } from 'lucide-react'

/** Limite usado quando a API ainda nao informou o valor (mantido igual ao padrao do backend). */
export const KM_LIMITE_ATIPICO_PADRAO = 1000

/** Bloqueio: km informado abaixo do ultimo registro de chegada do veiculo (RN-041). */
export function KmBlockedAlert({ title, message }: { title: string; message: string }) {
  return (
    <div className="info-card danger" role="alert">
      <OctagonX aria-hidden="true" />
      <div>
        <strong>{title}</strong>
        <p>{message}</p>
      </div>
    </div>
  )
}

/** Aviso de km atipico: exige que o motorista confirme que revisou o valor (RN-042, RN-043). */
export function KmReviewAlert({
  message,
  confirmed,
  onConfirmedChange,
}: {
  message: string
  confirmed: boolean
  onConfirmedChange: (confirmed: boolean) => void
}) {
  return (
    <div className="info-card warning km-review-card" role="alert">
      <div>
        <AlertTriangle aria-hidden="true" />
        <div>
          <strong>Revise o km informado</strong>
          <p>{message}</p>
        </div>
      </div>
      <label className="checkbox-row">
        <input type="checkbox" checked={confirmed} onChange={(event) => onConfirmedChange(event.target.checked)} />
        <span>Revisei o hodometro e o valor esta correto</span>
      </label>
    </div>
  )
}
