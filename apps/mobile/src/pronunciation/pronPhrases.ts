// Pronunciation-practice target phrases (발음 피드백). Everyday N5/N4 sentences a
// Korean learner actually needs to say out loud. Each phrase carries furigana
// tokens for kanji readings and a Korean gloss. Hand-authored, no runtime
// network. ASCII-safe source.

export type PronToken = { b: string; r?: string };

export type PronPhrase = {
  id: string;
  ja: string;
  tokens: PronToken[];
  ko: string;
  level: 'N5' | 'N4';
};

export const PRON_PHRASES: PronPhrase[] = [
  {
    id: 'greet_morning',
    ja: 'おはようございます。',
    tokens: [{ b: 'おはようございます。' }],
    ko: '안녕하세요 (아침 인사).',
    level: 'N5',
  },
  {
    id: 'nice_to_meet',
    ja: 'はじめまして。よろしくお願いします。',
    tokens: [
      { b: 'はじめまして。よろしくお' },
      { b: '願', r: 'ねが' },
      { b: 'いします。' },
    ],
    ko: '처음 뵙겠습니다. 잘 부탁드립니다.',
    level: 'N5',
  },
  {
    id: 'thanks_help',
    ja: '手伝ってくれてありがとう。',
    tokens: [
      { b: '手伝', r: 'てつだ' },
      { b: 'ってくれてありがとう。' },
    ],
    ko: '도와줘서 고마워.',
    level: 'N4',
  },
  {
    id: 'sorry_late',
    ja: '遅れてすみません。',
    tokens: [
      { b: '遅', r: 'おく' },
      { b: 'れてすみません。' },
    ],
    ko: '늦어서 죄송합니다.',
    level: 'N5',
  },
  {
    id: 'where_station',
    ja: '駅はどこですか。',
    tokens: [
      { b: '駅', r: 'えき' },
      { b: 'はどこですか。' },
    ],
    ko: '역은 어디예요?',
    level: 'N5',
  },
  {
    id: 'how_much',
    ja: 'これはいくらですか。',
    tokens: [{ b: 'これはいくらですか。' }],
    ko: '이거 얼마예요?',
    level: 'N5',
  },
  {
    id: 'coffee_order',
    ja: 'コーヒーを一つください。',
    tokens: [
      { b: 'コーヒーを' },
      { b: '一', r: 'ひと' },
      { b: 'つください。' },
    ],
    ko: '커피 하나 주세요.',
    level: 'N5',
  },
  {
    id: 'menu_please',
    ja: 'メニューを見せてください。',
    tokens: [
      { b: 'メニューを' },
      { b: '見', r: 'み' },
      { b: 'せてください。' },
    ],
    ko: '메뉴 보여주세요.',
    level: 'N5',
  },
  {
    id: 'check_please',
    ja: 'お会計をお願いします。',
    tokens: [
      { b: 'お' },
      { b: '会計', r: 'かいけい' },
      { b: 'をお' },
      { b: '願', r: 'ねが' },
      { b: 'いします。' },
    ],
    ko: '계산 부탁드립니다.',
    level: 'N4',
  },
  {
    id: 'weather_today',
    ja: '今日はいい天気ですね。',
    tokens: [
      { b: '今日', r: 'きょう' },
      { b: 'はいい' },
      { b: '天気', r: 'てんき' },
      { b: 'ですね。' },
    ],
    ko: '오늘 날씨 좋네요.',
    level: 'N5',
  },
  {
    id: 'tired_today',
    ja: '今日はとても疲れました。',
    tokens: [
      { b: '今日', r: 'きょう' },
      { b: 'はとても' },
      { b: '疲', r: 'つか' },
      { b: 'れました。' },
    ],
    ko: '오늘 너무 피곤했어요.',
    level: 'N4',
  },
  {
    id: 'what_time',
    ja: '今何時ですか。',
    tokens: [
      { b: '今', r: 'いま' },
      { b: '何時', r: 'なんじ' },
      { b: 'ですか。' },
    ],
    ko: '지금 몇 시예요?',
    level: 'N5',
  },
  {
    id: 'meet_tomorrow',
    ja: 'また明日会いましょう。',
    tokens: [
      { b: 'また' },
      { b: '明日', r: 'あした' },
      { b: '会', r: 'あ' },
      { b: 'いましょう。' },
    ],
    ko: '내일 또 만나요.',
    level: 'N4',
  },
  {
    id: 'call_later',
    ja: 'あとで電話します。',
    tokens: [
      { b: 'あとで' },
      { b: '電話', r: 'でんわ' },
      { b: 'します。' },
    ],
    ko: '나중에 전화할게요.',
    level: 'N4',
  },
  {
    id: 'once_more',
    ja: 'もう一度言ってください。',
    tokens: [
      { b: 'もう' },
      { b: '一度', r: 'いちど' },
      { b: '言', r: 'い' },
      { b: 'ってください。' },
    ],
    ko: '다시 한 번 말해 주세요.',
    level: 'N4',
  },
  {
    id: 'slow_please',
    ja: 'ゆっくり話してください。',
    tokens: [
      { b: 'ゆっくり' },
      { b: '話', r: 'はな' },
      { b: 'してください。' },
    ],
    ko: '천천히 말해 주세요.',
    level: 'N4',
  },
  {
    id: 'dont_understand',
    ja: 'すみません、よく分かりません。',
    tokens: [
      { b: 'すみません、よく' },
      { b: '分', r: 'わ' },
      { b: 'かりません。' },
    ],
    ko: '죄송해요, 잘 모르겠어요.',
    level: 'N4',
  },
  {
    id: 'ok_fine',
    ja: '大丈夫です。',
    tokens: [
      { b: '大丈夫', r: 'だいじょうぶ' },
      { b: 'です。' },
    ],
    ko: '괜찮아요.',
    level: 'N5',
  },
  {
    id: 'lets_eat',
    ja: '一緒にご飯を食べましょう。',
    tokens: [
      { b: '一緒', r: 'いっしょ' },
      { b: 'に' },
      { b: 'ご飯', r: 'ごはん' },
      { b: 'を' },
      { b: '食', r: 'た' },
      { b: 'べましょう。' },
    ],
    ko: '같이 밥 먹어요.',
    level: 'N4',
  },
  {
    id: 'delicious',
    ja: 'この料理はおいしいです。',
    tokens: [
      { b: 'この' },
      { b: '料理', r: 'りょうり' },
      { b: 'はおいしいです。' },
    ],
    ko: '이 요리 맛있어요.',
    level: 'N5',
  },
  {
    id: 'go_home',
    ja: 'そろそろ家に帰ります。',
    tokens: [
      { b: 'そろそろ' },
      { b: '家', r: 'いえ' },
      { b: 'に' },
      { b: '帰', r: 'かえ' },
      { b: 'ります。' },
    ],
    ko: '슬슬 집에 갈게요.',
    level: 'N4',
  },
  {
    id: 'have_a_question',
    ja: 'ちょっと質問があります。',
    tokens: [
      { b: 'ちょっと' },
      { b: '質問', r: 'しつもん' },
      { b: 'があります。' },
    ],
    ko: '질문이 좀 있어요.',
    level: 'N4',
  },
  {
    id: 'busy_now',
    ja: '今ちょっと忙しいです。',
    tokens: [
      { b: '今', r: 'いま' },
      { b: 'ちょっと' },
      { b: '忙', r: 'いそが' },
      { b: 'しいです。' },
    ],
    ko: '지금 좀 바빠요.',
    level: 'N4',
  },
  {
    id: 'take_care',
    ja: '気をつけて帰ってね。',
    tokens: [
      { b: '気', r: 'き' },
      { b: 'をつけて' },
      { b: '帰', r: 'かえ' },
      { b: 'ってね。' },
    ],
    ko: '조심히 들어가.',
    level: 'N4',
  },
];

export const PRON_PHRASE_TOTAL = PRON_PHRASES.length;
