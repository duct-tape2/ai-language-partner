// F6. Client-side mock for POST /v1/dialogue/match (mock mode only). The real
// matcher embeds+compares on the server; this stub uses bigram Dice similarity over
// candidate texts (available locally in mock). Thresholds mirror the contract
// (§6.2 / dialogue_match.py): >=0.75 match / 0.55-0.75 confirm / <0.55 fallback.
// Global-intent set matches backend: repeat / hint / quit / slow (JP + KR).
import type { Candidate, DialogueMatchResponse, GlobalIntent } from './types';

const MATCH_MIN = 0.75;
const CONFIRM_MIN = 0.55;

function normalize(s: string): string {
  return s.replace(/[\s、。！？!?.,「」『』…~〜ー]/g, '').toLowerCase().trim();
}

function bigrams(s: string): Set<string> {
  const out = new Set<string>();
  if (s.length < 2) {
    if (s) out.add(s);
    return out;
  }
  for (let i = 0; i < s.length - 1; i++) out.add(s.slice(i, i + 2));
  return out;
}

function dice(a: string, b: string): number {
  const na = normalize(a);
  const nb = normalize(b);
  if (!na || !nb) return 0;
  if (na === nb) return 1;
  if (na.includes(nb) || nb.includes(na)) return 0.9;
  const A = bigrams(na);
  const B = bigrams(nb);
  let inter = 0;
  for (const g of A) if (B.has(g)) inter++;
  return (2 * inter) / (A.size + B.size);
}

const GLOBAL_INTENT_PATTERNS: { intent: GlobalIntent; re: RegExp }[] = [
  { intent: 'repeat', re: /(もう一回|もういっかい|もう一度|もっかい|다시|한 ?번 ?더)/ },
  { intent: 'slow', re: /(ゆっくり|천천히|slow)/ },
  { intent: 'hint', re: /(ヒント|힌트|도와|모르겠|わからない|分からない)/ },
  { intent: 'quit', re: /(やめる|終わり|おわり|그만|끝|バイバイ|ばいばい|さようなら)/ },
];

export function detectGlobalIntent(utterance: string): GlobalIntent | null {
  const n = utterance.trim();
  for (const p of GLOBAL_INTENT_PATTERNS) if (p.re.test(n)) return p.intent;
  return null;
}

export function matchMock(utterance: string, candidates: Candidate[], confirmLineId: string | null): DialogueMatchResponse {
  const globalIntent = detectGlobalIntent(utterance);
  if (globalIntent) {
    return { tier: 'match', matchedLineId: null, score: 1, confirmLineId: null, globalIntent, latencyMs: 5 };
  }

  let best: Candidate | null = null;
  let bestScore = 0;
  for (const c of candidates) {
    const s = dice(utterance, c.text);
    if (s > bestScore) {
      bestScore = s;
      best = c;
    }
  }

  if (best && bestScore >= MATCH_MIN) {
    return { tier: 'match', matchedLineId: best.lineId, score: bestScore, confirmLineId: null, globalIntent: null, latencyMs: 5 };
  }
  if (best && bestScore >= CONFIRM_MIN) {
    return { tier: 'confirm', matchedLineId: best.lineId, score: bestScore, confirmLineId, globalIntent: null, latencyMs: 5 };
  }
  return { tier: 'fallback', matchedLineId: null, score: bestScore, confirmLineId: null, globalIntent: null, latencyMs: 5 };
}
