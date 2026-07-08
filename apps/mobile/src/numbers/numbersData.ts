// Numbers / time / date reference data for Korean learners of Japanese.
// Each entry carries the surface label, the kana reading, furigana tokens for
// the FuriganaTokens component ({ b: base, r?: reading }), and a Korean gloss.
// `irregular` marks readings that break the regular pattern (sound changes or
// wholly special forms) so the screen can highlight what to memorize.
//
// Hand-authored, offline. No runtime network. ASCII-safe source (Japanese/Korean
// live only inside string literals).

import type { FuriToken } from '../i18n';

export type ReadingEntry = {
  label: string; // surface form shown big, e.g. "4時"
  readingJa: string; // full kana reading, e.g. "よじ"
  tokens: FuriToken[]; // furigana tokens: kanji gets a reading, kana gets none
  ko: string; // Korean meaning / note
  irregular?: boolean; // true when the reading is a sound-change / special form
};

// ---------- 숫자 (cardinal numbers) ----------
export const NUMBERS: ReadingEntry[] = [
  { label: '0', readingJa: 'ゼロ / れい', tokens: [{ b: '0', r: 'ゼロ' }], ko: '영 (ゼロ 또는 れい)' },
  { label: '1', readingJa: 'いち', tokens: [{ b: '1', r: 'いち' }], ko: '일' },
  { label: '2', readingJa: 'に', tokens: [{ b: '2', r: 'に' }], ko: '이' },
  { label: '3', readingJa: 'さん', tokens: [{ b: '3', r: 'さん' }], ko: '삼' },
  { label: '4', readingJa: 'よん / し', tokens: [{ b: '4', r: 'よん' }], ko: '사 (보통 よん, し 도 씀)', irregular: true },
  { label: '5', readingJa: 'ご', tokens: [{ b: '5', r: 'ご' }], ko: '오' },
  { label: '6', readingJa: 'ろく', tokens: [{ b: '6', r: 'ろく' }], ko: '육' },
  { label: '7', readingJa: 'なな / しち', tokens: [{ b: '7', r: 'なな' }], ko: '칠 (보통 なな, しち 도 씀)', irregular: true },
  { label: '8', readingJa: 'はち', tokens: [{ b: '8', r: 'はち' }], ko: '팔' },
  { label: '9', readingJa: 'きゅう / く', tokens: [{ b: '9', r: 'きゅう' }], ko: '구 (보통 きゅう, く 도 씀)', irregular: true },
  { label: '10', readingJa: 'じゅう', tokens: [{ b: '10', r: 'じゅう' }], ko: '십' },
  { label: '100', readingJa: 'ひゃく', tokens: [{ b: '100', r: 'ひゃく' }], ko: '백' },
  { label: '300', readingJa: 'さんびゃく', tokens: [{ b: '300', r: 'さんびゃく' }], ko: '삼백 (음 변화: ひゃく to びゃく)', irregular: true },
  { label: '600', readingJa: 'ろっぴゃく', tokens: [{ b: '600', r: 'ろっぴゃく' }], ko: '육백 (음 변화: ろく to ろっ, ひゃく to ぴゃく)', irregular: true },
  { label: '800', readingJa: 'はっぴゃく', tokens: [{ b: '800', r: 'はっぴゃく' }], ko: '팔백 (음 변화: はち to はっ, ひゃく to ぴゃく)', irregular: true },
  { label: '1000', readingJa: 'せん', tokens: [{ b: '1000', r: 'せん' }], ko: '천' },
  { label: '3000', readingJa: 'さんぜん', tokens: [{ b: '3000', r: 'さんぜん' }], ko: '삼천 (음 변화: せん to ぜん)', irregular: true },
  { label: '8000', readingJa: 'はっせん', tokens: [{ b: '8000', r: 'はっせん' }], ko: '팔천 (음 변화: はち to はっ)', irregular: true },
  { label: '10000', readingJa: 'いちまん', tokens: [{ b: '10000', r: 'いちまん' }], ko: '만 (1만은 반드시 いちまん)', irregular: true },
];

// ---------- 시간 (time: hours and minutes) ----------
export const HOURS: ReadingEntry[] = [
  { label: '1時', readingJa: 'いちじ', tokens: [{ b: '1', r: 'いち' }, { b: '時', r: 'じ' }], ko: '1시' },
  { label: '2時', readingJa: 'にじ', tokens: [{ b: '2', r: 'に' }, { b: '時', r: 'じ' }], ko: '2시' },
  { label: '3時', readingJa: 'さんじ', tokens: [{ b: '3', r: 'さん' }, { b: '時', r: 'じ' }], ko: '3시' },
  { label: '4時', readingJa: 'よじ', tokens: [{ b: '4', r: 'よ' }, { b: '時', r: 'じ' }], ko: '4시 (よん 아님, よじ)', irregular: true },
  { label: '5時', readingJa: 'ごじ', tokens: [{ b: '5', r: 'ご' }, { b: '時', r: 'じ' }], ko: '5시' },
  { label: '6時', readingJa: 'ろくじ', tokens: [{ b: '6', r: 'ろく' }, { b: '時', r: 'じ' }], ko: '6시' },
  { label: '7時', readingJa: 'しちじ', tokens: [{ b: '7', r: 'しち' }, { b: '時', r: 'じ' }], ko: '7시 (なな 아님, しちじ)', irregular: true },
  { label: '8時', readingJa: 'はちじ', tokens: [{ b: '8', r: 'はち' }, { b: '時', r: 'じ' }], ko: '8시' },
  { label: '9時', readingJa: 'くじ', tokens: [{ b: '9', r: 'く' }, { b: '時', r: 'じ' }], ko: '9시 (きゅう 아님, くじ)', irregular: true },
  { label: '10時', readingJa: 'じゅうじ', tokens: [{ b: '10', r: 'じゅう' }, { b: '時', r: 'じ' }], ko: '10시' },
  { label: '11時', readingJa: 'じゅういちじ', tokens: [{ b: '11', r: 'じゅういち' }, { b: '時', r: 'じ' }], ko: '11시' },
  { label: '12時', readingJa: 'じゅうにじ', tokens: [{ b: '12', r: 'じゅうに' }, { b: '時', r: 'じ' }], ko: '12시' },
  { label: '何時', readingJa: 'なんじ', tokens: [{ b: '何', r: 'なん' }, { b: '時', r: 'じ' }], ko: '몇 시', irregular: true },
];

export const MINUTES: ReadingEntry[] = [
  { label: '1分', readingJa: 'いっぷん', tokens: [{ b: '1', r: 'いっ' }, { b: '分', r: 'ぷん' }], ko: '1분 (음 변화: いち to いっ, ふん to ぷん)', irregular: true },
  { label: '2分', readingJa: 'にふん', tokens: [{ b: '2', r: 'に' }, { b: '分', r: 'ふん' }], ko: '2분' },
  { label: '3分', readingJa: 'さんぷん', tokens: [{ b: '3', r: 'さん' }, { b: '分', r: 'ぷん' }], ko: '3분 (음 변화: ふん to ぷん)', irregular: true },
  { label: '4分', readingJa: 'よんぷん', tokens: [{ b: '4', r: 'よん' }, { b: '分', r: 'ぷん' }], ko: '4분 (음 변화: ふん to ぷん)', irregular: true },
  { label: '5分', readingJa: 'ごふん', tokens: [{ b: '5', r: 'ご' }, { b: '分', r: 'ふん' }], ko: '5분' },
  { label: '6分', readingJa: 'ろっぷん', tokens: [{ b: '6', r: 'ろっ' }, { b: '分', r: 'ぷん' }], ko: '6분 (음 변화: ろく to ろっ, ふん to ぷん)', irregular: true },
  { label: '7分', readingJa: 'ななふん', tokens: [{ b: '7', r: 'なな' }, { b: '分', r: 'ふん' }], ko: '7분 (しちふん 도 가능하나 보통 ななふん)' },
  { label: '8分', readingJa: 'はっぷん', tokens: [{ b: '8', r: 'はっ' }, { b: '分', r: 'ぷん' }], ko: '8분 (음 변화: はち to はっ, ふん to ぷん)', irregular: true },
  { label: '9分', readingJa: 'きゅうふん', tokens: [{ b: '9', r: 'きゅう' }, { b: '分', r: 'ふん' }], ko: '9분' },
  { label: '10分', readingJa: 'じゅっぷん', tokens: [{ b: '10', r: 'じゅっ' }, { b: '分', r: 'ぷん' }], ko: '10분 (じっぷん 도 가능, 음 변화: ふん to ぷん)', irregular: true },
  { label: '15分', readingJa: 'じゅうごふん', tokens: [{ b: '15', r: 'じゅうご' }, { b: '分', r: 'ふん' }], ko: '15분' },
  { label: '30分', readingJa: 'さんじゅっぷん', tokens: [{ b: '30', r: 'さんじゅっ' }, { b: '分', r: 'ぷん' }], ko: '30분 (= 半 はん, 음 변화: ふん to ぷん)', irregular: true },
  { label: '半', readingJa: 'はん', tokens: [{ b: '半', r: 'はん' }], ko: '반 (30분)' },
  { label: '何分', readingJa: 'なんぷん', tokens: [{ b: '何', r: 'なん' }, { b: '分', r: 'ぷん' }], ko: '몇 분 (음 변화: ふん to ぷん)', irregular: true },
];

// ---------- 날짜 (days of the month) ----------
// 1-10 and 14/20/24 use native (wago) readings; the rest are on-yomi + にち.
export const DAYS: ReadingEntry[] = [
  { label: '1日', readingJa: 'ついたち', tokens: [{ b: '1日', r: 'ついたち' }], ko: '1일 (초하루, 특수 읽기)', irregular: true },
  { label: '2日', readingJa: 'ふつか', tokens: [{ b: '2日', r: 'ふつか' }], ko: '2일 (고유 읽기)', irregular: true },
  { label: '3日', readingJa: 'みっか', tokens: [{ b: '3日', r: 'みっか' }], ko: '3일 (고유 읽기)', irregular: true },
  { label: '4日', readingJa: 'よっか', tokens: [{ b: '4日', r: 'よっか' }], ko: '4일 (고유 읽기)', irregular: true },
  { label: '5日', readingJa: 'いつか', tokens: [{ b: '5日', r: 'いつか' }], ko: '5일 (고유 읽기)', irregular: true },
  { label: '6日', readingJa: 'むいか', tokens: [{ b: '6日', r: 'むいか' }], ko: '6일 (고유 읽기)', irregular: true },
  { label: '7日', readingJa: 'なのか', tokens: [{ b: '7日', r: 'なのか' }], ko: '7일 (고유 읽기)', irregular: true },
  { label: '8日', readingJa: 'ようか', tokens: [{ b: '8日', r: 'ようか' }], ko: '8일 (고유 읽기, 4일 よっか 와 혼동 주의)', irregular: true },
  { label: '9日', readingJa: 'ここのか', tokens: [{ b: '9日', r: 'ここのか' }], ko: '9일 (고유 읽기)', irregular: true },
  { label: '10日', readingJa: 'とおか', tokens: [{ b: '10日', r: 'とおか' }], ko: '10일 (고유 읽기)', irregular: true },
  { label: '11日', readingJa: 'じゅういちにち', tokens: [{ b: '11', r: 'じゅういち' }, { b: '日', r: 'にち' }], ko: '11일 (규칙형: 숫자 + にち)' },
  { label: '12日', readingJa: 'じゅうににち', tokens: [{ b: '12', r: 'じゅうに' }, { b: '日', r: 'にち' }], ko: '12일' },
  { label: '13日', readingJa: 'じゅうさんにち', tokens: [{ b: '13', r: 'じゅうさん' }, { b: '日', r: 'にち' }], ko: '13일' },
  { label: '14日', readingJa: 'じゅうよっか', tokens: [{ b: '14日', r: 'じゅうよっか' }], ko: '14일 (よっか 로 끝나는 예외)', irregular: true },
  { label: '15日', readingJa: 'じゅうごにち', tokens: [{ b: '15', r: 'じゅうご' }, { b: '日', r: 'にち' }], ko: '15일' },
  { label: '16日', readingJa: 'じゅうろくにち', tokens: [{ b: '16', r: 'じゅうろく' }, { b: '日', r: 'にち' }], ko: '16일' },
  { label: '17日', readingJa: 'じゅうしちにち', tokens: [{ b: '17', r: 'じゅうしち' }, { b: '日', r: 'にち' }], ko: '17일 (しち 로 읽음)' },
  { label: '18日', readingJa: 'じゅうはちにち', tokens: [{ b: '18', r: 'じゅうはち' }, { b: '日', r: 'にち' }], ko: '18일' },
  { label: '19日', readingJa: 'じゅうくにち', tokens: [{ b: '19', r: 'じゅうく' }, { b: '日', r: 'にち' }], ko: '19일 (く 로 읽음, きゅう 아님)', irregular: true },
  { label: '20日', readingJa: 'はつか', tokens: [{ b: '20日', r: 'はつか' }], ko: '20일 (특수 읽기)', irregular: true },
  { label: '24日', readingJa: 'にじゅうよっか', tokens: [{ b: '24日', r: 'にじゅうよっか' }], ko: '24일 (よっか 로 끝나는 예외)', irregular: true },
  { label: '何日', readingJa: 'なんにち', tokens: [{ b: '何', r: 'なん' }, { b: '日', r: 'にち' }], ko: '며칠', irregular: true },
];

// ---------- 요일 (weekdays) ----------
export const WEEKDAYS: ReadingEntry[] = [
  { label: '月曜日', readingJa: 'げつようび', tokens: [{ b: '月', r: 'げつ' }, { b: '曜', r: 'よう' }, { b: '日', r: 'び' }], ko: '월요일' },
  { label: '火曜日', readingJa: 'かようび', tokens: [{ b: '火', r: 'か' }, { b: '曜', r: 'よう' }, { b: '日', r: 'び' }], ko: '화요일' },
  { label: '水曜日', readingJa: 'すいようび', tokens: [{ b: '水', r: 'すい' }, { b: '曜', r: 'よう' }, { b: '日', r: 'び' }], ko: '수요일' },
  { label: '木曜日', readingJa: 'もくようび', tokens: [{ b: '木', r: 'もく' }, { b: '曜', r: 'よう' }, { b: '日', r: 'び' }], ko: '목요일' },
  { label: '金曜日', readingJa: 'きんようび', tokens: [{ b: '金', r: 'きん' }, { b: '曜', r: 'よう' }, { b: '日', r: 'び' }], ko: '금요일' },
  { label: '土曜日', readingJa: 'どようび', tokens: [{ b: '土', r: 'ど' }, { b: '曜', r: 'よう' }, { b: '日', r: 'び' }], ko: '토요일' },
  { label: '日曜日', readingJa: 'にちようび', tokens: [{ b: '日', r: 'にち' }, { b: '曜', r: 'よう' }, { b: '日', r: 'び' }], ko: '일요일' },
  { label: '何曜日', readingJa: 'なんようび', tokens: [{ b: '何', r: 'なん' }, { b: '曜', r: 'よう' }, { b: '日', r: 'び' }], ko: '무슨 요일', irregular: true },
];

export type NumbersTab = 'numbers' | 'time' | 'date' | 'weekday';
