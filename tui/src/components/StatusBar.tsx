/**
 * Status Bar Component
 * Displays connection status and system information with vibrant colors
 */

import { ollamaConnected, redisConnected, statusMessage } from '../stores/app'
import theme from '../theme'

export function StatusBar() {
  return (
    <box
      style={{
        height: 2,
        width: '100%',
        background: `linear-gradient(90deg, ${theme.surface} 0%, ${theme.surfaceDark} 100%)`,
        borderBottom: `2px solid ${theme.primary}`,
        padding: '0 2',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}
    >
      {/* Left: Connection indicators with badges */}
      <box style={{ flexDirection: 'row', gap: 2, alignItems: 'center' }}>
        <box
          style={{
            padding: '0 1',
            backgroundColor: ollamaConnected() ? theme.success : theme.error,
            borderRadius: 3,
          }}
        >
          <text style={{ color: theme.textBright, fontWeight: 'bold' }}>
            {ollamaConnected() ? '●' : '○'} Ollama
          </text>
        </box>
        <box
          style={{
            padding: '0 1',
            backgroundColor: redisConnected() ? theme.cache : theme.warning,
            borderRadius: 3,
          }}
        >
          <text style={{ color: theme.textBright, fontWeight: 'bold' }}>
            {redisConnected() ? '●' : '○'} Redis
          </text>
        </box>
      </box>

      {/* Center: Status message with icon */}
      <box style={{ flexDirection: 'row', gap: 1, alignItems: 'center' }}>
        <text style={{ color: theme.primary }}>⚡</text>
        <text style={{ color: theme.textMuted, fontStyle: 'italic' }}>
          {statusMessage()}
        </text>
      </box>

      {/* Right: Version badge */}
      <box
        style={{
          padding: '0 1',
          background: theme.gradients.primary,
          borderRadius: 3,
        }}
      >
        <text style={{ color: theme.textBright, fontWeight: 'bold' }}>
          v3.0.5 🚀
        </text>
      </box>
    </box>
  )
}
