/**
 * Metrics Panel Component
 * Displays analytics and scraping statistics
 */

import { createSignal, onMount, onCleanup, Show, For } from 'solid-js'
import { apiClient } from '../api/client'
import type { MetricsStats } from '../api/types'

export function MetricsPanel() {
  const [stats, setStats] = createSignal<MetricsStats | null>(null)
  const [loading, setLoading] = createSignal<boolean>(true)
  const [error, setError] = createSignal<string | null>(null)
  const [autoRefresh, setAutoRefresh] = createSignal<boolean>(true)

  let refreshInterval: ReturnType<typeof setInterval> | null = null

  const loadStats = async () => {
    try {
      setError(null)
      const data = await apiClient.getMetricsStats()
      setStats(data)
      setLoading(false)
    } catch (err: any) {
      setError(err.message || 'Failed to load metrics')
      setLoading(false)
    }
  }

  onMount(async () => {
    await loadStats()

    // Auto-refresh every 10 seconds if enabled
    refreshInterval = setInterval(() => {
      if (autoRefresh()) {
        loadStats()
      }
    }, 10000)
  })

  onCleanup(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval)
    }
  })

  return (
    <box
      style={{
        width: '100%',
        height: '100%',
        flexDirection: 'column',
        padding: 1,
        gap: 1,
      }}
    >
      {/* Header */}
      <box
        style={{
          flexDirection: 'row',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid #30363D',
          paddingBottom: 1,
        }}
      >
        <text
          style={{
            color: '#4ECDC4',
            fontWeight: 'bold',
            fontSize: 16,
          }}
        >
          Metrics & Analytics
        </text>
        <box style={{ flexDirection: 'row', gap: 1, alignItems: 'center' }}>
          <text style={{ color: '#E6EDF3' }}>
            Auto-refresh: {autoRefresh() ? 'ON' : 'OFF'}
          </text>
          <button
            onclick={() => setAutoRefresh(!autoRefresh())}
            style={{
              backgroundColor: '#30363D',
              color: '#E6EDF3',
              border: 'none',
              padding: '0 1',
              cursor: 'pointer',
            }}
          >
            Toggle
          </button>
          <button
            onclick={loadStats}
            disabled={loading()}
            style={{
              backgroundColor: '#4ECDC4',
              color: '#0D1117',
              border: 'none',
              padding: '0 1',
              fontWeight: 'bold',
              cursor: loading() ? 'not-allowed' : 'pointer',
            }}
          >
            {loading() ? 'Loading...' : 'Refresh'}
          </button>
        </box>
      </box>

      {/* Content */}
      <Show
        when={!loading() && !error()}
        fallback={
          <box
            style={{
              flex: 1,
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            <text style={{ color: '#6E7681' }}>
              {loading() ? 'Loading metrics...' : error()}
            </text>
          </box>
        }
      >
        <Show when={stats()}>
          {(metricsData) => (
            <box
              style={{
                flex: 1,
                flexDirection: 'column',
                gap: 2,
                overflow: 'auto',
              }}
            >
              {/* Overview Cards */}
              <box
                style={{
                  flexDirection: 'row',
                  gap: 2,
                  flexWrap: 'wrap',
                }}
              >
                {/* Total Scrapes */}
                <box
                  style={{
                    flex: 1,
                    minWidth: 20,
                    padding: 1,
                    backgroundColor: '#161B22',
                    border: '1px solid #30363D',
                    borderRadius: 4,
                  }}
                >
                  <box style={{ flexDirection: 'column', gap: 0.5 }}>
                    <text style={{ color: '#6E7681', fontSize: 10 }}>
                      Total Scrapes (7d)
                    </text>
                    <text
                      style={{
                        color: '#4ECDC4',
                        fontSize: 20,
                        fontWeight: 'bold',
                      }}
                    >
                      {metricsData().total_scrapes}
                    </text>
                  </box>
                </box>

                {/* Average Time */}
                <box
                  style={{
                    flex: 1,
                    minWidth: 20,
                    padding: 1,
                    backgroundColor: '#161B22',
                    border: '1px solid #30363D',
                    borderRadius: 4,
                  }}
                >
                  <box style={{ flexDirection: 'column', gap: 0.5 }}>
                    <text style={{ color: '#6E7681', fontSize: 10 }}>
                      Avg Time
                    </text>
                    <text
                      style={{
                        color: '#4ECDC4',
                        fontSize: 20,
                        fontWeight: 'bold',
                      }}
                    >
                      {metricsData().avg_execution_time.toFixed(2)}s
                    </text>
                  </box>
                </box>

                {/* Cache Hit Rate */}
                <box
                  style={{
                    flex: 1,
                    minWidth: 20,
                    padding: 1,
                    backgroundColor: '#161B22',
                    border: '1px solid #30363D',
                    borderRadius: 4,
                  }}
                >
                  <box style={{ flexDirection: 'column', gap: 0.5 }}>
                    <text style={{ color: '#6E7681', fontSize: 10 }}>
                      Cache Hit Rate
                    </text>
                    <text
                      style={{
                        color: '#4ECDC4',
                        fontSize: 20,
                        fontWeight: 'bold',
                      }}
                    >
                      {(metricsData().cache_hit_rate * 100).toFixed(1)}%
                    </text>
                  </box>
                </box>

                {/* Error Rate */}
                <box
                  style={{
                    flex: 1,
                    minWidth: 20,
                    padding: 1,
                    backgroundColor: '#161B22',
                    border: '1px solid #30363D',
                    borderRadius: 4,
                  }}
                >
                  <box style={{ flexDirection: 'column', gap: 0.5 }}>
                    <text style={{ color: '#6E7681', fontSize: 10 }}>
                      Error Rate
                    </text>
                    <text
                      style={{
                        color:
                          metricsData().error_rate > 0.1 ? '#FF7B72' : '#4ECDC4',
                        fontSize: 20,
                        fontWeight: 'bold',
                      }}
                    >
                      {(metricsData().error_rate * 100).toFixed(1)}%
                    </text>
                  </box>
                </box>
              </box>

              {/* Model Usage Table */}
              <box
                style={{
                  flexDirection: 'column',
                  gap: 1,
                  padding: 1,
                  backgroundColor: '#161B22',
                  border: '1px solid #30363D',
                  borderRadius: 4,
                }}
              >
                <text
                  style={{
                    color: '#E6EDF3',
                    fontWeight: 'bold',
                    fontSize: 14,
                  }}
                >
                  Model Usage Distribution
                </text>
                <Show
                  when={
                    metricsData().model_usage &&
                    Object.keys(metricsData().model_usage).length > 0
                  }
                  fallback={
                    <text style={{ color: '#6E7681' }}>
                      No model usage data available
                    </text>
                  }
                >
                  <box style={{ flexDirection: 'column', gap: 0.5 }}>
                    <For
                      each={Object.entries(metricsData().model_usage).sort(
                        ([, a], [, b]) => b - a
                      )}
                    >
                      {([model, count]) => (
                        <box
                          style={{
                            flexDirection: 'row',
                            justifyContent: 'space-between',
                            padding: '0.5 1',
                            backgroundColor: '#0D1117',
                            borderRadius: 2,
                          }}
                        >
                          <text style={{ color: '#E6EDF3' }}>{model}</text>
                          <text style={{ color: '#4ECDC4', fontWeight: 'bold' }}>
                            {count} scrapes
                          </text>
                        </box>
                      )}
                    </For>
                  </box>
                </Show>
              </box>

              {/* Recent Scrapes */}
              <box
                style={{
                  flexDirection: 'column',
                  gap: 1,
                  padding: 1,
                  backgroundColor: '#161B22',
                  border: '1px solid #30363D',
                  borderRadius: 4,
                  maxHeight: 30,
                  overflow: 'auto',
                }}
              >
                <text
                  style={{
                    color: '#E6EDF3',
                    fontWeight: 'bold',
                    fontSize: 14,
                  }}
                >
                  Recent Scrapes (Last 10)
                </text>
                <Show
                  when={
                    metricsData().recent_scrapes &&
                    metricsData().recent_scrapes.length > 0
                  }
                  fallback={
                    <text style={{ color: '#6E7681' }}>
                      No recent scrapes available
                    </text>
                  }
                >
                  <box style={{ flexDirection: 'column', gap: 0.5 }}>
                    <For each={metricsData().recent_scrapes}>
                      {(scrape) => (
                        <box
                          style={{
                            padding: 1,
                            backgroundColor: '#0D1117',
                            border: '1px solid #30363D',
                            borderRadius: 2,
                            flexDirection: 'column',
                            gap: 0.3,
                          }}
                        >
                          <box
                            style={{
                              flexDirection: 'row',
                              justifyContent: 'space-between',
                            }}
                          >
                            <text
                              style={{
                                color: scrape.success ? '#3FB950' : '#FF7B72',
                                fontWeight: 'bold',
                              }}
                            >
                              {scrape.success ? '✓' : '✗'}{' '}
                              {scrape.url.substring(0, 50)}
                              {scrape.url.length > 50 ? '...' : ''}
                            </text>
                            <text style={{ color: '#6E7681', fontSize: 10 }}>
                              {new Date(scrape.timestamp).toLocaleString()}
                            </text>
                          </box>
                          <box
                            style={{
                              flexDirection: 'row',
                              gap: 2,
                            }}
                          >
                            <text style={{ color: '#6E7681', fontSize: 10 }}>
                              Model: {scrape.model}
                            </text>
                            <text style={{ color: '#6E7681', fontSize: 10 }}>
                              Time: {scrape.execution_time.toFixed(2)}s
                            </text>
                            <Show when={scrape.cached}>
                              <text style={{ color: '#4ECDC4', fontSize: 10 }}>
                                [CACHED]
                              </text>
                            </Show>
                          </box>
                        </box>
                      )}
                    </For>
                  </box>
                </Show>
              </box>
            </box>
          )}
        </Show>
      </Show>
    </box>
  )
}
