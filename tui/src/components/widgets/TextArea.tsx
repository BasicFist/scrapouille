/**
 * TextArea Widget Component
 * Beautiful multi-line text input with gradient border
 */

import theme from '../../theme'

interface TextAreaProps {
  value: string
  onchange: (value: string) => void
  placeholder?: string
  height?: number
  width?: number | string
  disabled?: boolean
}

export function TextArea(props: TextAreaProps) {
  return (
    <textarea
      value={props.value}
      onchange={(e: any) => props.onchange(e.target.value)}
      placeholder={props.placeholder || ''}
      disabled={props.disabled || false}
      style={{
        width: props.width || '100%',
        height: props.height || 4,
        backgroundColor: theme.surface,
        color: theme.text,
        border: `2px solid ${theme.accent2}`,
        padding: 1,
        borderRadius: 4,
        fontSize: 12,
      }}
    />
  )
}
