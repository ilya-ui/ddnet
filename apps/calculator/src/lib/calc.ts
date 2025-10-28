export type Operator = '+' | '-' | '*' | '/'

export interface CalculatorState {
  currentValue: string
  previousValue: string | null
  operator: Operator | null
  overwrite: boolean
  error: boolean
  lastOperator: Operator | null
  lastOperand: string | null
}

export type CalculatorAction =
  | { type: 'digit'; digit: string }
  | { type: 'decimal' }
  | { type: 'operator'; operator: Operator }
  | { type: 'evaluate' }
  | { type: 'clear-all' }
  | { type: 'clear-entry' }
  | { type: 'toggle-sign' }
  | { type: 'percent' }
  | { type: 'backspace' }

export const ERROR_VALUE = 'Error'
export const MAX_SIGNIFICANT_DIGITS = 12
const EPSILON = 1e-12

export function createInitialState(): CalculatorState {
  return {
    currentValue: '0',
    previousValue: null,
    operator: null,
    overwrite: false,
    error: false,
    lastOperator: null,
    lastOperand: null,
  }
}

export function calculatorReducer(
  state: CalculatorState,
  action: CalculatorAction,
): CalculatorState {
  switch (action.type) {
    case 'digit':
      return handleDigit(state, action.digit)
    case 'decimal':
      return handleDecimal(state)
    case 'operator':
      return handleOperator(state, action.operator)
    case 'evaluate':
      return handleEvaluate(state)
    case 'clear-all':
      return createInitialState()
    case 'clear-entry':
      return handleClearEntry(state)
    case 'toggle-sign':
      return handleToggleSign(state)
    case 'percent':
      return handlePercent(state)
    case 'backspace':
      return handleBackspace(state)
    default:
      return state
  }
}

export function operatorToSymbol(operator: Operator): string {
  switch (operator) {
    case '+':
      return '+'
    case '-':
      return '−'
    case '*':
      return '×'
    case '/':
      return '÷'
    default:
      return operator
  }
}

export function formatNumber(value: number): string {
  if (!Number.isFinite(value)) {
    return ERROR_VALUE
  }

  if (Object.is(value, -0)) {
    return '0'
  }

  if (value === 0) {
    return '0'
  }

  const abs = Math.abs(value)
  if (abs >= 10 ** MAX_SIGNIFICANT_DIGITS || abs < 10 ** -9) {
    return sanitiseExponential(value.toExponential(MAX_SIGNIFICANT_DIGITS - 1))
  }

  let result = value.toPrecision(MAX_SIGNIFICANT_DIGITS)
  if (result.includes('e')) {
    return sanitiseExponential(value.toExponential(MAX_SIGNIFICANT_DIGITS - 1))
  }

  if (result.includes('.')) {
    result = result.replace(/(\.\d*?[1-9])0+$/, '$1')
    result = result.replace(/\.0+$/, '')
  }

  if (result.endsWith('.')) {
    result = result.slice(0, -1)
  }

  return result
}

function handleDigit(state: CalculatorState, digit: string): CalculatorState {
  if (!/^[0-9]$/.test(digit)) {
    return state
  }

  const baseState = state.error ? createInitialState() : state
  const startingOver = baseState.overwrite || baseState.currentValue === ERROR_VALUE

  let nextValue: string
  if (startingOver) {
    nextValue = digit
  } else if (baseState.currentValue === '0' && digit === '0' && !baseState.currentValue.includes('.')) {
    nextValue = '0'
  } else if (baseState.currentValue === '0' && !baseState.currentValue.includes('.')) {
    nextValue = digit
  } else {
    nextValue = `${baseState.currentValue}${digit}`
  }

  if (isDigitLimitExceeded(nextValue)) {
    return baseState
  }

  return {
    ...baseState,
    currentValue: nextValue,
    overwrite: false,
    error: false,
    lastOperator: null,
    lastOperand: null,
  }
}

function handleDecimal(state: CalculatorState): CalculatorState {
  const baseState = state.error ? createInitialState() : state

  if (baseState.overwrite) {
    return {
      ...baseState,
      currentValue: '0.',
      overwrite: false,
      error: false,
      lastOperator: null,
      lastOperand: null,
    }
  }

  if (baseState.currentValue.includes('.')) {
    return baseState
  }

  const nextValue = `${baseState.currentValue}.`

  if (isDigitLimitExceeded(nextValue)) {
    return baseState
  }

  return {
    ...baseState,
    currentValue: nextValue,
    lastOperator: null,
    lastOperand: null,
  }
}

function handleOperator(state: CalculatorState, operator: Operator): CalculatorState {
  const baseState = state.error ? createInitialState() : state

  if (baseState.operator && baseState.overwrite) {
    return {
      ...baseState,
      operator,
    }
  }

  if (baseState.operator && baseState.previousValue !== null && !baseState.overwrite) {
    const result = performCalculation(baseState.previousValue, baseState.currentValue, baseState.operator)
    if (result === null) {
      return buildErrorState()
    }

    return {
      currentValue: result,
      previousValue: result,
      operator,
      overwrite: true,
      error: false,
      lastOperator: null,
      lastOperand: null,
    }
  }

  const normalized = normalizeValue(baseState.currentValue)

  return {
    ...baseState,
    previousValue: normalized,
    currentValue: normalized,
    operator,
    overwrite: true,
    error: false,
    lastOperator: null,
    lastOperand: null,
  }
}

function handleEvaluate(state: CalculatorState): CalculatorState {
  if (state.error) {
    return state
  }

  if (state.operator && state.previousValue !== null) {
    const useCurrentValue = !state.overwrite || state.currentValue !== state.previousValue
    const rightOperand = useCurrentValue
      ? state.currentValue
      : state.lastOperand ?? state.previousValue

    const result = performCalculation(state.previousValue, rightOperand, state.operator)
    if (result === null) {
      return buildErrorState()
    }

    return {
      currentValue: result,
      previousValue: null,
      operator: null,
      overwrite: true,
      error: false,
      lastOperator: state.operator,
      lastOperand: normalizeValue(rightOperand),
    }
  }

  if (state.lastOperator && state.lastOperand !== null) {
    const result = performCalculation(state.currentValue, state.lastOperand, state.lastOperator)
    if (result === null) {
      return buildErrorState()
    }

    return {
      ...state,
      currentValue: result,
      overwrite: true,
      error: false,
    }
  }

  return state
}

function handleClearEntry(state: CalculatorState): CalculatorState {
  if (state.error) {
    return createInitialState()
  }

  return {
    ...state,
    currentValue: '0',
    overwrite: true,
    error: false,
    lastOperator: null,
    lastOperand: null,
  }
}

function handleToggleSign(state: CalculatorState): CalculatorState {
  const baseState = state.error ? createInitialState() : state

  const numeric = Number(normalizeValue(baseState.currentValue))
  const toggled = formatNumber(-numeric)
  if (toggled === ERROR_VALUE) {
    return buildErrorState()
  }

  return {
    ...baseState,
    currentValue: toggled,
    overwrite: false,
    error: false,
    lastOperator: null,
    lastOperand: null,
  }
}

function handlePercent(state: CalculatorState): CalculatorState {
  const baseState = state.error ? createInitialState() : state
  const current = Number(normalizeValue(baseState.currentValue))

  let computed: number
  if (baseState.previousValue !== null && baseState.operator) {
    const previous = Number(normalizeValue(baseState.previousValue))
    computed = (previous * current) / 100
  } else {
    computed = current / 100
  }

  const formatted = formatNumber(computed)
  if (formatted === ERROR_VALUE) {
    return buildErrorState()
  }

  return {
    ...baseState,
    currentValue: formatted,
    overwrite: true,
    error: false,
    lastOperator: null,
    lastOperand: null,
  }
}

function handleBackspace(state: CalculatorState): CalculatorState {
  const baseState = state.error ? createInitialState() : state

  if (baseState.overwrite) {
    return {
      ...baseState,
      currentValue: '0',
      error: false,
      lastOperator: null,
      lastOperand: null,
    }
  }

  if (baseState.currentValue.length === 1 || (baseState.currentValue.length === 2 && baseState.currentValue.startsWith('-') && !baseState.currentValue.includes('.'))) {
    return {
      ...baseState,
      currentValue: '0',
    }
  }

  const nextValue = baseState.currentValue.slice(0, -1) || '0'

  return {
    ...baseState,
    currentValue: nextValue,
  }
}

function performCalculation(left: string, right: string, operator: Operator): string | null {
  const leftValue = Number(normalizeValue(left))
  const rightValue = Number(normalizeValue(right))

  if (!Number.isFinite(leftValue) || !Number.isFinite(rightValue)) {
    return null
  }

  if (operator === '/' && Math.abs(rightValue) < EPSILON) {
    return null
  }

  let result: number
  switch (operator) {
    case '+':
      result = leftValue + rightValue
      break
    case '-':
      result = leftValue - rightValue
      break
    case '*':
      result = leftValue * rightValue
      break
    case '/':
      result = leftValue / rightValue
      break
    default:
      result = leftValue
  }

  const formatted = formatNumber(result)
  return formatted === ERROR_VALUE ? null : formatted
}

function normalizeValue(value: string): string {
  if (value === ERROR_VALUE || value === '' || value === '.') {
    return '0'
  }

  let normalized = value
  if (normalized.endsWith('.')) {
    normalized = normalized.slice(0, -1)
  }

  if (normalized === '-0' || normalized === '-') {
    return '0'
  }

  return normalized
}

function isDigitLimitExceeded(value: string): boolean {
  const digits = value.replace(/[-.]/g, '')
  return digits.length > MAX_SIGNIFICANT_DIGITS
}

function buildErrorState(): CalculatorState {
  return {
    currentValue: ERROR_VALUE,
    previousValue: null,
    operator: null,
    overwrite: true,
    error: true,
    lastOperator: null,
    lastOperand: null,
  }
}

function sanitiseExponential(input: string): string {
  const [rawMantissa, rawExponent = '0'] = input.split('e')

  let formattedMantissa = rawMantissa
  if (formattedMantissa.includes('.')) {
    formattedMantissa = formattedMantissa.replace(/(\.\d*?[1-9])0+$/, '$1')
    formattedMantissa = formattedMantissa.replace(/\.0+$/, '')
    formattedMantissa = formattedMantissa.replace(/\.$/, '')
  }

  const exponentNumber = Number(rawExponent)
  const exponentSign = exponentNumber >= 0 ? '+' : '-'
  const exponentValue = Math.abs(exponentNumber).toString()

  return `${formattedMantissa}e${exponentSign}${exponentValue}`
}
