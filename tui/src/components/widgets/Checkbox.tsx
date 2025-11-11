/**
 * Checkbox Widget Component
 * Beautiful checkbox with colorful checked state
 */

import theme from '../../theme'

interface CheckboxProps {
  checked: boolean
  onchange: (checked: boolean) => void
  label: string
  disabled?: boolean
}

export function Checkbox(props: CheckboxProps) {
  return (
    <box
      style={{
        flexDirection: 'row',
        alignItems: 'center',
        gap: 1,
        padding: '0.5 1',
        backgroundColor: props.checked ? theme.surfaceLight : 'transparent',
        borderRadius: 4,
        cursor: props.disabled ? 'not-allowed' : 'pointer',
      }}
      onclick={() => !props.disabled && props.onchange(!props.checked)}
    >
      <box
        style={{
          width: 3,
          height: 1.5,
          backgroundColor: props.checked ? theme.success : theme.surface,
          border: `2px solid ${props.checked ? theme.success : theme.border}`,
          borderRadius: 3,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <text
          style={{
            color: props.checked ? theme.textBright : 'transparent',
            fontWeight: 'bold',
            fontSize: 14,
          }}
        >
          ✓
        </text>
      </box>
      <text
        style={{
          color: props.disabled ? theme.textDim : theme.text,
          fontSize: 12,
        }}
      >
        {props.label}
      </text>
    </box>
  )
}
