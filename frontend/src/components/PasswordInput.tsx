import { useId, useState } from 'react'
import type { InputHTMLAttributes } from 'react'
import { Eye, EyeOff } from 'lucide-react'

type PasswordInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> & {
  label: string
}

export function PasswordInput({ label, id, className, ...props }: PasswordInputProps) {
  const generatedId = useId()
  const inputId = id ?? generatedId
  const [visible, setVisible] = useState(false)
  const toggleLabel = visible ? `Ocultar ${label.toLowerCase()}` : `Mostrar ${label.toLowerCase()}`

  return (
    <label className={className} htmlFor={inputId}>
      <span>{label}</span>
      <div className="password-field">
        <input {...props} id={inputId} type={visible ? 'text' : 'password'} />
        <button
          className="password-toggle"
          type="button"
          aria-label={toggleLabel}
          aria-pressed={visible}
          title={toggleLabel}
          onClick={() => setVisible((current) => !current)}
        >
          {visible ? <EyeOff /> : <Eye />}
        </button>
      </div>
    </label>
  )
}
