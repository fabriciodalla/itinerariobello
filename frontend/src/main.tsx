import { StrictMode, createElement } from 'react'
import type { ComponentType, PropsWithChildren } from 'react'
import { createRoot } from 'react-dom/client'
import ReactPWAInstallProvider from 'react-pwa-install'
import { registerSW } from 'virtual:pwa-register'
import './index.css'
import App from './App.tsx'

registerSW({ immediate: true })

const pwaInstallProvider = ReactPWAInstallProvider as ComponentType<PropsWithChildren<{ enableLogging?: boolean }>>

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {createElement(pwaInstallProvider, null, <App />)}
  </StrictMode>,
)
