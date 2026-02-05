// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'logo192.png', 'logo512.png'],

      manifest: {
        name: 'Museo Pumapungo - Sistema de Itinerarios IA',
        short_name: 'Museo Pumapungo',
        description: 'Sistema inteligente de itinerarios personalizados para el Museo Pumapungo',
        start_url: '/',
        display: 'standalone',
        background_color: '#ffffff',
        theme_color: '#E74C3C',
        orientation: 'portrait',
        categories: ['education', 'travel', 'culture'],
        icons: [
          {
            src: '/logo192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any'
          },
          {
            src: '/logo192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'maskable'
          },
          {
            src: '/logo512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any'
          },
          {
            src: '/logo512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable'
          }
        ],
        shortcuts: [
          {
            name: 'Generar Itinerario',
            short_name: 'Nuevo Itinerario',
            description: 'Crear un nuevo itinerario personalizado',
            url: '/generar-itinerario',
            icons: [{ src: '/logo192.png', sizes: '192x192' }]
          },
          {
            name: 'Mis Itinerarios',
            short_name: 'Mis Visitas',
            description: 'Ver mis itinerarios guardados',
            url: '/mis-itinerarios',
            icons: [{ src: '/logo192.png', sizes: '192x192' }]
          }
        ]
      },

      // ⚡ Estrategia del Service Worker
      workbox: {
        // Cachear assets estáticos (JS, CSS, imágenes, fuentes)
        globPatterns: ['**/*.{js,css,html,ico,png,svg,webp,woff2}'],

        // Reglas para peticiones en runtime
        runtimeCaching: [
          {
            // API de FastAPI — Network First (siempre intenta red primero)
            urlPattern: /^https?:\/\/.*\/api\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 // 1 hora
              },
              networkTimeoutSeconds: 10,
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            // Google Fonts u otros CDN
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1 año
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            // Imágenes externas
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/i,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'images-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30 días
              }
            }
          }
        ]
      }
    })
  ],

  server: {
    port: 5173
  }
})