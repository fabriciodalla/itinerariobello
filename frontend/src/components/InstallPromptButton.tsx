import { Smartphone } from 'lucide-react'
import { useReactPWAInstall } from 'react-pwa-install'

export function InstallPromptButton() {
  const { pwaInstall, supported, isInstalled } = useReactPWAInstall()
  const canInstall = safeCheck(supported) && !safeCheck(isInstalled)

  if (!canInstall) {
    return null
  }

  return (
    <button
      className="icon-button"
      type="button"
      aria-label="Instalar aplicativo"
      onClick={() =>
        void pwaInstall({
          title: 'Itinerario Bello',
          description: 'Controle de viagem comercial',
        }).catch(() => undefined)
      }
    >
      <Smartphone />
    </button>
  )
}

function safeCheck(check: () => boolean) {
  try {
    return check()
  } catch {
    return false
  }
}
