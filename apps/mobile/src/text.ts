// Token-level pronunciation diff for the correction UX. Compares what the
// learner said (STT) against the target phrase and marks each target character
// correct / wrong via an LCS alignment. Works with the existing mock/real STT
// payload - no new API.
export type DiffSeg = { ch: string; status: 'correct' | 'wrong' };

function normalize(s: string): string {
  return s.replace(/[。、!?.\s]/g, '');
}

// Longest common subsequence membership for target characters.
export function diffChars(target: string, said: string): DiffSeg[] {
  const t = normalize(target);
  const s = normalize(said);
  const n = t.length;
  const m = s.length;
  const dp: number[][] = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = 1; i <= n; i++) {
    for (let j = 1; j <= m; j++) {
      dp[i][j] = t[i - 1] === s[j - 1] ? dp[i - 1][j - 1] + 1 : Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }
  // backtrack to mark which target chars are part of the LCS (correct)
  const correct = new Array(n).fill(false);
  let i = n;
  let j = m;
  while (i > 0 && j > 0) {
    if (t[i - 1] === s[j - 1]) {
      correct[i - 1] = true;
      i--;
      j--;
    } else if (dp[i - 1][j] >= dp[i][j - 1]) {
      i--;
    } else {
      j--;
    }
  }
  return Array.from(t).map((ch, idx) => ({ ch, status: correct[idx] ? 'correct' : 'wrong' }));
}

export function accuracyOf(segs: DiffSeg[]): number {
  if (segs.length === 0) return 0;
  const ok = segs.filter((s) => s.status === 'correct').length;
  return Math.round((ok / segs.length) * 100);
}

// ---- listen-and-type (받아쓰기) normalization ----
// Strip whitespace/punctuation only. ー (long vowel mark) is meaningful in
// katakana (ラーメン) so it is deliberately NOT stripped.
const DICTATION_PUNCT = /[\s。、．，！？!?…・「」『』（）()]/g;

export function stripForDictation(s: string): string {
  return s.replace(DICTATION_PUNCT, '');
}

export function kataToHira(s: string): string {
  return s.replace(/[ァ-ヶ]/g, (ch) => String.fromCharCode(ch.charCodeAt(0) - 0x60));
}

// Dictation check: accept the raw sentence (kanji) or its kana reading;
// katakana input counts as its hiragana equivalent so IME differences don't
// fail the learner.
export function dictationMatch(input: string, targetJa: string, reading?: string): boolean {
  const cleaned = stripForDictation(input);
  if (cleaned.length === 0) return false;
  if (cleaned === stripForDictation(targetJa)) return true;
  if (reading && kataToHira(cleaned) === kataToHira(stripForDictation(reading))) return true;
  return false;
}
