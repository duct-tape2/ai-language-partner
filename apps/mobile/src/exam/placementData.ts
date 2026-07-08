// Placement Test (배치 테스트) content. A short 6-question level check that
// ramps from easy (N5) to harder (N4) so onboarding can recommend a starting
// level. Self-contained, hand-authored data (no network fetch at runtime).
// Each item has a JA prompt, optional furigana tokens for the prompt (so the
// kanji reads correctly when shown), Korean choices, the answer index, and a
// Korean skill tag used to surface weak areas on the result screen.
export type PlacementLevel = 'N5' | 'N4';
export type FuriToken = { b: string; r?: string };

export type PlacementQuestion = {
  id: string;
  level: PlacementLevel;
  promptJa: string;
  promptTokens?: FuriToken[];
  choices: string[];
  answerIndex: number;
  skillTagKo: string;
};

// Ordered easy -> hard: three N5 items first, then three N4 items.
export const PLACEMENT_QUESTIONS: PlacementQuestion[] = [
  {
    id: 'p1_particle_wa',
    level: 'N5',
    promptJa: 'わたし＿がくせいです。',
    promptTokens: [{ b: 'わたし' }, { b: '＿' }, { b: 'がくせいです。' }],
    choices: ['は', 'を', 'に', 'へ'],
    answerIndex: 0,
    skillTagKo: '조사',
  },
  {
    id: 'p2_vocab_water',
    level: 'N5',
    promptJa: 'のどが かわいた。「みず」を のみます。',
    promptTokens: [{ b: 'のどが かわいた。「' }, { b: 'みず' }, { b: '」を のみます。' }],
    choices: ['물', '불', '밥', '차'],
    answerIndex: 0,
    skillTagKo: '어휘',
  },
  {
    id: 'p3_kanji_ashita',
    level: 'N5',
    promptJa: '明日 えいがを 見ます。「明日」の よみは？',
    promptTokens: [{ b: '明日', r: 'あした' }, { b: ' えいがを ' }, { b: '見', r: 'み' }, { b: 'ます。' }],
    choices: ['あした', 'きのう', 'きょう', 'ゆうべ'],
    answerIndex: 0,
    skillTagKo: '한자읽기',
  },
  {
    id: 'p4_verb_te_form',
    level: 'N4',
    promptJa: 'まどを ＿ ください。（あける）',
    promptTokens: [{ b: 'まどを ＿ ください。（' }, { b: 'あける' }, { b: '）' }],
    choices: ['あけて', 'あけた', 'あけない', 'あける'],
    answerIndex: 0,
    skillTagKo: '동사활용',
  },
  {
    id: 'p5_particle_de',
    level: 'N4',
    promptJa: 'バス＿ かいしゃへ いきます。',
    promptTokens: [{ b: 'バス＿ ' }, { b: 'かいしゃへ いきます。' }],
    choices: ['で', 'に', 'が', 'を'],
    answerIndex: 0,
    skillTagKo: '조사',
  },
  {
    id: 'p6_potential_form',
    level: 'N4',
    promptJa: 'わたしは にほんごが すこし ＿。（はなす）',
    promptTokens: [{ b: 'わたしは にほんごが すこし ＿。（' }, { b: 'はなす' }, { b: '）' }],
    choices: ['はなせます', 'はなします', 'はなしたい', 'はなしました'],
    answerIndex: 0,
    skillTagKo: '동사활용',
  },
];

export const PLACEMENT_TOTAL = PLACEMENT_QUESTIONS.length;

// Score threshold: 4+ correct out of 6 recommends starting at N4.
export const PLACEMENT_N4_THRESHOLD = 4;
