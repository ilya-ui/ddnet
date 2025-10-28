import type { CalculatorAction } from '../lib/calc'
import type { KeyVariant } from '../lib/keyboard'
import styles from './Button.module.css'

interface ButtonProps {
  id: string
  label: string
  ariaLabel?: string
  action: CalculatorAction
  variant: KeyVariant
  onPress: (action: CalculatorAction) => void
  isActive?: boolean
  gridArea?: string
}

export function Button({
  id,
  label,
  ariaLabel,
  action,
  variant,
  onPress,
  isActive = false,
  gridArea,
}: ButtonProps) {
  const classNames = [styles.button, styles[variant]]

  if (isActive) {
    classNames.push(styles.active)
  }

  return (
    <button
      type="button"
      className={classNames.join(' ')}
      aria-label={ariaLabel}
      onClick={() => onPress(action)}
      data-key-id={id}
      style={gridArea ? { gridArea } : undefined}
    >
      {label}
    </button>
  )
}
