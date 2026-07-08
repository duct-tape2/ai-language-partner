// Words (단어) recall content. Shows the Korean meaning + context; the learner
// recalls the Japanese word, then reveals + self-grades. Reinforces the exact
// vocabulary used in the speak/listen/story loops (same daily-life set).
// Mirrors Codex's word_review item ({ id, ko, ja, example, contextNote });
// self-grade maps to Codex's answer_word_review accepted/again.
export type WordItem = {
  id: string;
  ko: string; // meaning (prompt)
  ja: string; // target word
  reading: string;
  example: string;
  exampleKo: string;
  xpReward: number;
};

export const WORD_ITEMS: WordItem[] = [
  { id: 'word_tsukareta', ko: '피곤하다', ja: '疲れた', reading: 'つかれた', example: '今日めっちゃ疲れた。', exampleKo: '오늘 너무 피곤했어.', xpReward: 10 },
  { id: 'word_yasumu', ko: '쉬다', ja: '休む', reading: 'やすむ', example: 'ちょっと休もうかな。', exampleKo: '좀 쉬어야겠다.', xpReward: 10 },
  { id: 'word_onaka', ko: '배고프다', ja: 'お腹すいた', reading: 'おなかすいた', example: 'お腹すいた、何か食べよう。', exampleKo: '배고파, 뭐 좀 먹자.', xpReward: 10 },
  { id: 'word_ganbaru', ko: '힘내다 / 노력하다', ja: '頑張る', reading: 'がんばる', example: '明日も頑張ろうね。', exampleKo: '내일도 힘내자.', xpReward: 10 },
  { id: 'word_neru', ko: '자다', ja: '寝る', reading: 'ねる', example: '今日はもう寝るね。', exampleKo: '오늘은 이제 잘게.', xpReward: 10 },
];

export const WORD_TOTAL = WORD_ITEMS.length;
