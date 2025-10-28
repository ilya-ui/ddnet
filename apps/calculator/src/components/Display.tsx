import styles from './Display.module.css'

interface DisplayProps {
  value: string
  expression?: string
  isError?: boolean
}

export function Display({ value, expression, isError = false }: DisplayProps) {
  const valueClassName = isError ? `${styles.value} ${styles.error}` : styles.value

  return (
    <div className={styles.display} role="status" aria-live="polite">
      <div className={styles.expression}>{expression || '\u00a0'}</div>
      <div className={valueClassName}>{value}</div>
    </div>
  )
}
