// Tokyo-dialect (標準語) pitch-accent training data. Hand-authored, no network.
//
// Pattern taxonomy (by where the accent nucleus / drop falls):
//   heiban    平板  no drop. Mora 1 low, then all high (a following particle stays
//                   high too). accentPosition = 0.
//   atamadaka 頭高  drop after mora 1. Mora 1 high, rest low. accentPosition = 1.
//   nakadaka  中高  drop in the middle (not after mora 1, not the last mora).
//                   Low start, rise, then drop before the end.
//                   accentPosition = the last HIGH mora, in 2..(moraCount-1).
//   odaka     尾高  accent on the LAST mora: the word is low-start-then-high, but a
//                   following particle drops. accentPosition = moraCount.
//
// `accentPosition` follows the standard accent-number convention:
//   0 = heiban, 1 = atamadaka, k = drop after mora k (odaka when k === moraCount).
// Invariant kept for every entry: the number of mora in `reading` matches the mora
// grid the screen draws, and `pattern` agrees with `accentPosition`.
//
// Several classic minimal pairs are included on purpose so learners hear the
// contrast (箸 atamadaka / 橋 odaka / 端 heiban; 雨 atamadaka / 飴 heiban).

export type PitchPattern = 'heiban' | 'atamadaka' | 'nakadaka' | 'odaka';

export type PitchWord = {
  wordJa: string;
  tokens: { b: string; r?: string }[];
  reading: string; // full kana; each mora is one grid step (small kana combine)
  pattern: PitchPattern;
  accentPosition: number; // standard accent number (0 = heiban)
  meaningKo: string;
};

export const PITCH_WORDS: PitchWord[] = [
  // ---- classic hashi minimal set (2 mora) ----
  { wordJa: '箸', tokens: [{ b: '箸', r: 'はし' }], reading: 'はし', pattern: 'atamadaka', accentPosition: 1, meaningKo: '젓가락' },
  { wordJa: '橋', tokens: [{ b: '橋', r: 'はし' }], reading: 'はし', pattern: 'odaka', accentPosition: 2, meaningKo: '다리 (교량)' },
  { wordJa: '端', tokens: [{ b: '端', r: 'はし' }], reading: 'はし', pattern: 'heiban', accentPosition: 0, meaningKo: '끝, 가장자리' },

  // ---- ame minimal pair (2 mora) ----
  { wordJa: '雨', tokens: [{ b: '雨', r: 'あめ' }], reading: 'あめ', pattern: 'atamadaka', accentPosition: 1, meaningKo: '비' },
  { wordJa: '飴', tokens: [{ b: '飴', r: 'あめ' }], reading: 'あめ', pattern: 'heiban', accentPosition: 0, meaningKo: '사탕' },

  // ---- heiban 平板 ----
  { wordJa: '桜', tokens: [{ b: '桜', r: 'さくら' }], reading: 'さくら', pattern: 'heiban', accentPosition: 0, meaningKo: '벚꽃' },
  { wordJa: '友達', tokens: [{ b: '友達', r: 'ともだち' }], reading: 'ともだち', pattern: 'heiban', accentPosition: 0, meaningKo: '친구' },
  { wordJa: '学生', tokens: [{ b: '学生', r: 'がくせい' }], reading: 'がくせい', pattern: 'heiban', accentPosition: 0, meaningKo: '학생' },
  { wordJa: '会社', tokens: [{ b: '会社', r: 'かいしゃ' }], reading: 'かいしゃ', pattern: 'heiban', accentPosition: 0, meaningKo: '회사' },
  { wordJa: '時間', tokens: [{ b: '時間', r: 'じかん' }], reading: 'じかん', pattern: 'heiban', accentPosition: 0, meaningKo: '시간' },
  { wordJa: '電車', tokens: [{ b: '電車', r: 'でんしゃ' }], reading: 'でんしゃ', pattern: 'heiban', accentPosition: 0, meaningKo: '전철' },
  { wordJa: '魚', tokens: [{ b: '魚', r: 'さかな' }], reading: 'さかな', pattern: 'heiban', accentPosition: 0, meaningKo: '생선, 물고기' },
  { wordJa: '犬', tokens: [{ b: '犬', r: 'いぬ' }], reading: 'いぬ', pattern: 'heiban', accentPosition: 0, meaningKo: '개' },
  { wordJa: '大学', tokens: [{ b: '大学', r: 'だいがく' }], reading: 'だいがく', pattern: 'heiban', accentPosition: 0, meaningKo: '대학' },

  // ---- atamadaka 頭高 ----
  { wordJa: '猫', tokens: [{ b: '猫', r: 'ねこ' }], reading: 'ねこ', pattern: 'atamadaka', accentPosition: 1, meaningKo: '고양이' },
  { wordJa: '本', tokens: [{ b: '本', r: 'ほん' }], reading: 'ほん', pattern: 'atamadaka', accentPosition: 1, meaningKo: '책' },
  { wordJa: '春', tokens: [{ b: '春', r: 'はる' }], reading: 'はる', pattern: 'atamadaka', accentPosition: 1, meaningKo: '봄' },
  { wordJa: '今', tokens: [{ b: '今', r: 'いま' }], reading: 'いま', pattern: 'atamadaka', accentPosition: 1, meaningKo: '지금' },
  { wordJa: '朝', tokens: [{ b: '朝', r: 'あさ' }], reading: 'あさ', pattern: 'atamadaka', accentPosition: 1, meaningKo: '아침' },
  { wordJa: '元気', tokens: [{ b: '元気', r: 'げんき' }], reading: 'げんき', pattern: 'atamadaka', accentPosition: 1, meaningKo: '건강함, 기운' },
  { wordJa: '天気', tokens: [{ b: '天気', r: 'てんき' }], reading: 'てんき', pattern: 'atamadaka', accentPosition: 1, meaningKo: '날씨' },
  { wordJa: '電気', tokens: [{ b: '電気', r: 'でんき' }], reading: 'でんき', pattern: 'atamadaka', accentPosition: 1, meaningKo: '전기, 전등' },
  { wordJa: '兄弟', tokens: [{ b: '兄弟', r: 'きょうだい' }], reading: 'きょうだい', pattern: 'atamadaka', accentPosition: 1, meaningKo: '형제' },
  { wordJa: '毎日', tokens: [{ b: '毎日', r: 'まいにち' }], reading: 'まいにち', pattern: 'atamadaka', accentPosition: 1, meaningKo: '매일' },

  // ---- nakadaka 中高 ----
  { wordJa: '日本', tokens: [{ b: '日本', r: 'にほん' }], reading: 'にほん', pattern: 'nakadaka', accentPosition: 2, meaningKo: '일본' },
  { wordJa: '先生', tokens: [{ b: '先生', r: 'せんせい' }], reading: 'せんせい', pattern: 'nakadaka', accentPosition: 3, meaningKo: '선생님' },
  { wordJa: '飛行機', tokens: [{ b: '飛行機', r: 'ひこうき' }], reading: 'ひこうき', pattern: 'nakadaka', accentPosition: 2, meaningKo: '비행기' },
  { wordJa: '音楽', tokens: [{ b: '音楽', r: 'おんがく' }], reading: 'おんがく', pattern: 'atamadaka', accentPosition: 1, meaningKo: '음악' },
  { wordJa: '果物', tokens: [{ b: '果物', r: 'くだもの' }], reading: 'くだもの', pattern: 'nakadaka', accentPosition: 2, meaningKo: '과일' },
  { wordJa: '玉子', tokens: [{ b: '玉子', r: 'たまご' }], reading: 'たまご', pattern: 'nakadaka', accentPosition: 2, meaningKo: '계란' },
  { wordJa: '心', tokens: [{ b: '心', r: 'こころ' }], reading: 'こころ', pattern: 'nakadaka', accentPosition: 2, meaningKo: '마음' },
  { wordJa: '大人', tokens: [{ b: '大人', r: 'おとな' }], reading: 'おとな', pattern: 'heiban', accentPosition: 0, meaningKo: '어른' },

  // ---- odaka 尾高 (accent on last mora; particle drops) ----
  { wordJa: '花', tokens: [{ b: '花', r: 'はな' }], reading: 'はな', pattern: 'odaka', accentPosition: 2, meaningKo: '꽃' },
  { wordJa: '山', tokens: [{ b: '山', r: 'やま' }], reading: 'やま', pattern: 'odaka', accentPosition: 2, meaningKo: '산' },
  { wordJa: '川', tokens: [{ b: '川', r: 'かわ' }], reading: 'かわ', pattern: 'odaka', accentPosition: 2, meaningKo: '강' },
  { wordJa: '男', tokens: [{ b: '男', r: 'おとこ' }], reading: 'おとこ', pattern: 'odaka', accentPosition: 3, meaningKo: '남자' },
  { wordJa: '女', tokens: [{ b: '女', r: 'おんな' }], reading: 'おんな', pattern: 'odaka', accentPosition: 3, meaningKo: '여자' },
  { wordJa: '弟', tokens: [{ b: '弟', r: 'おとうと' }], reading: 'おとうと', pattern: 'odaka', accentPosition: 4, meaningKo: '남동생' },
  { wordJa: '妹', tokens: [{ b: '妹', r: 'いもうと' }], reading: 'いもうと', pattern: 'odaka', accentPosition: 4, meaningKo: '여동생' },
];

export const PITCH_WORD_TOTAL = PITCH_WORDS.length;
