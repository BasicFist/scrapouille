/**
 * Button Widget Component
 * Beautiful, colorful button with gradients
 */

import theme from '../../theme'

interface ButtonProps {
  label: string
  onclick: () => void
  disabled?: boolean
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'warning'
  width?: number | string
}

export function Button(props: ButtonProps) {
  const getBackgroundStyle = () => {
    if (props.disabled) {
      return {
        background: theme.surfaceLight,
        border: `1px solid ${theme.border}`,
      }
    }

    switch (props.variant || 'primary') {
      case 'primary':
        return {
          background: theme.gradients.primary,
          border: `2px solid ${theme.primary}`,
          boxShadow: `0 0 15px ${theme.primary}`,
        }
      case 'secondary':
        return {
          background: theme.surface,
          border: `2px solid ${theme.secondary}`,
        }
      case 'danger':
        return {
          background: theme.gradients.error,
          border: `2px solid ${theme.error}`,
          boxShadow: `0 0 10px ${theme.error}`,
        }
      case 'success':
        return {
          background: theme.gradients.success,
          border: `2px solid ${theme.success}`,
          boxShadow: `0 0 10px ${theme.success}`,
        }
      case 'warning':
        return {
          background: theme.gradients.warning,
          border: `2px solid ${theme.warning}`,
        }
      default:
        return {
          background: theme.gradients.primary,
          border: `2px solid ${theme.primary}`,
        }
    }
  }

  const getTextColor = () => {
    if (props.disabled) return theme.textDim
    return theme.textBright
  }

  const backgroundStyle = getBackgroundStyle()

  return (
    <button
      onclick={props.onclick}
      disabled={props.disabled || false}
      style={{
        width: props.width || 'auto',
        height: 2,
        ...backgroundStyle,
        color: getTextColor(),
        padding: '0 2',
        fontWeight: 'bold',
        cursor: props.disabled ? 'not-allowed' : 'pointer',
        borderRadius: 4,
      }}
    >
      {props.label}
    </button>
  )
}
