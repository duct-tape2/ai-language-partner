// Hand-authored keigo (敬語) bank for the 존댓말/경어 guide screen.
// Static data only, no network. A real N4 -> N3 pain point: the same plain verb
// splits into three politeness registers, and 존경어/겸양어 often become
// suppletive (completely different) verbs, not simple ます-attachments.
//
// Four columns per entry:
//  - plain     : 사전형 (dictionary / casual form)
//  - teineigo  : 정중어 (丁寧語) — the ordinary polite ます form, neutral respect
//  - sonkeigo  : 존경어 (尊敬語) — RAISES the other person / their actions
//  - kenjougo  : 겸양어 (謙譲語) — LOWERS the speaker's own actions to show respect
//
// Furigana tokens mirror the FuriToken shape used by <FuriganaTokens>:
// kanji chunks carry an `r` reading, kana chunks omit it.

export type FuriTok = { b: string; r?: string };

// One politeness form: display string (for TTS) + furigana tokens (for render).
export type KeigoForm = { ja: string; tokens: FuriTok[] };

export type KeigoEntry = {
  id: string;
  plain: KeigoForm; // 사전형
  tokens: FuriTok[]; // convenience alias of plain.tokens (dictionary form furigana)
  teineigo: KeigoForm; // 정중어 (ます)
  sonkeigo: KeigoForm; // 존경어 (尊敬語)
  kenjougo: KeigoForm; // 겸양어 (謙譲語)
  meaningKo: string; // 뜻
  usageKo: string; // 사용 노트 (언제 어느 형을 쓰는지)
};

// Column metadata used by the screen header / legend.
export type KeigoColKey = 'plain' | 'teineigo' | 'sonkeigo' | 'kenjougo';
export type KeigoCol = { key: KeigoColKey; label: string; shortKo: string };

export const KEIGO_COLS: KeigoCol[] = [
  { key: 'plain', label: '사전형', shortKo: '친구 사이의 반말' },
  { key: 'teineigo', label: '정중어 (ます)', shortKo: '누구에게나 무난한 존댓말' },
  { key: 'sonkeigo', label: '존경어 (尊敬語)', shortKo: '상대를 높임' },
  { key: 'kenjougo', label: '겸양어 (謙譲語)', shortKo: '나를 낮춤' },
];

export const KEIGO: KeigoEntry[] = [
  {
    id: 'suru',
    plain: { ja: 'する', tokens: [{ b: 'する' }] },
    tokens: [{ b: 'する' }],
    teineigo: { ja: 'します', tokens: [{ b: 'します' }] },
    sonkeigo: { ja: 'なさる', tokens: [{ b: 'なさる' }] },
    kenjougo: { ja: 'いたす', tokens: [{ b: 'いたす' }] },
    meaningKo: '하다',
    usageKo: '상대가 하는 일이면 なさる, 내가 하는 일이면 いたす. 「お電話いたします」처럼 겸양어는 자기 행동에만.',
  },
  {
    id: 'iku',
    plain: { ja: '行く', tokens: [{ b: '行', r: 'い' }, { b: 'く' }] },
    tokens: [{ b: '行', r: 'い' }, { b: 'く' }],
    teineigo: { ja: '行きます', tokens: [{ b: '行', r: 'い' }, { b: 'きます' }] },
    sonkeigo: { ja: 'いらっしゃる', tokens: [{ b: 'いらっしゃる' }] },
    kenjougo: { ja: '参る', tokens: [{ b: '参', r: 'まい' }, { b: 'る' }] },
    meaningKo: '가다',
    usageKo: 'いらっしゃる는 行く 오다 있다를 한꺼번에 높이는 만능 존경어. 내가 갈 때는 参る.',
  },
  {
    id: 'kuru',
    plain: { ja: '来る', tokens: [{ b: '来', r: 'く' }, { b: 'る' }] },
    tokens: [{ b: '来', r: 'く' }, { b: 'る' }],
    teineigo: { ja: '来ます', tokens: [{ b: '来', r: 'き' }, { b: 'ます' }] },
    sonkeigo: { ja: 'いらっしゃる', tokens: [{ b: 'いらっしゃる' }] },
    kenjougo: { ja: '参る', tokens: [{ b: '参', r: 'まい' }, { b: 'る' }] },
    meaningKo: '오다',
    usageKo: '来る도 いらっしゃる로 높임. 「先生がいらっしゃいました」. 내가 올 때는 参る.',
  },
  {
    id: 'iru',
    plain: { ja: 'いる', tokens: [{ b: 'いる' }] },
    tokens: [{ b: 'いる' }],
    teineigo: { ja: 'います', tokens: [{ b: 'います' }] },
    sonkeigo: { ja: 'いらっしゃる', tokens: [{ b: 'いらっしゃる' }] },
    kenjougo: { ja: 'おる', tokens: [{ b: 'おる' }] },
    meaningKo: '있다 (사람)',
    usageKo: '존재의 いる도 いらっしゃる. 나는 おる (「私は東京におります」). 사람에게만, 사물은 ある.',
  },
  {
    id: 'taberu',
    plain: { ja: '食べる', tokens: [{ b: '食', r: 'た' }, { b: 'べる' }] },
    tokens: [{ b: '食', r: 'た' }, { b: 'べる' }],
    teineigo: { ja: '食べます', tokens: [{ b: '食', r: 'た' }, { b: 'べます' }] },
    sonkeigo: { ja: '召し上がる', tokens: [{ b: '召', r: 'め' }, { b: 'し' }, { b: '上', r: 'あ' }, { b: 'がる' }] },
    kenjougo: { ja: 'いただく', tokens: [{ b: 'いただく' }] },
    meaningKo: '먹다',
    usageKo: '飲む 마시다도 똑같이 召し上がる / いただく. いただく는 받다의 겸양어와 같은 단어.',
  },
  {
    id: 'nomu',
    plain: { ja: '飲む', tokens: [{ b: '飲', r: 'の' }, { b: 'む' }] },
    tokens: [{ b: '飲', r: 'の' }, { b: 'む' }],
    teineigo: { ja: '飲みます', tokens: [{ b: '飲', r: 'の' }, { b: 'みます' }] },
    sonkeigo: { ja: '召し上がる', tokens: [{ b: '召', r: 'め' }, { b: 'し' }, { b: '上', r: 'あ' }, { b: 'がる' }] },
    kenjougo: { ja: 'いただく', tokens: [{ b: 'いただく' }] },
    meaningKo: '마시다',
    usageKo: '食べる와 존경어 겸양어를 공유. 「お茶を召し上がりますか」 / 「いただきます」.',
  },
  {
    id: 'miru',
    plain: { ja: '見る', tokens: [{ b: '見', r: 'み' }, { b: 'る' }] },
    tokens: [{ b: '見', r: 'み' }, { b: 'る' }],
    teineigo: { ja: '見ます', tokens: [{ b: '見', r: 'み' }, { b: 'ます' }] },
    sonkeigo: { ja: 'ご覧になる', tokens: [{ b: 'ご' }, { b: '覧', r: 'らん' }, { b: 'になる' }] },
    kenjougo: { ja: '拝見する', tokens: [{ b: '拝', r: 'はい' }, { b: '見', r: 'けん' }, { b: 'する' }] },
    meaningKo: '보다',
    usageKo: '자료를 상대가 보면 ご覧になる, 내가 보여받으면 拝見する (「資料を拝見しました」).',
  },
  {
    id: 'iu',
    plain: { ja: '言う', tokens: [{ b: '言', r: 'い' }, { b: 'う' }] },
    tokens: [{ b: '言', r: 'い' }, { b: 'う' }],
    teineigo: { ja: '言います', tokens: [{ b: '言', r: 'い' }, { b: 'います' }] },
    sonkeigo: { ja: 'おっしゃる', tokens: [{ b: 'おっしゃる' }] },
    kenjougo: { ja: '申す', tokens: [{ b: '申', r: 'もう' }, { b: 'す' }] },
    meaningKo: '말하다',
    usageKo: '이름 댈 때 「田中と申します」가 겸양어 대표 문장. 상대 말은 おっしゃる. 申し上げる는 더 정중.',
  },
  {
    id: 'kiku',
    plain: { ja: '聞く', tokens: [{ b: '聞', r: 'き' }, { b: 'く' }] },
    tokens: [{ b: '聞', r: 'き' }, { b: 'く' }],
    teineigo: { ja: '聞きます', tokens: [{ b: '聞', r: 'き' }, { b: 'きます' }] },
    sonkeigo: { ja: 'お聞きになる', tokens: [{ b: 'お' }, { b: '聞', r: 'き' }, { b: 'きになる' }] },
    kenjougo: { ja: '伺う', tokens: [{ b: '伺', r: 'うかが' }, { b: 'う' }] },
    meaningKo: '듣다 / 묻다',
    usageKo: '내가 묻거나 방문할 때 伺う (「明日伺います」는 방문의 뜻도). 존경어는 규칙형 お聞きになる.',
  },
  {
    id: 'au',
    plain: { ja: '会う', tokens: [{ b: '会', r: 'あ' }, { b: 'う' }] },
    tokens: [{ b: '会', r: 'あ' }, { b: 'う' }],
    teineigo: { ja: '会います', tokens: [{ b: '会', r: 'あ' }, { b: 'います' }] },
    sonkeigo: { ja: 'お会いになる', tokens: [{ b: 'お' }, { b: '会', r: 'あ' }, { b: 'いになる' }] },
    kenjougo: { ja: 'お目にかかる', tokens: [{ b: 'お' }, { b: '目', r: 'め' }, { b: 'にかかる' }] },
    meaningKo: '만나다',
    usageKo: '겸양어 お目にかかる는 관용구 (「お目にかかれて光栄です」). 존경어는 규칙형.',
  },
  {
    id: 'shiru',
    plain: { ja: '知る', tokens: [{ b: '知', r: 'し' }, { b: 'る' }] },
    tokens: [{ b: '知', r: 'し' }, { b: 'る' }],
    teineigo: { ja: '知っています', tokens: [{ b: '知', r: 'し' }, { b: 'っています' }] },
    sonkeigo: { ja: 'ご存じだ', tokens: [{ b: 'ご' }, { b: '存', r: 'ぞん' }, { b: 'じだ' }] },
    kenjougo: { ja: '存じ上げる', tokens: [{ b: '存', r: 'ぞん' }, { b: 'じ' }, { b: '上', r: 'あ' }, { b: 'げる' }] },
    meaningKo: '알다',
    usageKo: '「ご存じですか」= 아세요?, 「存じ上げております」= 알고 있습니다. 부정은 「存じません」.',
  },
  {
    id: 'ageru',
    plain: { ja: 'あげる', tokens: [{ b: 'あげる' }] },
    tokens: [{ b: 'あげる' }],
    teineigo: { ja: 'あげます', tokens: [{ b: 'あげます' }] },
    sonkeigo: { ja: 'くださる', tokens: [{ b: 'くださる' }] },
    kenjougo: { ja: '差し上げる', tokens: [{ b: '差', r: 'さ' }, { b: 'し' }, { b: '上', r: 'あ' }, { b: 'げる' }] },
    meaningKo: '주다 / 드리다',
    usageKo: '상대가 나에게 주면 くださる, 내가 상대에게 드리면 差し上げる. 방향이 헷갈리기 쉬움.',
  },
  {
    id: 'morau',
    plain: { ja: 'もらう', tokens: [{ b: 'もらう' }] },
    tokens: [{ b: 'もらう' }],
    teineigo: { ja: 'もらいます', tokens: [{ b: 'もらいます' }] },
    sonkeigo: { ja: 'くださる', tokens: [{ b: 'くださる' }] },
    kenjougo: { ja: 'いただく', tokens: [{ b: 'いただく' }] },
    meaningKo: '받다',
    usageKo: '내가 받는 겸양어 いただく (「お手紙をいただきました」). 상대가 주는 くださる와 짝.',
  },
  {
    id: 'omou',
    plain: { ja: '思う', tokens: [{ b: '思', r: 'おも' }, { b: 'う' }] },
    tokens: [{ b: '思', r: 'おも' }, { b: 'う' }],
    teineigo: { ja: '思います', tokens: [{ b: '思', r: 'おも' }, { b: 'います' }] },
    sonkeigo: { ja: 'お思いになる', tokens: [{ b: 'お' }, { b: '思', r: 'おも' }, { b: 'いになる' }] },
    kenjougo: { ja: '存じる', tokens: [{ b: '存', r: 'ぞん' }, { b: 'じる' }] },
    meaningKo: '생각하다',
    usageKo: '겸양어 存じる는 思う와 知る 둘 다 커버. 「〜と存じます」= 라고 생각합니다 (아주 정중).',
  },
  {
    id: 'suru-give',
    plain: { ja: '見せる', tokens: [{ b: '見', r: 'み' }, { b: 'せる' }] },
    tokens: [{ b: '見', r: 'み' }, { b: 'せる' }],
    teineigo: { ja: '見せます', tokens: [{ b: '見', r: 'み' }, { b: 'せます' }] },
    sonkeigo: { ja: 'お見せになる', tokens: [{ b: 'お' }, { b: '見', r: 'み' }, { b: 'せになる' }] },
    kenjougo: { ja: 'お目にかける', tokens: [{ b: 'お' }, { b: '目', r: 'め' }, { b: 'にかける' }] },
    meaningKo: '보여주다',
    usageKo: '겸양어 お目にかける / ご覧に入れる = 보여드리다. 존경어는 규칙형 お見せになる.',
  },
  {
    id: 'kariru',
    plain: { ja: '借りる', tokens: [{ b: '借', r: 'か' }, { b: 'りる' }] },
    tokens: [{ b: '借', r: 'か' }, { b: 'りる' }],
    teineigo: { ja: '借ります', tokens: [{ b: '借', r: 'か' }, { b: 'ります' }] },
    sonkeigo: { ja: 'お借りになる', tokens: [{ b: 'お' }, { b: '借', r: 'か' }, { b: 'りになる' }] },
    kenjougo: { ja: '拝借する', tokens: [{ b: '拝', r: 'はい' }, { b: '借', r: 'しゃく' }, { b: 'する' }] },
    meaningKo: '빌리다',
    usageKo: '내가 빌릴 때 拝借する (「ペンを拝借します」). 딱딱한 비즈니스 표현.',
  },
  {
    id: 'suru-general-regular',
    plain: { ja: '使う', tokens: [{ b: '使', r: 'つか' }, { b: 'う' }] },
    tokens: [{ b: '使', r: 'つか' }, { b: 'う' }],
    teineigo: { ja: '使います', tokens: [{ b: '使', r: 'つか' }, { b: 'います' }] },
    sonkeigo: { ja: 'お使いになる', tokens: [{ b: 'お' }, { b: '使', r: 'つか' }, { b: 'いになる' }] },
    kenjougo: { ja: 'お使いする', tokens: [{ b: 'お' }, { b: '使', r: 'つか' }, { b: 'いする' }] },
    meaningKo: '쓰다 / 사용하다',
    usageKo: '전용 경어가 없는 동사의 규칙 패턴: 존경어 「お＋ます어간＋になる」, 겸양어 「お＋ます어간＋する」.',
  },
];

export const KEIGO_TOTAL = KEIGO.length;

// The three keigo registers explained in one place (used by the screen intro).
export type KeigoTypeInfo = { key: 'teineigo' | 'sonkeigo' | 'kenjougo'; title: string; descKo: string; exampleKo: string };

export const KEIGO_TYPES: KeigoTypeInfo[] = [
  {
    key: 'teineigo',
    title: '정중어 (丁寧語)',
    descKo: 'です / ます를 붙여 문장을 공손하게. 상대나 나를 높이거나 낮추지 않고, 말투 자체만 정중하게 만들어요. 가장 먼저 배우는 존댓말.',
    exampleKo: '行く 가다 -> 行きます',
  },
  {
    key: 'sonkeigo',
    title: '존경어 (尊敬語)',
    descKo: '상대(윗사람)의 행동이나 상태를 높여요. 주어가 상대일 때 사용. 전용 단어(いらっしゃる 등)가 있거나 「お～になる」 규칙형을 써요.',
    exampleKo: '先生が来る -> 先生がいらっしゃる',
  },
  {
    key: 'kenjougo',
    title: '겸양어 (謙譲語)',
    descKo: '내(또는 내 쪽)의 행동을 낮춰서 결과적으로 상대를 높여요. 주어가 나일 때만 사용. 전용 단어(参る 등)나 「お～する」 규칙형.',
    exampleKo: '私が行く -> 私が参る',
  },
];
