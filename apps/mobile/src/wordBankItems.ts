// Word bank (문장 조립) content. Sentences are sourced from the existing fixture
// modules (practice sequence / listening / mini stories / roleplay) so the game
// reuses the same daily-life set instead of inventing new content. Each item is
// split into tappable chips — curated furigana word segments when available,
// else a naive script-boundary/particle split — and shuffled deterministically
// per sentence so the same sentence always shows the same chip order.
import { PRACTICE_SEQUENCE } from './practiceSequence';
import { LISTENING_ITEMS } from './listeningItems';
import { MINI_STORIES } from './miniStories';
import { ROLEPLAY_ITEMS } from './roleplayItems';
import { findFurigana } from './i18n';

export type WordBankItem = {
  id: string;
  ja: string; // original sentence (for TTS)
  reading?: string; // kana gloss when the source provides one
  ko: string; // meaning prompt
  chips: string[]; // correct-order segments (punctuation stripped)
  answer: string; // chips.join('')
  xpReward: number;
};

const PUNCT = /[\s。、．，！？!?…・「」『』（）()]/g;
const strip = (s: string) => s.replace(PUNCT, '');

type Script = 'kanji' | 'hira' | 'kata' | 'other';
function scriptOf(ch: string): Script {
  if (/[一-龯々]/.test(ch)) return 'kanji';
  if (/[ぁ-ん]/.test(ch)) return 'hira';
  if (/[ァ-ヶー]/.test(ch)) return 'kata';
  return 'other';
}

// Split a hiragana run after the least-ambiguous particles (は/が/を) so e.g.
// 「はどうだった」 becomes 「は」+「どうだった」. No lookbehind regex (Hermes).
function splitAfterParticles(run: string): string[] {
  const parts: string[] = [];
  let cur = '';
  for (let i = 0; i < run.length; i++) {
    cur += run[i];
    if ('はがを'.includes(run[i]) && i < run.length - 1) {
      parts.push(cur);
      cur = '';
    }
  }
  if (cur) parts.push(cur);
  return parts;
}

// Naive fallback: punctuation splits first (so clause boundaries never merge
// across 、/。), then script-boundary runs, then particle splits inside kana
// runs. A sentence that still yields one chip falls back to 2-char groups so
// every sentence stays assemblable.
function naiveSegments(sentence: string): string[] {
  const segs: string[] = [];
  for (const clause of sentence.split(PUNCT)) {
    if (clause.length === 0) continue;
    const runs: string[] = [];
    for (const ch of clause) {
      const last = runs[runs.length - 1];
      if (last && scriptOf(last[last.length - 1]) === scriptOf(ch)) runs[runs.length - 1] = last + ch;
      else runs.push(ch);
    }
    for (const run of runs) {
      if (scriptOf(run[0]) === 'hira' && run.length > 2) segs.push(...splitAfterParticles(run));
      else segs.push(run);
    }
  }
  if (segs.length < 2) {
    const clean = strip(sentence);
    const pairs: string[] = [];
    for (let i = 0; i < clean.length; i += 2) pairs.push(clean.slice(i, i + 2));
    return pairs;
  }
  return segs;
}

export function segmentSentence(ja: string): string[] {
  const tokens = findFurigana(ja);
  if (tokens && tokens.length > 1) {
    const segs = tokens.map((t) => strip(t.b)).filter((b) => b.length > 0);
    if (segs.length >= 2) return segs;
  }
  return naiveSegments(ja);
}

function hashOf(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

// Deterministic (sentence-seeded) Fisher-Yates; rotate once if the shuffle
// happens to land on the solved order so the game is never pre-solved.
export function shuffledChips(item: WordBankItem): string[] {
  const a = item.chips.slice();
  let s = hashOf(item.ja) || 1;
  const rnd = () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 4294967296;
  };
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    const tmp = a[i];
    a[i] = a[j];
    a[j] = tmp;
  }
  if (a.length > 1 && a.join('') === item.chips.join('')) {
    const first = a.shift();
    if (first !== undefined) a.push(first);
  }
  return a;
}

// Korean glosses for fixture sentences whose source has no per-line KO field
// (story lines / roleplay partner lines). Keyed by the exact JA string.
const KO_GLOSS: Record<string, string> = {
  '今日はどうだった？': '오늘 어땠어?',
  'そっか、ゆっくり休んでね。': '그렇구나, 푹 쉬어.',
  'おなかすいた？': '배고파?',
  'うん、何か食べよう。': '응, 뭐 좀 먹자.',
  'いいね、ラーメンにする？': '좋네, 라멘으로 할까?',
  '明日もテストだよね。': '내일도 시험이지?',
  'うん、でも頑張ろうね。': '응, 그래도 힘내자.',
  'うん、一緒に頑張ろう！': '응, 같이 힘내자!',
  '明日テストなんだ…。': '내일 시험이야….',
  '大丈夫、一緒に頑張ろう！': '괜찮아, 같이 힘내자!',
};

function buildItems(): WordBankItem[] {
  const candidates: { ja: string; reading?: string; ko?: string }[] = [];
  for (const p of PRACTICE_SEQUENCE) {
    candidates.push({ ja: p.ja, ko: p.ko, reading: LISTENING_ITEMS.find((l) => l.ja === p.ja)?.reading });
  }
  for (const l of LISTENING_ITEMS) {
    candidates.push({ ja: l.ja, reading: l.reading, ko: l.choices.find((c) => c.id === l.correctChoiceId)?.label });
  }
  for (const story of MINI_STORIES) {
    for (const line of story.lines) candidates.push({ ja: line.text, reading: line.reading, ko: KO_GLOSS[line.text] });
  }
  for (const r of ROLEPLAY_ITEMS) {
    candidates.push({ ja: r.partnerJa, reading: r.partnerReading, ko: KO_GLOSS[r.partnerJa] });
    candidates.push({ ja: r.replyJa, reading: r.replyReading, ko: r.replyKo });
  }

  const seen = new Set<string>();
  const items: WordBankItem[] = [];
  for (const c of candidates) {
    const key = strip(c.ja);
    if (!c.ko || key.length === 0 || seen.has(key)) continue;
    seen.add(key);
    const chips = segmentSentence(c.ja);
    if (chips.length < 2) continue;
    items.push({
      id: `bank_${hashOf(key).toString(36)}`,
      ja: c.ja,
      reading: c.reading,
      ko: c.ko,
      chips,
      answer: chips.join(''),
      xpReward: 12,
    });
  }
  return items;
}

export const WORD_BANK_ITEMS: WordBankItem[] = buildItems();
export const WORD_BANK_TOTAL = WORD_BANK_ITEMS.length;
