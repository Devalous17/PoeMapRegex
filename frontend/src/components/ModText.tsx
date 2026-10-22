/** Color emphasis is presentation only; source text and modifier decisions stay intact. */
const keywords = /\b(fire|burning|ignite|lightning|shock(?:ed|ing)?|cold|chill(?:ed|ing)?|freez(?:e|ing)|frozen|chaos|poison|critical(?: strike)?(?:s)?|armour|evasion|energy shield|mana|life|bleed(?:ing)?|physical)\b/gi;
function colorFor(word: string): string {
  if (/^(fire|burning|ignite|armour|life|bleed)/i.test(word)) return 'fire';
  if (/^(lightning|shock)/i.test(word)) return 'lightning';
  if (/^(cold|chill|freez|frozen)/i.test(word)) return 'cold';
  if (/^(chaos|poison)/i.test(word)) return 'chaos';
  if (/^critical/i.test(word)) return 'critical';
  if (/^evasion/i.test(word)) return 'evasion';
  if (/^energy/i.test(word)) return 'shield';
  if (/^mana/i.test(word)) return 'mana';
  return 'physical';
}
export function ModText({text}: {text: string}) {
  return <>{text.split(keywords).map((part, index) => index % 2 ? <span className={`mod-term mod-term--${colorFor(part)}`} key={index}>{part}</span> : part)}</>;
}
