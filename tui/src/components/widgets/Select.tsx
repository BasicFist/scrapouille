/**
 * Select Widget Component
 * Beautiful dropdown select with colorful styling
 */

import theme from '../../theme'

interface SelectProps {
  value: string
  options: string[] | { label: string; value: string }[]
  onchange: (value: string) => void
  width?: number | string
  disabled?: boolean
}

export function Select(props: SelectProps) {
  // Normalize options to { label, value } format
  const normalizedOptions = props.options.map((opt) =>
    typeof opt === 'string' ? { label: opt, value: opt } : opt
  )

  return (
    <select
      value={props.value}
      onchange={(e: any) => props.onchange(e.target.value)}
      disabled={props.disabled || false}
      style={{
        width: props.width || '100%',
        height: 2,
        backgroundColor: theme.surface,
        color: theme.text,
        border: `2px solid ${theme.secondary}`,
        padding: '0 1',
        borderRadius: 4,
        fontSize: 12,
      }}
    >
      {normalizedOptions.map((option) => (
        <option value={option.value}>{option.label}</option>
      ))}
    </select>
  )
}
