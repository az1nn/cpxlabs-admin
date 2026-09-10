const DEFAULT_FRACTION_DIGITS = 2

function normalizeCurrency(currency: string) {
  return currency.trim().toUpperCase()
}

export function currencyFractionDigits(currency: string): number {
  const normalized = normalizeCurrency(currency)

  if (!/^[A-Z]{3}$/.test(normalized)) return DEFAULT_FRACTION_DIGITS

  try {
    return new Intl.NumberFormat('en', {
      style: 'currency',
      currency: normalized,
    }).resolvedOptions().maximumFractionDigits ?? DEFAULT_FRACTION_DIGITS
  } catch {
    // The reference API intentionally accepts ISO-style three-letter codes without
    // maintaining its own currency catalogue. Unknown codes therefore retain the
    // conventional two-decimal fallback instead of becoming a frontend-only policy.
    return DEFAULT_FRACTION_DIGITS
  }
}

export function currencyMinorUnitStep(currency: string): string {
  const digits = currencyFractionDigits(currency)
  return digits === 0 ? '1' : `0.${'0'.repeat(digits - 1)}1`
}

export function majorAmountToMinorUnits(amount: string, currency: string): number {
  const normalizedAmount = amount.trim()
  const match = /^(\d+)(?:\.(\d+))?$/.exec(normalizedAmount)

  if (!match) {
    throw new Error('Amount must be a non-negative decimal number using a dot separator')
  }

  const digits = currencyFractionDigits(currency)
  const fraction = match[2] ?? ''

  if (fraction.length > digits) {
    throw new Error(
      digits === 0
        ? `${normalizeCurrency(currency)} does not use fractional minor units`
        : `Use at most ${digits} decimal places for ${normalizeCurrency(currency)}`,
    )
  }

  const scale = 10n ** BigInt(digits)
  const wholeMinor = BigInt(match[1] ?? '0') * scale
  const fractionMinor = fraction ? BigInt(fraction.padEnd(digits, '0')) : 0n
  const minorUnits = wholeMinor + fractionMinor

  if (minorUnits > BigInt(Number.MAX_SAFE_INTEGER)) {
    throw new Error('Amount exceeds the supported safe integer range')
  }

  return Number(minorUnits)
}

function fallbackMinorUnitText(amountMinor: number, currency: string, digits: number) {
  const raw = String(amountMinor).padStart(digits + 1, '0')
  if (digits === 0) return `${currency} ${raw}`
  return `${currency} ${raw.slice(0, -digits)}.${raw.slice(-digits)}`
}

export function formatMinorUnits(
  amountMinor: number,
  currency: string,
  locale = 'en',
): string {
  if (!Number.isSafeInteger(amountMinor) || amountMinor < 0) {
    throw new Error('Minor-unit amount must be a non-negative safe integer')
  }

  const normalizedCurrency = normalizeCurrency(currency)
  const digits = currencyFractionDigits(normalizedCurrency)

  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: normalizedCurrency,
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(amountMinor / 10 ** digits)
  } catch {
    return fallbackMinorUnitText(amountMinor, normalizedCurrency, digits)
  }
}
