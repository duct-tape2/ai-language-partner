// Today's speaking set for the daily-life room. A short, coherent sequence of
// casual friend-register sentences so the core loop has a clear "다음 문장 → 완료"
// progression instead of a single dead-end phrase. Furigana readings for each
// sentence are hand-authored in i18n.ts (FURIGANA map) and translations here.
// Keep them in sync: every ja string below MUST have a FURIGANA entry, else the
// kanji render unreadable (getFurigana warns in __DEV__). Kept consistent in politeness
// (casual, 반말 친구체) so the persona coaching tone matches.
export type PracticePhrase = { ja: string; ko: string };

export const PRACTICE_SEQUENCE: PracticePhrase[] = [
  { ja: '今日めっちゃ疲れた。', ko: '오늘 너무 피곤했어.' },
  { ja: 'ちょっと休もうかな。', ko: '좀 쉬어야겠다.' },
  { ja: 'お腹すいた、何か食べよう。', ko: '배고파, 뭐 좀 먹자.' },
  { ja: '明日も頑張ろうね。', ko: '내일도 같이 힘내자.' },
  { ja: '今日はもう寝るね。', ko: '오늘은 이제 잘게.' },
];

export const PRACTICE_TOTAL = PRACTICE_SEQUENCE.length;
