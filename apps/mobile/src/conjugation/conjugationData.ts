// Hand-authored JLPT N5/N4 conjugation bank for the 동사 형용사 활용 드릴 screen.
// Static data only, no network. Furigana tokens mirror the FuriToken shape used by
// <FuriganaTokens>: kanji chunks carry an `r` reading, kana chunks omit it.
//
// Conjugations are authored by hand and checked against standard rules:
//  - godan (5-dan / u-verbs): stem changes by the vowel row (u -> i for masu, etc.)
//  - ichidan (1-dan / ru-verbs): drop る, add ます / て / ない / た / られる
//  - irregular: する, くる (and 来る) only
//  - i-adj: past = 〜かった, negative = 〜くない, te = 〜くて
//  - na-adj: past = 〜だった, negative = 〜じゃない, te = 〜で
//
// The `forms` map holds the RESULT of each conjugation used by the drill. The
// `tokens` on each form are separate so furigana still renders on the answer.

export type FuriTok = { b: string; r?: string };

export type WordType = 'godan' | 'ichidan' | 'irregular' | 'i-adj' | 'na-adj';

// A conjugated form: display string, furigana tokens, and Korean gloss of the form name.
export type ConjForm = { ja: string; tokens: FuriTok[] };

export type FormKey = 'masu' | 'te' | 'nai' | 'ta' | 'potential';

export type ConjWord = {
  id: string;
  word: string; // dictionary (plain) form
  tokens: FuriTok[]; // dictionary form furigana
  type: WordType;
  meaningKo: string;
  forms: {
    masu: ConjForm; // 정중형 (ます형)
    te: ConjForm; // て형
    nai: ConjForm; // 부정형 (ない형)
    ta: ConjForm; // 과거형 (た형)
    potential?: ConjForm; // 가능형 (adjectives omit this)
  };
};

// Form metadata: the drill asks for one of these; browse mode explains each.
export type FormMeta = { key: FormKey; label: string; descKo: string };

export const FORM_META: FormMeta[] = [
  { key: 'masu', label: 'ます형 (정중형)', descKo: '정중하게 말할 때 쓰는 형태. "~합니다".' },
  { key: 'te', label: 'て형 (연결형)', descKo: '동작을 잇거나 요청, 진행형을 만들 때 쓰는 형태.' },
  { key: 'nai', label: 'ない형 (부정형)', descKo: '반말 부정. "~하지 않는다".' },
  { key: 'ta', label: 'た형 (과거형)', descKo: '반말 과거. "~했다".' },
  { key: 'potential', label: '가능형', descKo: '"~할 수 있다"는 뜻을 나타내는 형태.' },
];

export const FORM_LABEL: Record<FormKey, string> = {
  masu: 'ます형',
  te: 'て형',
  nai: 'ない형',
  ta: 'た형',
  potential: '가능형',
};

export const CONJUGATIONS: ConjWord[] = [
  // -------- godan (u-verbs) --------
  {
    id: 'kau',
    word: '買う',
    tokens: [{ b: '買', r: 'か' }, { b: 'う' }],
    type: 'godan',
    meaningKo: '사다',
    forms: {
      masu: { ja: '買います', tokens: [{ b: '買', r: 'か' }, { b: 'います' }] },
      te: { ja: '買って', tokens: [{ b: '買', r: 'か' }, { b: 'って' }] },
      nai: { ja: '買わない', tokens: [{ b: '買', r: 'か' }, { b: 'わない' }] },
      ta: { ja: '買った', tokens: [{ b: '買', r: 'か' }, { b: 'った' }] },
      potential: { ja: '買える', tokens: [{ b: '買', r: 'か' }, { b: 'える' }] },
    },
  },
  {
    id: 'iku',
    word: '行く',
    tokens: [{ b: '行', r: 'い' }, { b: 'く' }],
    type: 'godan',
    meaningKo: '가다',
    forms: {
      masu: { ja: '行きます', tokens: [{ b: '行', r: 'い' }, { b: 'きます' }] },
      // 行く is the classic te-form exception: 行って (not 行いて).
      te: { ja: '行って', tokens: [{ b: '行', r: 'い' }, { b: 'って' }] },
      nai: { ja: '行かない', tokens: [{ b: '行', r: 'い' }, { b: 'かない' }] },
      ta: { ja: '行った', tokens: [{ b: '行', r: 'い' }, { b: 'った' }] },
      potential: { ja: '行ける', tokens: [{ b: '行', r: 'い' }, { b: 'ける' }] },
    },
  },
  {
    id: 'hanasu',
    word: '話す',
    tokens: [{ b: '話', r: 'はな' }, { b: 'す' }],
    type: 'godan',
    meaningKo: '이야기하다',
    forms: {
      masu: { ja: '話します', tokens: [{ b: '話', r: 'はな' }, { b: 'します' }] },
      te: { ja: '話して', tokens: [{ b: '話', r: 'はな' }, { b: 'して' }] },
      nai: { ja: '話さない', tokens: [{ b: '話', r: 'はな' }, { b: 'さない' }] },
      ta: { ja: '話した', tokens: [{ b: '話', r: 'はな' }, { b: 'した' }] },
      potential: { ja: '話せる', tokens: [{ b: '話', r: 'はな' }, { b: 'せる' }] },
    },
  },
  {
    id: 'matsu',
    word: '待つ',
    tokens: [{ b: '待', r: 'ま' }, { b: 'つ' }],
    type: 'godan',
    meaningKo: '기다리다',
    forms: {
      masu: { ja: '待ちます', tokens: [{ b: '待', r: 'ま' }, { b: 'ちます' }] },
      te: { ja: '待って', tokens: [{ b: '待', r: 'ま' }, { b: 'って' }] },
      nai: { ja: '待たない', tokens: [{ b: '待', r: 'ま' }, { b: 'たない' }] },
      ta: { ja: '待った', tokens: [{ b: '待', r: 'ま' }, { b: 'った' }] },
      potential: { ja: '待てる', tokens: [{ b: '待', r: 'ま' }, { b: 'てる' }] },
    },
  },
  {
    id: 'nomu',
    word: '飲む',
    tokens: [{ b: '飲', r: 'の' }, { b: 'む' }],
    type: 'godan',
    meaningKo: '마시다',
    forms: {
      masu: { ja: '飲みます', tokens: [{ b: '飲', r: 'の' }, { b: 'みます' }] },
      te: { ja: '飲んで', tokens: [{ b: '飲', r: 'の' }, { b: 'んで' }] },
      nai: { ja: '飲まない', tokens: [{ b: '飲', r: 'の' }, { b: 'まない' }] },
      ta: { ja: '飲んだ', tokens: [{ b: '飲', r: 'の' }, { b: 'んだ' }] },
      potential: { ja: '飲める', tokens: [{ b: '飲', r: 'の' }, { b: 'める' }] },
    },
  },
  {
    id: 'yomu',
    word: '読む',
    tokens: [{ b: '読', r: 'よ' }, { b: 'む' }],
    type: 'godan',
    meaningKo: '읽다',
    forms: {
      masu: { ja: '読みます', tokens: [{ b: '読', r: 'よ' }, { b: 'みます' }] },
      te: { ja: '読んで', tokens: [{ b: '読', r: 'よ' }, { b: 'んで' }] },
      nai: { ja: '読まない', tokens: [{ b: '読', r: 'よ' }, { b: 'まない' }] },
      ta: { ja: '読んだ', tokens: [{ b: '読', r: 'よ' }, { b: 'んだ' }] },
      potential: { ja: '読める', tokens: [{ b: '読', r: 'よ' }, { b: 'める' }] },
    },
  },
  {
    id: 'asobu',
    word: '遊ぶ',
    tokens: [{ b: '遊', r: 'あそ' }, { b: 'ぶ' }],
    type: 'godan',
    meaningKo: '놀다',
    forms: {
      masu: { ja: '遊びます', tokens: [{ b: '遊', r: 'あそ' }, { b: 'びます' }] },
      te: { ja: '遊んで', tokens: [{ b: '遊', r: 'あそ' }, { b: 'んで' }] },
      nai: { ja: '遊ばない', tokens: [{ b: '遊', r: 'あそ' }, { b: 'ばない' }] },
      ta: { ja: '遊んだ', tokens: [{ b: '遊', r: 'あそ' }, { b: 'んだ' }] },
      potential: { ja: '遊べる', tokens: [{ b: '遊', r: 'あそ' }, { b: 'べる' }] },
    },
  },
  {
    id: 'kaku',
    word: '書く',
    tokens: [{ b: '書', r: 'か' }, { b: 'く' }],
    type: 'godan',
    meaningKo: '쓰다',
    forms: {
      masu: { ja: '書きます', tokens: [{ b: '書', r: 'か' }, { b: 'きます' }] },
      te: { ja: '書いて', tokens: [{ b: '書', r: 'か' }, { b: 'いて' }] },
      nai: { ja: '書かない', tokens: [{ b: '書', r: 'か' }, { b: 'かない' }] },
      ta: { ja: '書いた', tokens: [{ b: '書', r: 'か' }, { b: 'いた' }] },
      potential: { ja: '書ける', tokens: [{ b: '書', r: 'か' }, { b: 'ける' }] },
    },
  },
  {
    id: 'oyogu',
    word: '泳ぐ',
    tokens: [{ b: '泳', r: 'およ' }, { b: 'ぐ' }],
    type: 'godan',
    meaningKo: '헤엄치다',
    forms: {
      masu: { ja: '泳ぎます', tokens: [{ b: '泳', r: 'およ' }, { b: 'ぎます' }] },
      te: { ja: '泳いで', tokens: [{ b: '泳', r: 'およ' }, { b: 'いで' }] },
      nai: { ja: '泳がない', tokens: [{ b: '泳', r: 'およ' }, { b: 'がない' }] },
      ta: { ja: '泳いだ', tokens: [{ b: '泳', r: 'およ' }, { b: 'いだ' }] },
      potential: { ja: '泳げる', tokens: [{ b: '泳', r: 'およ' }, { b: 'げる' }] },
    },
  },
  {
    id: 'kaeru-return',
    word: '帰る',
    tokens: [{ b: '帰', r: 'かえ' }, { b: 'る' }],
    type: 'godan', // 帰る looks like ichidan but is a godan exception.
    meaningKo: '돌아가다',
    forms: {
      masu: { ja: '帰ります', tokens: [{ b: '帰', r: 'かえ' }, { b: 'ります' }] },
      te: { ja: '帰って', tokens: [{ b: '帰', r: 'かえ' }, { b: 'って' }] },
      nai: { ja: '帰らない', tokens: [{ b: '帰', r: 'かえ' }, { b: 'らない' }] },
      ta: { ja: '帰った', tokens: [{ b: '帰', r: 'かえ' }, { b: 'った' }] },
      potential: { ja: '帰れる', tokens: [{ b: '帰', r: 'かえ' }, { b: 'れる' }] },
    },
  },
  // -------- ichidan (ru-verbs) --------
  {
    id: 'taberu',
    word: '食べる',
    tokens: [{ b: '食', r: 'た' }, { b: 'べる' }],
    type: 'ichidan',
    meaningKo: '먹다',
    forms: {
      masu: { ja: '食べます', tokens: [{ b: '食', r: 'た' }, { b: 'べます' }] },
      te: { ja: '食べて', tokens: [{ b: '食', r: 'た' }, { b: 'べて' }] },
      nai: { ja: '食べない', tokens: [{ b: '食', r: 'た' }, { b: 'べない' }] },
      ta: { ja: '食べた', tokens: [{ b: '食', r: 'た' }, { b: 'べた' }] },
      potential: { ja: '食べられる', tokens: [{ b: '食', r: 'た' }, { b: 'べられる' }] },
    },
  },
  {
    id: 'miru',
    word: '見る',
    tokens: [{ b: '見', r: 'み' }, { b: 'る' }],
    type: 'ichidan',
    meaningKo: '보다',
    forms: {
      masu: { ja: '見ます', tokens: [{ b: '見', r: 'み' }, { b: 'ます' }] },
      te: { ja: '見て', tokens: [{ b: '見', r: 'み' }, { b: 'て' }] },
      nai: { ja: '見ない', tokens: [{ b: '見', r: 'み' }, { b: 'ない' }] },
      ta: { ja: '見た', tokens: [{ b: '見', r: 'み' }, { b: 'た' }] },
      potential: { ja: '見られる', tokens: [{ b: '見', r: 'み' }, { b: 'られる' }] },
    },
  },
  {
    id: 'neru',
    word: '寝る',
    tokens: [{ b: '寝', r: 'ね' }, { b: 'る' }],
    type: 'ichidan',
    meaningKo: '자다',
    forms: {
      masu: { ja: '寝ます', tokens: [{ b: '寝', r: 'ね' }, { b: 'ます' }] },
      te: { ja: '寝て', tokens: [{ b: '寝', r: 'ね' }, { b: 'て' }] },
      nai: { ja: '寝ない', tokens: [{ b: '寝', r: 'ね' }, { b: 'ない' }] },
      ta: { ja: '寝た', tokens: [{ b: '寝', r: 'ね' }, { b: 'た' }] },
      potential: { ja: '寝られる', tokens: [{ b: '寝', r: 'ね' }, { b: 'られる' }] },
    },
  },
  {
    id: 'okiru',
    word: '起きる',
    tokens: [{ b: '起', r: 'お' }, { b: 'きる' }],
    type: 'ichidan',
    meaningKo: '일어나다',
    forms: {
      masu: { ja: '起きます', tokens: [{ b: '起', r: 'お' }, { b: 'きます' }] },
      te: { ja: '起きて', tokens: [{ b: '起', r: 'お' }, { b: 'きて' }] },
      nai: { ja: '起きない', tokens: [{ b: '起', r: 'お' }, { b: 'きない' }] },
      ta: { ja: '起きた', tokens: [{ b: '起', r: 'お' }, { b: 'きた' }] },
      potential: { ja: '起きられる', tokens: [{ b: '起', r: 'お' }, { b: 'きられる' }] },
    },
  },
  {
    id: 'oshieru',
    word: '教える',
    tokens: [{ b: '教', r: 'おし' }, { b: 'える' }],
    type: 'ichidan',
    meaningKo: '가르치다',
    forms: {
      masu: { ja: '教えます', tokens: [{ b: '教', r: 'おし' }, { b: 'えます' }] },
      te: { ja: '教えて', tokens: [{ b: '教', r: 'おし' }, { b: 'えて' }] },
      nai: { ja: '教えない', tokens: [{ b: '教', r: 'おし' }, { b: 'えない' }] },
      ta: { ja: '教えた', tokens: [{ b: '教', r: 'おし' }, { b: 'えた' }] },
      potential: { ja: '教えられる', tokens: [{ b: '教', r: 'おし' }, { b: 'えられる' }] },
    },
  },
  // -------- irregular --------
  {
    id: 'suru',
    word: 'する',
    tokens: [{ b: 'する' }],
    type: 'irregular',
    meaningKo: '하다',
    forms: {
      masu: { ja: 'します', tokens: [{ b: 'します' }] },
      te: { ja: 'して', tokens: [{ b: 'して' }] },
      nai: { ja: 'しない', tokens: [{ b: 'しない' }] },
      ta: { ja: 'した', tokens: [{ b: 'した' }] },
      potential: { ja: 'できる', tokens: [{ b: 'できる' }] },
    },
  },
  {
    id: 'kuru',
    word: '来る',
    tokens: [{ b: '来', r: 'く' }, { b: 'る' }],
    type: 'irregular',
    meaningKo: '오다',
    forms: {
      masu: { ja: '来ます', tokens: [{ b: '来', r: 'き' }, { b: 'ます' }] },
      te: { ja: '来て', tokens: [{ b: '来', r: 'き' }, { b: 'て' }] },
      nai: { ja: '来ない', tokens: [{ b: '来', r: 'こ' }, { b: 'ない' }] },
      ta: { ja: '来た', tokens: [{ b: '来', r: 'き' }, { b: 'た' }] },
      potential: { ja: '来られる', tokens: [{ b: '来', r: 'こ' }, { b: 'られる' }] },
    },
  },
  {
    id: 'benkyou-suru',
    word: '勉強する',
    tokens: [{ b: '勉強', r: 'べんきょう' }, { b: 'する' }],
    type: 'irregular',
    meaningKo: '공부하다',
    forms: {
      masu: { ja: '勉強します', tokens: [{ b: '勉強', r: 'べんきょう' }, { b: 'します' }] },
      te: { ja: '勉強して', tokens: [{ b: '勉強', r: 'べんきょう' }, { b: 'して' }] },
      nai: { ja: '勉強しない', tokens: [{ b: '勉強', r: 'べんきょう' }, { b: 'しない' }] },
      ta: { ja: '勉強した', tokens: [{ b: '勉強', r: 'べんきょう' }, { b: 'した' }] },
      potential: { ja: '勉強できる', tokens: [{ b: '勉強', r: 'べんきょう' }, { b: 'できる' }] },
    },
  },
  // -------- i-adjectives --------
  {
    id: 'takai',
    word: '高い',
    tokens: [{ b: '高', r: 'たか' }, { b: 'い' }],
    type: 'i-adj',
    meaningKo: '높다 / 비싸다',
    forms: {
      masu: { ja: '高いです', tokens: [{ b: '高', r: 'たか' }, { b: 'いです' }] },
      te: { ja: '高くて', tokens: [{ b: '高', r: 'たか' }, { b: 'くて' }] },
      nai: { ja: '高くない', tokens: [{ b: '高', r: 'たか' }, { b: 'くない' }] },
      ta: { ja: '高かった', tokens: [{ b: '高', r: 'たか' }, { b: 'かった' }] },
    },
  },
  {
    id: 'oishii',
    word: 'おいしい',
    tokens: [{ b: 'おいしい' }],
    type: 'i-adj',
    meaningKo: '맛있다',
    forms: {
      masu: { ja: 'おいしいです', tokens: [{ b: 'おいしいです' }] },
      te: { ja: 'おいしくて', tokens: [{ b: 'おいしくて' }] },
      nai: { ja: 'おいしくない', tokens: [{ b: 'おいしくない' }] },
      ta: { ja: 'おいしかった', tokens: [{ b: 'おいしかった' }] },
    },
  },
  {
    id: 'ii',
    word: 'いい',
    tokens: [{ b: 'いい' }],
    type: 'i-adj',
    meaningKo: '좋다',
    forms: {
      // いい / よい is irregular: all conjugations use the よ- stem.
      masu: { ja: 'いいです', tokens: [{ b: 'いいです' }] },
      te: { ja: 'よくて', tokens: [{ b: 'よくて' }] },
      nai: { ja: 'よくない', tokens: [{ b: 'よくない' }] },
      ta: { ja: 'よかった', tokens: [{ b: 'よかった' }] },
    },
  },
  {
    id: 'atsui',
    word: '暑い',
    tokens: [{ b: '暑', r: 'あつ' }, { b: 'い' }],
    type: 'i-adj',
    meaningKo: '덥다',
    forms: {
      masu: { ja: '暑いです', tokens: [{ b: '暑', r: 'あつ' }, { b: 'いです' }] },
      te: { ja: '暑くて', tokens: [{ b: '暑', r: 'あつ' }, { b: 'くて' }] },
      nai: { ja: '暑くない', tokens: [{ b: '暑', r: 'あつ' }, { b: 'くない' }] },
      ta: { ja: '暑かった', tokens: [{ b: '暑', r: 'あつ' }, { b: 'かった' }] },
    },
  },
  // -------- na-adjectives --------
  {
    id: 'kirei',
    word: 'きれいだ',
    tokens: [{ b: 'きれいだ' }],
    type: 'na-adj',
    meaningKo: '예쁘다 / 깨끗하다',
    forms: {
      masu: { ja: 'きれいです', tokens: [{ b: 'きれいです' }] },
      te: { ja: 'きれいで', tokens: [{ b: 'きれいで' }] },
      nai: { ja: 'きれいじゃない', tokens: [{ b: 'きれいじゃない' }] },
      ta: { ja: 'きれいだった', tokens: [{ b: 'きれいだった' }] },
    },
  },
  {
    id: 'shizuka',
    word: '静かだ',
    tokens: [{ b: '静', r: 'しず' }, { b: 'かだ' }],
    type: 'na-adj',
    meaningKo: '조용하다',
    forms: {
      masu: { ja: '静かです', tokens: [{ b: '静', r: 'しず' }, { b: 'かです' }] },
      te: { ja: '静かで', tokens: [{ b: '静', r: 'しず' }, { b: 'かで' }] },
      nai: { ja: '静かじゃない', tokens: [{ b: '静', r: 'しず' }, { b: 'かじゃない' }] },
      ta: { ja: '静かだった', tokens: [{ b: '静', r: 'しず' }, { b: 'かだった' }] },
    },
  },
  {
    id: 'genki',
    word: '元気だ',
    tokens: [{ b: '元気', r: 'げんき' }, { b: 'だ' }],
    type: 'na-adj',
    meaningKo: '건강하다 / 활기차다',
    forms: {
      masu: { ja: '元気です', tokens: [{ b: '元気', r: 'げんき' }, { b: 'です' }] },
      te: { ja: '元気で', tokens: [{ b: '元気', r: 'げんき' }, { b: 'で' }] },
      nai: { ja: '元気じゃない', tokens: [{ b: '元気', r: 'げんき' }, { b: 'じゃない' }] },
      ta: { ja: '元気だった', tokens: [{ b: '元気', r: 'げんき' }, { b: 'だった' }] },
    },
  },
];

export const CONJ_TOTAL = CONJUGATIONS.length;

export const TYPE_LABEL: Record<WordType, string> = {
  godan: '5단동사 (u동사)',
  ichidan: '1단동사 (ru동사)',
  irregular: '불규칙동사',
  'i-adj': 'い형용사',
  'na-adj': 'な형용사',
};

// Short rule summary per type, for browse mode.
export type TypeRule = { type: WordType; title: string; rulesKo: string[]; sampleId: string };

export const TYPE_RULES: TypeRule[] = [
  {
    type: 'godan',
    title: '5단동사 (u동사)',
    sampleId: 'nomu',
    rulesKo: [
      'ます형: 어미 う단을 い단으로 바꾸고 ます. 飲む → 飲みます',
      'て형: 어미에 따라 음편. む/ぶ/ぬ → んで, う/つ/る → って, く → いて, ぐ → いで, す → して',
      'ない형: 어미 う단을 あ단으로. 단 う로 끝나면 わ. 買う → 買わない',
      'た형: て형과 같은 음편, て→た / で→だ. 飲む → 飲んだ',
      '가능형: 어미 う단을 え단으로 바꾸고 る. 飲む → 飲める',
    ],
  },
  {
    type: 'ichidan',
    title: '1단동사 (ru동사)',
    sampleId: 'taberu',
    rulesKo: [
      'ます형: 어미 る를 떼고 ます. 食べる → 食べます',
      'て형: 어미 る를 떼고 て. 食べる → 食べて',
      'ない형: 어미 る를 떼고 ない. 食べる → 食べない',
      'た형: 어미 る를 떼고 た. 食べる → 食べた',
      '가능형: 어미 る를 떼고 られる. 食べる → 食べられる',
    ],
  },
  {
    type: 'irregular',
    title: '불규칙동사 (する / 来る)',
    sampleId: 'suru',
    rulesKo: [
      'する → します / して / しない / した, 가능형은 できる',
      '来る(くる) → 来ます(きます) / 来て(きて) / 来ない(こない) / 来た(きた)',
      '来る 가능형은 来られる(こられる)',
      '한자어+する(勉強する 등)도 する와 똑같이 활용',
    ],
  },
  {
    type: 'i-adj',
    title: 'い형용사',
    sampleId: 'takai',
    rulesKo: [
      '정중형: 사전형 그대로 + です. 高い → 高いです',
      'て형(연결): 어미 い를 くて로. 高い → 高くて',
      '부정형: 어미 い를 くない로. 高い → 高くない',
      '과거형: 어미 い를 かった로. 高い → 高かった',
      'いい는 예외: よくて / よくない / よかった',
    ],
  },
  {
    type: 'na-adj',
    title: 'な형용사',
    sampleId: 'kirei',
    rulesKo: [
      '정중형: 어간 + です. きれいだ → きれいです',
      'て형(연결): 어간 + で. きれいだ → きれいで',
      '부정형: 어간 + じゃない. きれいだ → きれいじゃない',
      '과거형: 어간 + だった. きれいだ → きれいだった',
      '명사를 꾸밀 때는 어간 + な (예: きれいな はな)',
    ],
  },
];

export function wordsByType(type: WordType): ConjWord[] {
  return CONJUGATIONS.filter((w) => w.type === type);
}
