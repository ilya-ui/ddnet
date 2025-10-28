import type { CalculatorAction } from './calc'

export type KeyVariant = 'number' | 'operator' | 'function' | 'equals'

export interface KeyDefinition {
  id: string
  label: string
  ariaLabel?: string
  action: CalculatorAction
  variant: KeyVariant
  gridArea: string
  keyboard?: string[]
}

interface KeyBinding {
  action: CalculatorAction
  buttonId: string
}

export const keyDefinitions: KeyDefinition[] = [
  {
    id: 'clear-all',
    label: 'AC',
    ariaLabel: 'All clear',
    action: { type: 'clear-all' },
    variant: 'function',
    gridArea: 'ac',
    keyboard: ['Escape'],
  },
  {
    id: 'clear-entry',
    label: 'C',
    ariaLabel: 'Clear entry',
    action: { type: 'clear-entry' },
    variant: 'function',
    gridArea: 'c',
    keyboard: ['Delete'],
  },
  {
    id: 'percent',
    label: '%',
    ariaLabel: 'Percent',
    action: { type: 'percent' },
    variant: 'function',
    gridArea: 'percent',
    keyboard: ['%'],
  },
  {
    id: 'divide',
    label: '÷',
    ariaLabel: 'Divide',
    action: { type: 'operator', operator: '/' },
    variant: 'operator',
    gridArea: 'divide',
    keyboard: ['/', '÷', ':'],
  },
  {
    id: 'seven',
    label: '7',
    action: { type: 'digit', digit: '7' },
    variant: 'number',
    gridArea: 'seven',
    keyboard: ['7'],
  },
  {
    id: 'eight',
    label: '8',
    action: { type: 'digit', digit: '8' },
    variant: 'number',
    gridArea: 'eight',
    keyboard: ['8'],
  },
  {
    id: 'nine',
    label: '9',
    action: { type: 'digit', digit: '9' },
    variant: 'number',
    gridArea: 'nine',
    keyboard: ['9'],
  },
  {
    id: 'multiply',
    label: '×',
    ariaLabel: 'Multiply',
    action: { type: 'operator', operator: '*' },
    variant: 'operator',
    gridArea: 'multiply',
    keyboard: ['*', 'x', 'X', '×'],
  },
  {
    id: 'four',
    label: '4',
    action: { type: 'digit', digit: '4' },
    variant: 'number',
    gridArea: 'four',
    keyboard: ['4'],
  },
  {
    id: 'five',
    label: '5',
    action: { type: 'digit', digit: '5' },
    variant: 'number',
    gridArea: 'five',
    keyboard: ['5'],
  },
  {
    id: 'six',
    label: '6',
    action: { type: 'digit', digit: '6' },
    variant: 'number',
    gridArea: 'six',
    keyboard: ['6'],
  },
  {
    id: 'subtract',
    label: '−',
    ariaLabel: 'Subtract',
    action: { type: 'operator', operator: '-' },
    variant: 'operator',
    gridArea: 'subtract',
    keyboard: ['-'],
  },
  {
    id: 'one',
    label: '1',
    action: { type: 'digit', digit: '1' },
    variant: 'number',
    gridArea: 'one',
    keyboard: ['1'],
  },
  {
    id: 'two',
    label: '2',
    action: { type: 'digit', digit: '2' },
    variant: 'number',
    gridArea: 'two',
    keyboard: ['2'],
  },
  {
    id: 'three',
    label: '3',
    action: { type: 'digit', digit: '3' },
    variant: 'number',
    gridArea: 'three',
    keyboard: ['3'],
  },
  {
    id: 'add',
    label: '+',
    ariaLabel: 'Add',
    action: { type: 'operator', operator: '+' },
    variant: 'operator',
    gridArea: 'add',
    keyboard: ['+'],
  },
  {
    id: 'sign',
    label: '±',
    ariaLabel: 'Toggle sign',
    action: { type: 'toggle-sign' },
    variant: 'function',
    gridArea: 'sign',
    keyboard: ['F9'],
  },
  {
    id: 'zero',
    label: '0',
    action: { type: 'digit', digit: '0' },
    variant: 'number',
    gridArea: 'zero',
    keyboard: ['0'],
  },
  {
    id: 'decimal',
    label: '.',
    ariaLabel: 'Decimal',
    action: { type: 'decimal' },
    variant: 'number',
    gridArea: 'decimal',
    keyboard: ['.', ','],
  },
  {
    id: 'equals',
    label: '=',
    ariaLabel: 'Equals',
    action: { type: 'evaluate' },
    variant: 'equals',
    gridArea: 'equals',
    keyboard: ['=', 'Enter', 'NumpadEnter'],
  },
  {
    id: 'backspace',
    label: '⌫',
    ariaLabel: 'Backspace',
    action: { type: 'backspace' },
    variant: 'function',
    gridArea: 'backspace',
    keyboard: ['Backspace'],
  },
]

const shortcutRegistry = new Map<string, KeyBinding>()

for (const definition of keyDefinitions) {
  for (const key of definition.keyboard ?? []) {
    shortcutRegistry.set(normalizeKey(key), {
      action: definition.action,
      buttonId: definition.id,
    })
  }
}

export function getBindingForKey(key: string): KeyBinding | null {
  const normalized = normalizeKey(key)
  return shortcutRegistry.get(normalized) ?? null
}

function normalizeKey(key: string): string {
  if (key === 'Enter' || key === 'NumpadEnter') {
    return 'Enter'
  }

  if (key === 'Backspace' || key === 'Delete' || key === 'Escape') {
    return key
  }

  if (key === ',') {
    return '.'
  }

  if (key === '÷') {
    return '/'
  }

  if (key === '×') {
    return '*'
  }

  if (key.length === 1) {
    const lower = key.toLowerCase()
    if (lower === 'x') {
      return '*'
    }
    return lower
  }

  return key
}
