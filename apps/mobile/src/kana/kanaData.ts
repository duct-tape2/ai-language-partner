// Full, accurate Hiragana and Katakana tables for the Kana Chart screen.
// Groups: 'gojuon' (basic 46), 'dakuten' (voiced + handakuten), 'yoon' (combos).
// Romaji uses Hepburn. No runtime network; all data is hand-authored here.

export type KanaType = 'hira' | 'kata';
export type KanaGroup = 'gojuon' | 'dakuten' | 'yoon';

export type KanaCell = {
  kana: string;
  romaji: string;
  type: KanaType;
  group: KanaGroup;
};

// Base rows shared by both scripts. Each entry: [hira, kata, romaji].
// null marks a gap in the classic 5x grid (e.g. yi/ye/wu do not exist).
type BaseRow = [string | null, string | null, string | null][];

const GOJUON: BaseRow = [
  ['あ', 'ア', 'a'], ['い', 'イ', 'i'], ['う', 'ウ', 'u'], ['え', 'エ', 'e'], ['お', 'オ', 'o'],
  ['か', 'カ', 'ka'], ['き', 'キ', 'ki'], ['く', 'ク', 'ku'], ['け', 'ケ', 'ke'], ['こ', 'コ', 'ko'],
  ['さ', 'サ', 'sa'], ['し', 'シ', 'shi'], ['す', 'ス', 'su'], ['せ', 'セ', 'se'], ['そ', 'ソ', 'so'],
  ['た', 'タ', 'ta'], ['ち', 'チ', 'chi'], ['つ', 'ツ', 'tsu'], ['て', 'テ', 'te'], ['と', 'ト', 'to'],
  ['な', 'ナ', 'na'], ['に', 'ニ', 'ni'], ['ぬ', 'ヌ', 'nu'], ['ね', 'ネ', 'ne'], ['の', 'ノ', 'no'],
  ['は', 'ハ', 'ha'], ['ひ', 'ヒ', 'hi'], ['ふ', 'フ', 'fu'], ['へ', 'ヘ', 'he'], ['ほ', 'ホ', 'ho'],
  ['ま', 'マ', 'ma'], ['み', 'ミ', 'mi'], ['む', 'ム', 'mu'], ['め', 'メ', 'me'], ['も', 'モ', 'mo'],
  ['や', 'ヤ', 'ya'], [null, null, null], ['ゆ', 'ユ', 'yu'], [null, null, null], ['よ', 'ヨ', 'yo'],
  ['ら', 'ラ', 'ra'], ['り', 'リ', 'ri'], ['る', 'ル', 'ru'], ['れ', 'レ', 're'], ['ろ', 'ロ', 'ro'],
  ['わ', 'ワ', 'wa'], [null, null, null], [null, null, null], [null, null, null], ['を', 'ヲ', 'wo'],
  ['ん', 'ン', 'n'], [null, null, null], [null, null, null], [null, null, null], [null, null, null],
];

const DAKUTEN: BaseRow = [
  ['が', 'ガ', 'ga'], ['ぎ', 'ギ', 'gi'], ['ぐ', 'グ', 'gu'], ['げ', 'ゲ', 'ge'], ['ご', 'ゴ', 'go'],
  ['ざ', 'ザ', 'za'], ['じ', 'ジ', 'ji'], ['ず', 'ズ', 'zu'], ['ぜ', 'ゼ', 'ze'], ['ぞ', 'ゾ', 'zo'],
  ['だ', 'ダ', 'da'], ['ぢ', 'ヂ', 'ji'], ['づ', 'ヅ', 'zu'], ['で', 'デ', 'de'], ['ど', 'ド', 'do'],
  ['ば', 'バ', 'ba'], ['び', 'ビ', 'bi'], ['ぶ', 'ブ', 'bu'], ['べ', 'ベ', 'be'], ['ぼ', 'ボ', 'bo'],
  ['ぱ', 'パ', 'pa'], ['ぴ', 'ピ', 'pi'], ['ぷ', 'プ', 'pu'], ['ぺ', 'ペ', 'pe'], ['ぽ', 'ポ', 'po'],
];

const YOON: BaseRow = [
  ['きゃ', 'キャ', 'kya'], ['きゅ', 'キュ', 'kyu'], ['きょ', 'キョ', 'kyo'],
  ['しゃ', 'シャ', 'sha'], ['しゅ', 'シュ', 'shu'], ['しょ', 'ショ', 'sho'],
  ['ちゃ', 'チャ', 'cha'], ['ちゅ', 'チュ', 'chu'], ['ちょ', 'チョ', 'cho'],
  ['にゃ', 'ニャ', 'nya'], ['にゅ', 'ニュ', 'nyu'], ['にょ', 'ニョ', 'nyo'],
  ['ひゃ', 'ヒャ', 'hya'], ['ひゅ', 'ヒュ', 'hyu'], ['ひょ', 'ヒョ', 'hyo'],
  ['みゃ', 'ミャ', 'mya'], ['みゅ', 'ミュ', 'myu'], ['みょ', 'ミョ', 'myo'],
  ['りゃ', 'リャ', 'rya'], ['りゅ', 'リュ', 'ryu'], ['りょ', 'リョ', 'ryo'],
  ['ぎゃ', 'ギャ', 'gya'], ['ぎゅ', 'ギュ', 'gyu'], ['ぎょ', 'ギョ', 'gyo'],
  ['じゃ', 'ジャ', 'ja'], ['じゅ', 'ジュ', 'ju'], ['じょ', 'ジョ', 'jo'],
  ['びゃ', 'ビャ', 'bya'], ['びゅ', 'ビュ', 'byu'], ['びょ', 'ビョ', 'byo'],
  ['ぴゃ', 'ピャ', 'pya'], ['ぴゅ', 'ピュ', 'pyu'], ['ぴょ', 'ピョ', 'pyo'],
];

function expand(rows: BaseRow, group: KanaGroup, type: KanaType): KanaCell[] {
  const idx = type === 'hira' ? 0 : 1;
  const out: KanaCell[] = [];
  for (const cell of rows) {
    const kana = cell[idx];
    const romaji = cell[2];
    if (kana == null || romaji == null) continue;
    out.push({ kana, romaji, type, group });
  }
  return out;
}

export const hiraganaGojuon = expand(GOJUON, 'gojuon', 'hira');
export const hiraganaDakuten = expand(DAKUTEN, 'dakuten', 'hira');
export const hiraganaYoon = expand(YOON, 'yoon', 'hira');

export const katakanaGojuon = expand(GOJUON, 'gojuon', 'kata');
export const katakanaDakuten = expand(DAKUTEN, 'dakuten', 'kata');
export const katakanaYoon = expand(YOON, 'yoon', 'kata');

export const allKana: KanaCell[] = [
  ...hiraganaGojuon,
  ...hiraganaDakuten,
  ...hiraganaYoon,
  ...katakanaGojuon,
  ...katakanaDakuten,
  ...katakanaYoon,
];

// Column count for the basic grid.
export const GRID_COLS = 5;

// Build a padded 5-wide layout for a given script's gojuon (keeps blanks aligned).
export function gojuonLayout(type: KanaType): (KanaCell | null)[] {
  const idx = type === 'hira' ? 0 : 1;
  return GOJUON.map((cell) => {
    const kana = cell[idx];
    const romaji = cell[2];
    if (kana == null || romaji == null) return null;
    return { kana, romaji, type, group: 'gojuon' } as KanaCell;
  });
}
