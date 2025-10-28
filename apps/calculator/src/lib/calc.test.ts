import { describe, expect, it } from 'vitest'
import {
  calculatorReducer,
  createInitialState,
  formatNumber,
  type CalculatorAction,
  type CalculatorState,
  type Operator,
} from './calc'

function runActions(actions: CalculatorAction[]) {
  return actions.reduce(calculatorReducer, createInitialState())
}

describe('calculatorReducer', () => {
  it('performs basic addition', () => {
    const state = runActions([
      { type: 'digit', digit: '3' },
      { type: 'operator', operator: '+' },
      { type: 'digit', digit: '2' },
      { type: 'evaluate' },
    ])

    expect(state.currentValue).toBe('5')
    expect(state.previousValue).toBeNull()
  })

  it('performs subtraction', () => {
    const state = runActions([
      { type: 'digit', digit: '9' },
      { type: 'operator', operator: '-' },
      { type: 'digit', digit: '4' },
      { type: 'evaluate' },
    ])

    expect(state.currentValue).toBe('5')
  })

  it('performs division', () => {
    const state = runActions([
      { type: 'digit', digit: '8' },
      { type: 'operator', operator: '/' },
      { type: 'digit', digit: '4' },
      { type: 'evaluate' },
    ])

    expect(state.currentValue).toBe('2')
  })

  it('chains operations sequentially', () => {
    const state = runActions([
      { type: 'digit', digit: '5' },
      { type: 'operator', operator: '+' },
      { type: 'digit', digit: '6' },
      { type: 'operator', operator: '*' },
      { type: 'digit', digit: '2' },
      { type: 'evaluate' },
    ])

    expect(state.currentValue).toBe('22')
  })

  it('supports decimals and normalises results', () => {
    const state = runActions([
      { type: 'digit', digit: '1' },
      { type: 'decimal' },
      { type: 'digit', digit: '5' },
      { type: 'operator', operator: '+' },
      { type: 'digit', digit: '2' },
      { type: 'decimal' },
      { type: 'digit', digit: '5' },
      { type: 'evaluate' },
    ])

    expect(state.currentValue).toBe('4')
  })

  it('handles toggle sign and multiplication', () => {
    let state = createInitialState()
    const actions: CalculatorAction[] = [
      { type: 'digit', digit: '5' },
      { type: 'toggle-sign' },
      { type: 'operator', operator: '*' },
      { type: 'digit', digit: '2' },
      { type: 'evaluate' },
    ]

    for (const action of actions) {
      state = calculatorReducer(state, action)
    }

    expect(state.currentValue).toBe('-10')
  })

  it('applies percent relative to the previous value', () => {
    const state = runActions([
      { type: 'digit', digit: '2' },
      { type: 'digit', digit: '0' },
      { type: 'digit', digit: '0' },
      { type: 'operator', operator: '+' },
      { type: 'digit', digit: '1' },
      { type: 'digit', digit: '0' },
      { type: 'percent' },
      { type: 'evaluate' },
    ])

    expect(state.currentValue).toBe('220')
  })

  it('calculates standalone percent values', () => {
    const state = runActions([
      { type: 'digit', digit: '5' },
      { type: 'digit', digit: '0' },
      { type: 'percent' },
    ])

    expect(state.currentValue).toBe('0.5')
  })

  it('clears entry without losing the pending operation', () => {
    const state = runActions([
      { type: 'digit', digit: '1' },
      { type: 'digit', digit: '2' },
      { type: 'operator', operator: '+' },
      { type: 'digit', digit: '3' },
      { type: 'clear-entry' },
      { type: 'digit', digit: '5' },
      { type: 'evaluate' },
    ])

    expect(state.currentValue).toBe('17')
  })

  it('handles backspace and resets cleanly', () => {
    let state = createInitialState()
    const actions: CalculatorAction[] = [
      { type: 'digit', digit: '9' },
      { type: 'digit', digit: '8' },
      { type: 'digit', digit: '7' },
      { type: 'backspace' },
      { type: 'backspace' },
      { type: 'backspace' },
    ]

    for (const action of actions) {
      state = calculatorReducer(state, action)
    }

    expect(state.currentValue).toBe('0')
  })

  it('resets overwrite state when backspace follows evaluation', () => {
    const evaluated = runActions([
      { type: 'digit', digit: '1' },
      { type: 'operator', operator: '+' },
      { type: 'digit', digit: '2' },
      { type: 'evaluate' },
    ])

    const state = calculatorReducer(evaluated, { type: 'backspace' })
    expect(state.currentValue).toBe('0')
    expect(state.lastOperator).toBeNull()
  })

  it('treats a trailing decimal point as an integer value', () => {
    const state = runActions([
      { type: 'digit', digit: '3' },
      { type: 'decimal' },
      { type: 'operator', operator: '+' },
      { type: 'digit', digit: '2' },
      { type: 'evaluate' },
    ])

    expect(state.currentValue).toBe('5')
  })

  it('supports repeated equals with the last operand', () => {
    let state = createInitialState()
    const actions: CalculatorAction[] = [
      { type: 'digit', digit: '3' },
      { type: 'operator', operator: '+' },
      { type: 'digit', digit: '2' },
      { type: 'evaluate' },
      { type: 'evaluate' },
      { type: 'evaluate' },
    ]

    for (const action of actions) {
      state = calculatorReducer(state, action)
    }

    expect(state.currentValue).toBe('9')
  })

  it('reuses the previous operand when equals is pressed immediately', () => {
    const state = runActions([
      { type: 'digit', digit: '3' },
      { type: 'operator', operator: '+' },
      { type: 'evaluate' },
    ])

    expect(state.currentValue).toBe('6')
  })

  it('normalises -0 operands before evaluating', () => {
    const customState: CalculatorState = {
      currentValue: '-0',
      previousValue: '5',
      operator: '+',
      overwrite: false,
      error: false,
      lastOperator: null,
      lastOperand: null,
    }

    const result = calculatorReducer(customState, { type: 'evaluate' })
    expect(result.currentValue).toBe('5')
  })

  it('guards against non-finite operands', () => {
    const customState: CalculatorState = {
      currentValue: 'Infinity',
      previousValue: '1',
      operator: '+',
      overwrite: false,
      error: false,
      lastOperator: null,
      lastOperand: null,
    }

    const result = calculatorReducer(customState, { type: 'evaluate' })
    expect(result.error).toBe(true)
    expect(result.currentValue).toBe('Error')
  })

  it('reports an error when toggling the sign of a non-finite value', () => {
    const customState: CalculatorState = {
      ...createInitialState(),
      currentValue: 'Infinity',
    }

    const result = calculatorReducer(customState, { type: 'toggle-sign' })
    expect(result.error).toBe(true)
    expect(result.currentValue).toBe('Error')
  })

  it('reports an error when converting a non-finite percent', () => {
    const customState: CalculatorState = {
      ...createInitialState(),
      currentValue: 'Infinity',
    }

    const result = calculatorReducer(customState, { type: 'percent' })
    expect(result.error).toBe(true)
    expect(result.currentValue).toBe('Error')
  })

  it('builds an error state when repeated equals leads to division by zero', () => {
    const customState: CalculatorState = {
      currentValue: '5',
      previousValue: null,
      operator: null,
      overwrite: true,
      error: false,
      lastOperator: '/' as Operator,
      lastOperand: '0',
    }

    const result = calculatorReducer(customState, { type: 'evaluate' })
    expect(result.error).toBe(true)
    expect(result.currentValue).toBe('Error')
  })

  it('falls back to the left operand for unexpected operators', () => {
    const customState: CalculatorState = {
      currentValue: '5',
      previousValue: '3',
      operator: '%' as Operator,
      overwrite: false,
      error: false,
      lastOperator: null,
      lastOperand: null,
    }

    const result = calculatorReducer(customState, { type: 'evaluate' })
    expect(result.currentValue).toBe('3')
  })

  it('converts stray decimal points to zero during operations', () => {
    const customState: CalculatorState = {
      ...createInitialState(),
      currentValue: '.',
    }

    const result = calculatorReducer(customState, { type: 'operator', operator: '+' })
    expect(result.previousValue).toBe('0')
    expect(result.currentValue).toBe('0')
  })

  it('returns an error on division by zero and recovers after digit input', () => {
    let state = createInitialState()
    const sequence: CalculatorAction[] = [
      { type: 'digit', digit: '7' },
      { type: 'operator', operator: '/' },
      { type: 'digit', digit: '0' },
      { type: 'evaluate' },
    ]

    for (const action of sequence) {
      state = calculatorReducer(state, action)
    }

    expect(state.error).toBe(true)
    expect(state.currentValue).toBe('Error')

    state = calculatorReducer(state, { type: 'digit', digit: '9' })
    expect(state.error).toBe(false)
    expect(state.currentValue).toBe('9')
  })

  it('resets an error state when clear entry is pressed', () => {
    let state = createInitialState()
    const sequence: CalculatorAction[] = [
      { type: 'digit', digit: '8' },
      { type: 'operator', operator: '/' },
      { type: 'digit', digit: '0' },
      { type: 'evaluate' },
    ]

    for (const action of sequence) {
      state = calculatorReducer(state, action)
    }

    const cleared = calculatorReducer(state, { type: 'clear-entry' })
    expect(cleared.error).toBe(false)
    expect(cleared.currentValue).toBe('0')
  })

  it('limits input to twelve significant digits', () => {
    let state = createInitialState()
    for (let index = 0; index < 15; index += 1) {
      state = calculatorReducer(state, { type: 'digit', digit: '9' })
    }

    expect(state.currentValue.length).toBe(12)
    expect(state.currentValue).toBe('999999999999')
  })
})

describe('formatNumber', () => {
  it('normalises floating point artefacts', () => {
    expect(formatNumber(2.4 - 2.2)).toBe('0.2')
  })

  it('uses exponential notation for very large numbers', () => {
    expect(formatNumber(1234567890123)).toBe('1.23456789012e+12')
  })

  it('uses exponential notation for very small numbers', () => {
    expect(formatNumber(0.0000000001234)).toBe('1.234e-10')
  })

  it('avoids negative zero', () => {
    expect(formatNumber(-0)).toBe('0')
  })
})
