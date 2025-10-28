import type { CalculatorAction } from '../lib/calc'
import { keyDefinitions } from '../lib/keyboard'
import { Button } from './Button'
import styles from './Keypad.module.css'

interface KeypadProps {
  onPress: (action: CalculatorAction) => void
  activeKey: string | null
}

export function Keypad({ onPress, activeKey }: KeypadProps) {
  return (
    <div className={styles.keypad}>
      {keyDefinitions.map((key) => (
        <Button
          key={key.id}
          id={key.id}
          label={key.label}
          ariaLabel={key.ariaLabel}
          action={key.action}
          variant={key.variant}
          onPress={onPress}
          isActive={activeKey === key.id}
          gridArea={key.gridArea}
        />
      ))}
    </div>
  )
}
