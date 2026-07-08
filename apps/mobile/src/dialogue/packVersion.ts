import type { DialoguePackSummary } from './types';

export function parsePackVersion(version: string): number | null {
  const match = /^v(0|[1-9]\d*)$/.exec(version);
  if (!match) return null;
  const parsed = Number(match[1]);
  return Number.isSafeInteger(parsed) ? parsed : null;
}

export function comparePackVersions(a: string, b: string): number {
  const aParsed = parsePackVersion(a);
  const bParsed = parsePackVersion(b);
  if (aParsed !== null && bParsed !== null) return aParsed - bParsed;
  if (aParsed !== null) return 1;
  if (bParsed !== null) return -1;
  return a.localeCompare(b);
}

type LatestOptions = {
  onInvalid?: (pack: DialoguePackSummary, reason: string) => void;
};

export function latestPerPersona(list: DialoguePackSummary[], options: LatestOptions = {}): DialoguePackSummary[] {
  const best = new Map<string, DialoguePackSummary>();
  let validCount = 0;

  for (const pack of list) {
    if (parsePackVersion(pack.packVersion) === null) {
      options.onInvalid?.(pack, 'Expected packVersion format v<number>, for example v1 or v10.');
      continue;
    }
    validCount += 1;
    const cur = best.get(pack.personaId);
    if (!cur || comparePackVersions(pack.packVersion, cur.packVersion) > 0) best.set(pack.personaId, pack);
  }

  if (list.length > 0 && validCount === 0) {
    throw new Error('No valid dialogue packs returned. Expected packVersion format v<number>.');
  }

  return Array.from(best.values()).sort((a, b) => a.personaId.localeCompare(b.personaId));
}
