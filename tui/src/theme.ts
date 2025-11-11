/**
 * Scrapouille TUI - Vibrant Color Theme
 * Beautiful, modern color palette with excellent contrast
 */

export const theme = {
  // Primary Colors - Vibrant and energetic
  primary: '#00D9FF',        // Bright Cyan - main brand color
  primaryDark: '#00A8CC',    // Darker cyan for hover states
  primaryLight: '#5DFDFF',   // Lighter cyan for highlights

  // Secondary Colors - Rich purple tones
  secondary: '#7C3AED',      // Purple - secondary actions
  secondaryDark: '#6D28D9',  // Darker purple
  secondaryLight: '#A78BFA', // Lighter purple

  // Status Colors - Clear visual feedback
  success: '#10B981',        // Emerald Green - success states
  warning: '#F59E0B',        // Amber - warnings
  error: '#EF4444',          // Red - errors/failures
  info: '#3B82F6',           // Blue - information

  // Accent Colors - Visual interest
  accent1: '#EC4899',        // Hot Pink - highlights
  accent2: '#8B5CF6',        // Violet - special elements
  accent3: '#14B8A6',        // Teal - alternative highlight
  accent4: '#F97316',        // Orange - attention

  // Background Colors - Dark theme base
  background: '#0F172A',     // Slate 900 - main background
  surface: '#1E293B',        // Slate 800 - elevated surfaces
  surfaceLight: '#334155',   // Slate 700 - lighter surfaces
  surfaceDark: '#0A0F1A',    // Even darker for depth

  // Border Colors - Subtle separation
  border: '#334155',         // Slate 700 - default borders
  borderLight: '#475569',    // Slate 600 - lighter borders
  borderDark: '#1E293B',     // Slate 800 - subtle borders

  // Text Colors - Readable hierarchy
  text: '#F1F5F9',           // Slate 100 - primary text
  textMuted: '#94A3B8',      // Slate 400 - secondary text
  textDim: '#64748B',        // Slate 500 - tertiary text
  textBright: '#FFFFFF',     // White - emphasis

  // Gradient Definitions - Beautiful transitions
  gradients: {
    primary: 'linear-gradient(135deg, #00D9FF 0%, #7C3AED 100%)',
    success: 'linear-gradient(135deg, #10B981 0%, #14B8A6 100%)',
    warning: 'linear-gradient(135deg, #F59E0B 0%, #F97316 100%)',
    error: 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)',
    rainbow: 'linear-gradient(90deg, #00D9FF 0%, #7C3AED 25%, #EC4899 50%, #F59E0B 75%, #10B981 100%)',
    sunset: 'linear-gradient(135deg, #F97316 0%, #EC4899 100%)',
    ocean: 'linear-gradient(135deg, #00D9FF 0%, #3B82F6 100%)',
  },

  // Semantic Colors - Contextual usage
  cache: '#14B8A6',          // Teal - cached items
  validation: '#8B5CF6',     // Violet - validation status
  model: '#EC4899',          // Pink - model indicators
  stealth: '#6D28D9',        // Deep Purple - stealth mode

  // Chart Colors - Data visualization
  chart: {
    color1: '#00D9FF',       // Cyan
    color2: '#7C3AED',       // Purple
    color3: '#EC4899',       // Pink
    color4: '#10B981',       // Green
    color5: '#F59E0B',       // Amber
    color6: '#3B82F6',       // Blue
  },
}

// Helper function for alpha transparency
export function withAlpha(color: string, alpha: number): string {
  // Convert hex to rgba
  const hex = color.replace('#', '')
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

// Pre-defined alpha variants for common use
export const alpha = {
  primary10: withAlpha(theme.primary, 0.1),
  primary20: withAlpha(theme.primary, 0.2),
  primary30: withAlpha(theme.primary, 0.3),
  primary50: withAlpha(theme.primary, 0.5),

  success10: withAlpha(theme.success, 0.1),
  success20: withAlpha(theme.success, 0.2),

  error10: withAlpha(theme.error, 0.1),
  error20: withAlpha(theme.error, 0.2),

  warning10: withAlpha(theme.warning, 0.1),
  warning20: withAlpha(theme.warning, 0.2),
}

// Export default theme
export default theme
