import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import basicSsl from '@vitejs/plugin-basic-ssl'

export default defineConfig({
  server: {
    host: true,
    proxy: {
      '/auth': 'http://localhost:8000',
      '/vehicles': 'http://localhost:8000',
      '/trips': 'http://localhost:8000',
      '/reports': 'http://localhost:8000',
      '/photos': 'http://localhost:8000',
      '/geocoding': 'http://localhost:8000',
    },
  },
  plugins: [
    basicSsl(),
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['bello-b.png'],
      manifest: {
        name: 'Controle Itinerario Comercial Bello',
        short_name: 'Itinerario Bello',
        description: 'Registro mobile de viagens com foto do hodometro e GPS.',
        theme_color: '#0f766e',
        background_color: '#f8fafc',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: '/bello-b.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable',
          },
        ],
      },
      workbox: {
        navigateFallback: '/index.html',
        runtimeCaching: [
          {
            urlPattern: ({ url }) =>
              ['/auth', '/vehicles', '/trips', '/reports', '/photos', '/geocoding'].some(
                (p) => url.pathname.startsWith(p),
              ),
            handler: 'NetworkFirst',
            options: {
              cacheName: 'bello-api-cache',
              expiration: {
                maxEntries: 80,
                maxAgeSeconds: 60 * 60,
              },
              networkTimeoutSeconds: 8,
            },
          },
        ],
      },
    }),
  ],
})
