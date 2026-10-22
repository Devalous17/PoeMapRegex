/** Visible summaries use one sentence; tooltips retain the original explanation. */
export function assessmentSummary(reason: string): string {
  const sentences = reason.trim().split(/(?<=[.!?])\s+(?=[A-Z])/).filter(Boolean);
  const useful = sentences.filter(sentence => !/^Normal pool, worst catalogue roll/i.test(sentence));
  return (useful[0] ?? sentences[0] ?? '').trim();
}
