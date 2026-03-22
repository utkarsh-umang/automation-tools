/**
 * Validation rule from workflow Story 4.2:
 * 1. Strip all valid quoted terms
 * 2. Remove all commas from what remains
 * 3. Trim whitespace from what remains
 * 4. If anything is left over (length > 0), the format is invalid
 */
export function isValidSearchTermsFormat(input: string): boolean {
  const stripped = input.replace(/"[^"]+"/g, '')
  const noCommas = stripped.replace(/,/g, '')
  return noCommas.trim().length === 0
}

/** Extract inner text from each "quoted" segment. */
export function parseQuotedTerms(input: string): string[] {
  const re = /"([^"]*)"/g
  const out: string[] = []
  let m: RegExpExecArray | null
  while ((m = re.exec(input)) !== null) {
    out.push(m[1])
  }
  return out
}
