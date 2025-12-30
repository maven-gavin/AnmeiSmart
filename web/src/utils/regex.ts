export function escapeRegExp(input: string): string {
  // Escape characters that have special meaning in regular expressions
  // Ref: MDN https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_expressions#escaping
  return input.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}


