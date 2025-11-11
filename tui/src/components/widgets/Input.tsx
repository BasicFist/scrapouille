/**
 * Input Widget Component
 * Beautiful text input with gradient border
 */

import theme from '../../theme'

interface InputProps {
  value: string
  onchange: (value: string) => void
  placeholder?: string
  width?: number | string
  disabled?: boolean
}

export function Input(props: InputProps) {
  return (
    <input
      value={props.value}
      onchange={(e: any) => props.onchange(e.target.value)}
      placeholder={props.placeholder || ''}
      disabled={props.disabled || false}
      style={{
        width: props.width || '100%',
        height: 2,
        backgroundColor: theme.surface,
        color: theme.text,
        border: `2px solid ${theme.primary}`,
        padding: '0 1',
        borderRadius: 4,
        fontSize: 12,
      }}
    />
  )
}
