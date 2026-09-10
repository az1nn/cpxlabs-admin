import { describe, expect, it } from 'vitest'

import {
  currencyFractionDigits,
  currencyMinorUnitStep,
  formatMinorUnits,
  majorAmountToMinorUnits,
} from './opportunity-money'

describe('opportunity money helpers', () => {
  it('resolves currency minor-unit scales without assuming two decimals', () => {
    expect(currencyFractionDigits('BRL')).toBe(2)
    expect(currencyFractionDigits('JPY')).toBe(0)
    expect(currencyFractionDigits('KWD')).toBe(3)
    expect(currencyMinorUnitStep('BRL')).toBe('0.01')
    expect(currencyMinorUnitStep('JPY')).toBe('1')
    expect(currencyMinorUnitStep('KWD')).toBe('0.001')
  })

  it('converts decimal strings to safe integer minor units without floating-point multiplication', () => {
    expect(majorAmountToMinorUnits('125000.50', 'BRL')).toBe(12_500_050)
    expect(majorAmountToMinorUnits('1250', 'JPY')).toBe(1_250)
    expect(majorAmountToMinorUnits('1.234', 'KWD')).toBe(1_234)
  })

  it('rejects precision that the selected currency cannot represent', () => {
    expect(() => majorAmountToMinorUnits('1250.1', 'JPY')).toThrow(/does not use fractional minor units/)
    expect(() => majorAmountToMinorUnits('1.234', 'BRL')).toThrow(/at most 2 decimal places/)
  })

  it('rejects values outside the shared safe-integer transport range', () => {
    expect(() => majorAmountToMinorUnits('90071992547409.92', 'BRL')).toThrow(/safe integer range/)
  })

  it('formats minor-unit values using the selected currency scale', () => {
    expect(formatMinorUnits(12_500_050, 'BRL', 'en-US')).toContain('125,000.50')
    expect(formatMinorUnits(1_250, 'JPY', 'en-US')).toMatch(/1,250/)
    expect(formatMinorUnits(1_234, 'KWD', 'en-US')).toContain('1.234')
  })
})
