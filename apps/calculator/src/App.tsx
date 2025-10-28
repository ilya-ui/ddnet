import { useEffect, useReducer, useState } from 'react'
import styles from './App.module.css'
import { Display } from './components/Display'
import { Keypad } from './components/Keypad'
import {
  calculatorReducer,
  createInitialState,
  operatorToSymbol,
  type CalculatorAction,
} from './lib/calc'
import { getBindingForKey } from './lib/keyboard'

type Theme = 'light' | 'dark'

const THEME_STORAGE_KEY = 'calculator:theme'

function getInitialTheme(): Theme {
  if (typeof window === 'undefined') {
    return 'light'
  }

  const stored = window.localStorage.getItem(THEME_STORAGE_KEY)
  if (stored === 'light' || stored === 'dark') {
    return stored
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export default function App() {
  const [state, dispatch] = useReducer(calculatorReducer, undefined, createInitialState)
  const [activeKey, setActiveKey] = useState<string | null>(null)
  const [theme, setTheme] = useState<Theme>(() => getInitialTheme())
  const [hasStoredTheme, setHasStoredTheme] = useState(() => {
    if (typeof window === 'undefined') {
      return false
    }
    return window.localStorage.getItem(THEME_STORAGE_KEY) != null
  })

  useEffect(() => {
    if (typeof document === 'undefined') {
      return
    }

    document.documentElement.dataset.theme = theme

    if (typeof window !== 'undefined') {
      if (hasStoredTheme) {
        window.localStorage.setItem(THEME_STORAGE_KEY, theme)
      } else {
        window.localStorage.removeItem(THEME_STORAGE_KEY)
      }
    }
  }, [theme, hasStoredTheme])

  useEffect(() => {
    if (typeof window === 'undefined' || hasStoredTheme) {
      return
    }

    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = (event: MediaQueryListEvent) => {
      setTheme(event.matches ? 'dark' : 'light')
    }

    media.addEventListener('change', onChange)
    return () => media.removeEventListener('change', onChange)
  }, [hasStoredTheme])

  useEffect(() => {
    if (typeof window === 'undefined') {
      return
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      const binding = getBindingForKey(event.key)
      if (!binding) {
        return
      }

      event.preventDefault()
      dispatch(binding.action)
      setActiveKey(binding.buttonId)
    }

    const handleKeyUp = () => {
      setActiveKey(null)
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
    }
  }, [])

  const handlePress = (action: CalculatorAction) => {
    dispatch(action)
  }

  const toggleTheme = () => {
    setHasStoredTheme(true)
    setTheme((current) => (current === 'light' ? 'dark' : 'light'))
  }

  const expression = state.error
    ? ''
    : state.operator && state.previousValue !== null
      ? `${state.previousValue} ${operatorToSymbol(state.operator)}`
      : ''

  return (
    <div className={styles.app}>
      <div className={styles.calculator}>
        <header className={styles.header}>
          <h1 className={styles.title}>Calculator</h1>
          <button
            type="button"
            className={styles.themeToggle}
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
          >
            <span aria-hidden="true">{theme === 'light' ? '🌞' : '🌙'}</span>
            <span className={styles.themeToggleText}>{theme === 'light' ? 'Light' : 'Dark'}</span>
          </button>
        </header>

        <Display value={state.currentValue} expression={expression} isError={state.error} />
        <Keypad onPress={handlePress} activeKey={activeKey} />

        <p className={styles.helperText}>
          Keyboard: 0-9 · . · + - * / · Enter (=) · Backspace (⌫) · Delete (C) · Escape (AC) · % · F9 (±)
        </p>
      </div>
    </div>
  )
}
