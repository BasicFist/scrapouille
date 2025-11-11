/**
 * Global Application State (SolidJS Signals)
 * Manages application-wide reactive state
 */

import { createSignal, createEffect } from 'solid-js'
import type { HealthResponse } from '../api/types'

// === Connection Status ===

export const [ollamaConnected, setOllamaConnected] = createSignal<boolean>(false)
export const [redisConnected, setRedisConnected] = createSignal<boolean>(false)
export const [apiStatus, setApiStatus] = createSignal<'healthy' | 'degraded' | 'unhealthy' | 'unknown'>('unknown')

// === UI State ===

export const [activeTab, setActiveTab] = createSignal<number>(0)
export const [statusMessage, setStatusMessage] = createSignal<string>('Initializing...')

// === Derived State ===

export const isBackendReady = () => apiStatus() === 'healthy' || apiStatus() === 'degraded'
export const hasOllama = () => ollamaConnected()
export const hasRedis = () => redisConnected()

// === Effects ===

// Update status message based on connection state
createEffect(() => {
  const status = apiStatus()
  const ollama = ollamaConnected()
  const redis = redisConnected()

  if (status === 'unknown') {
    setStatusMessage('Connecting to API...')
  } else if (status === 'unhealthy') {
    setStatusMessage('⚠️  Backend unavailable')
  } else if (!ollama) {
    setStatusMessage('⚠️  Ollama not running')
  } else if (status === 'degraded') {
    setStatusMessage('⚠️  Redis unavailable (caching disabled)')
  } else {
    setStatusMessage('Ready')
  }
})

// === Actions ===

export function updateHealthStatus(health: HealthResponse) {
  setApiStatus(health.status)
  setOllamaConnected(health.connections.ollama)
  setRedisConnected(health.connections.redis)
}
