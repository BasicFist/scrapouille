/**
 * Main Application Component
 * Beautiful, colorful TUI with gradient tab bar
 */

import { onMount, onCleanup, Show } from 'solid-js'
import { StatusBar } from './StatusBar'
import { SingleURLTab } from './SingleURLTab'
import { BatchProcessingTab } from './BatchProcessingTab'
import { MetricsPanel } from './MetricsPanel'
import { apiClient } from '../api/client'
import { updateHealthStatus, setApiStatus, activeTab, setActiveTab } from '../stores/app'
import theme from '../theme'

export function App() {
  let healthCheckInterval: Timer | null = null

  // Check backend health on mount and periodically
  onMount(async () => {
    console.log('🚀 Scrapouille TUI v3.0.5 (Phase 1)')
    console.log('📡 Connecting to API server...')

    // Initial health check
    await checkHealth()

    // Poll health every 5 seconds
    healthCheckInterval = setInterval(checkHealth, 5000)
  })

  onCleanup(() => {
    if (healthCheckInterval) {
      clearInterval(healthCheckInterval)
    }
  })

  async function checkHealth() {
    try {
      const health = await apiClient.checkHealth()
      updateHealthStatus(health)
      console.log('✓ Backend health:', health.status)
    } catch (error) {
      console.error('✗ Backend health check failed:', error)
      setApiStatus('unhealthy')
    }
  }

  const tabs = [
    { label: 'Single URL', icon: '🎯', color: theme.primary },
    { label: 'Batch', icon: '⚡', color: theme.secondary },
    { label: 'Metrics', icon: '📊', color: theme.accent1 },
  ]

  return (
    <box
      style={{
        width: '100%',
        height: '100%',
        background: `linear-gradient(180deg, ${theme.background} 0%, ${theme.surfaceDark} 100%)`,
        flexDirection: 'column',
      }}
    >
      {/* Status Bar */}
      <StatusBar />

      {/* Tab Bar with Rainbow Gradient */}
      <box
        style={{
          height: 3,
          width: '100%',
          flexDirection: 'row',
          gap: 0,
          background: theme.gradients.rainbow,
          padding: 0.5,
        }}
      >
        {tabs.map((tab, index) => (
          <box
            onclick={() => setActiveTab(index)}
            style={{
              flex: 1,
              padding: '1 2',
              cursor: 'pointer',
              backgroundColor:
                activeTab() === index ? theme.surface : 'transparent',
              border: activeTab() === index ? `2px solid ${tab.color}` : 'none',
              borderRadius: 6,
              marginRight: index < tabs.length - 1 ? 0.5 : 0,
              boxShadow:
                activeTab() === index
                  ? `0 0 10px ${tab.color}`
                  : 'none',
            }}
          >
            <box
              style={{
                flexDirection: 'row',
                gap: 1,
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <text style={{ fontSize: 14 }}>{tab.icon}</text>
              <text
                style={{
                  color: activeTab() === index ? tab.color : theme.textMuted,
                  fontWeight: activeTab() === index ? 'bold' : 'normal',
                  fontSize: activeTab() === index ? 14 : 12,
                }}
              >
                {tab.label}
              </text>
            </box>
          </box>
        ))}
      </box>

      {/* Main Content Area - Tab Content */}
      <box
        style={{
          flex: 1,
          width: '100%',
          overflow: 'auto',
        }}
      >
        <Show when={activeTab() === 0}>
          <SingleURLTab />
        </Show>
        <Show when={activeTab() === 1}>
          <BatchProcessingTab />
        </Show>
        <Show when={activeTab() === 2}>
          <MetricsPanel />
        </Show>
      </box>

      {/* Footer with Gradient */}
      <box
        style={{
          height: 2,
          width: '100%',
          background: `linear-gradient(90deg, ${theme.surfaceDark} 0%, ${theme.surface} 50%, ${theme.surfaceDark} 100%)`,
          borderTop: `2px solid ${theme.accent2}`,
          padding: '0 2',
          flexDirection: 'row',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <box style={{ flexDirection: 'row', gap: 2 }}>
          <text style={{ color: theme.primary, fontWeight: 'bold' }}>
            Scrapouille v3.0.5
          </text>
          <text style={{ color: theme.textDim }}>|</text>
          <text style={{ color: theme.info, fontSize: 10 }}>
            Backend: localhost:8000
          </text>
        </box>

        <box style={{ flexDirection: 'row', gap: 2 }}>
          <box
            style={{
              padding: '0 1',
              backgroundColor: theme.accent2,
              borderRadius: 2,
            }}
          >
            <text style={{ color: theme.textBright, fontSize: 10 }}>
              Tab ↹ Switch
            </text>
          </box>
          <box
            style={{
              padding: '0 1',
              backgroundColor: theme.error,
              borderRadius: 2,
            }}
          >
            <text style={{ color: theme.textBright, fontSize: 10 }}>
              Ctrl+C Exit
            </text>
          </box>
        </box>
      </box>
    </box>
  )
}
