// Hand-authored JLPT N4 mock exam (20 questions). No network fetch — the data
// ships with the app. Sections mirror the real N4 paper: 문자·어휘 (kanji reading /
// word meaning), 문법 (grammar), 독해 (short passage + comprehension question).
//
// promptTokens (optional) drives FuriganaTokens so kanji chunks show their reading
// stacked over the base. passageJa (optional) is the short reading text shown above
// the question stem. answerIndex is 0-based into choices (always 4 options).

export type ExamSection = 'vocab' | 'grammar' | 'reading';

export type FuriTok = { b: string; r?: string };

export type ExamQuestion = {
  id: string;
  section: ExamSection;
  promptJa: string;
  promptTokens?: FuriTok[];
  passageJa?: string;
  choices: string[];
  answerIndex: number;
  explanationKo: string;
};

// 합격 기준: 60% 이상 (12/20).
export const PASS_RATIO = 0.6;

export const SECTION_LABEL: Record<ExamSection, string> = {
  vocab: '문자·어휘',
  grammar: '문법',
  reading: '독해',
};

export const MOCK_EXAM: ExamQuestion[] = [
  // ---------- 문자·어휘 (1-8) ----------
  {
    id: 'v1',
    section: 'vocab',
    promptJa: '来週、日本へ行きます。',
    promptTokens: [
      { b: '来', r: 'らい' },
      { b: '週', r: 'しゅう' },
      { b: '、' },
      { b: '日', r: 'に' },
      { b: '本', r: 'ほん' },
      { b: 'へ' },
      { b: '行', r: 'い' },
      { b: 'きます' },
      { b: '。' },
    ],
    choices: ['らいしゅう', 'らいじゅう', 'らいしゅ', 'らいゅう'],
    answerIndex: 0,
    explanationKo: '来週(らいしゅう)는 "다음 주". 週는 음독 しゅう로, 촉음이나 탁음이 붙지 않습니다.',
  },
  {
    id: 'v2',
    section: 'vocab',
    promptJa: 'この店はとても有名です。',
    promptTokens: [
      { b: 'この' },
      { b: '店', r: 'みせ' },
      { b: 'は' },
      { b: 'とても' },
      { b: '有', r: 'ゆう' },
      { b: '名', r: 'めい' },
      { b: 'です' },
      { b: '。' },
    ],
    choices: ['ゆうめい', 'ゆうめえ', 'ようめい', 'ゆめい'],
    answerIndex: 0,
    explanationKo: '有名(ゆうめい)는 "유명". 有=ゆう, 名=めい. 장음 표기는 めい이며 めえ가 아닙니다.',
  },
  {
    id: 'v3',
    section: 'vocab',
    promptJa: '朝はいつも六時におきます。',
    promptTokens: [
      { b: '朝', r: 'あさ' },
      { b: 'は' },
      { b: 'いつも' },
      { b: '六', r: 'ろく' },
      { b: '時', r: 'じ' },
      { b: 'に' },
      { b: 'おきます' },
      { b: '。' },
    ],
    choices: ['ろくじ', 'ろくし', 'むじ', 'ろっじ'],
    answerIndex: 0,
    explanationKo: '六時(ろくじ)는 "여섯 시". 時는 시각을 셀 때 じ로 읽습니다. 六은 ろく.',
  },
  {
    id: 'v4',
    section: 'vocab',
    promptJa: 'かれは英語をおしえています。',
    promptTokens: [
      { b: 'かれは' },
      { b: '英', r: 'えい' },
      { b: '語', r: 'ご' },
      { b: 'を' },
      { b: 'おしえて' },
      { b: 'います' },
      { b: '。' },
    ],
    choices: ['えいご', 'えいこ', 'えご', 'えいごう'],
    answerIndex: 0,
    explanationKo: '英語(えいご)는 "영어". 語는 여기서 탁음 ご. えいこ처럼 탁음이 빠지면 틀립니다.',
  },
  {
    id: 'v5',
    section: 'vocab',
    promptJa: '（　）にきっぷを買いました。',
    choices: ['えき', 'いえ', 'みせ', 'まち'],
    answerIndex: 0,
    explanationKo: 'きっぷ(표)를 사는 곳은 えき(역)입니다. いえ=집, みせ=가게, まち=거리.',
  },
  {
    id: 'v6',
    section: 'vocab',
    promptJa: 'この問題はとても（　）です。',
    choices: ['かんたん', 'げんき', 'しんせつ', 'べんり'],
    answerIndex: 0,
    explanationKo: '問題(문제)에 어울리는 형용동사는 かんたん(간단). げんき=건강, しんせつ=친절, べんり=편리로 문맥에 맞지 않습니다.',
  },
  {
    id: 'v7',
    section: 'vocab',
    promptJa: 'つかれたので、すこし（　）ました。',
    choices: ['やすみ', 'あそび', 'はしり', 'あるき'],
    answerIndex: 0,
    explanationKo: 'つかれた(피곤하다) 뒤에는 やすむ(쉬다)가 자연스럽습니다. やすみました=쉬었습니다.',
  },
  {
    id: 'v8',
    section: 'vocab',
    promptJa: 'このかばんは（　）が、とても軽いです。',
    choices: ['大きいです', '小さいです', '安いです', '古いです'],
    answerIndex: 0,
    explanationKo: '「が」로 대조되므로 앞은 軽い(가볍다)와 대비되는 뜻이어야 합니다. 「大きいですが、軽い」= 크지만 가볍다가 가장 자연스럽습니다.',
  },

  // ---------- 문법 (9-15) ----------
  {
    id: 'g1',
    section: 'grammar',
    promptJa: '日本語を三年（　）べんきょうしています。',
    choices: ['から', 'まで', 'ぐらい', 'しか'],
    answerIndex: 2,
    explanationKo: '기간의 대략적인 양을 나타낼 때 ～ぐらい(정도). "삼 년 정도 공부하고 있습니다". から=부터, まで=까지, しか=밖에.',
  },
  {
    id: 'g2',
    section: 'grammar',
    promptJa: 'まどが開いています。だれか（　）でしょう。',
    choices: ['開けた', '開いた', '開ける', '開きます'],
    answerIndex: 0,
    explanationKo: '"누군가 열었을 것이다". 사람이 의도적으로 여는 타동사 開ける의 과거형 開けた가 정답입니다. 開く는 자동사입니다.',
  },
  {
    id: 'g3',
    section: 'grammar',
    promptJa: 'あした雨が（　）、しあいは中止です。',
    choices: ['ふると', 'ふったら', 'ふれば', 'ふって'],
    answerIndex: 1,
    explanationKo: '아직 일어나지 않은 개별 조건 "비가 오면 (그때는)"에는 ～たら가 자연스럽습니다. ～と는 항상 성립하는 일반 조건에 씁니다.',
  },
  {
    id: 'g4',
    section: 'grammar',
    promptJa: '先生に本を貸して（　）。',
    choices: ['あげました', 'くれました', 'もらいました', 'やりました'],
    answerIndex: 2,
    explanationKo: '내가 선생님으로부터 받는 행위이므로 ～てもらう. "선생님이 책을 빌려 주셨다(내가 받았다)". くれる는 상대가 주어일 때 씁니다.',
  },
  {
    id: 'g5',
    section: 'grammar',
    promptJa: 'この漢字は読める（　）、書けません。',
    choices: ['けど', 'から', 'ので', 'し'],
    answerIndex: 0,
    explanationKo: '"읽을 수 있지만 쓸 수 없다"라는 역접이므로 けど(=けれど). から/ので는 이유, し는 나열입니다.',
  },
  {
    id: 'g6',
    section: 'grammar',
    promptJa: 'へやをきれいに（　）から、出かけます。',
    choices: ['して', 'なって', 'あって', 'いて'],
    answerIndex: 0,
    explanationKo: 'きれいに + する = "깨끗하게 하다(청소하다)". 형용동사 + に + する 형태입니다. なる는 "～해지다"로 의지적 행동이 아닙니다.',
  },
  {
    id: 'g7',
    section: 'grammar',
    promptJa: 'いそがしくても、あさごはんは（　）ほうがいいです。',
    choices: ['食べる', '食べた', '食べて', '食べない'],
    answerIndex: 1,
    explanationKo: '조언 "～하는 편이 좋다"의 긍정형은 동사 た형 + ほうがいい. 따라서 食べたほうがいい가 정답입니다.',
  },

  // ---------- 독해 (16-20) ----------
  {
    id: 'r1',
    section: 'reading',
    passageJa:
      'わたしは毎朝、公園を散歩します。天気がいい日は三十分ぐらい歩きますが、雨の日は歩きません。かわりに、家でストレッチをします。',
    promptJa: '雨の日、この人は何をしますか。',
    choices: ['三十分歩く', '公園を散歩する', '家でストレッチをする', '何もしない'],
    answerIndex: 2,
    explanationKo: '본문에 "雨の日は歩きません。かわりに、家でストレッチをします"라고 나옵니다. 비 오는 날에는 집에서 스트레칭을 합니다.',
  },
  {
    id: 'r2',
    section: 'reading',
    passageJa:
      'たなかさんへ\nあしたの会議は午後二時からです。場所が三階の会議室にかわりました。しりょうを二十部、コピーして持ってきてください。\nやまだ',
    promptJa: 'たなかさんは、何を持っていきますか。',
    choices: ['会議室のかぎ', 'コピーしたしりょう', 'あたらしいパソコン', 'お茶とおかし'],
    answerIndex: 1,
    explanationKo: '메모에 "しりょうを二十部、コピーして持ってきてください"라고 부탁했으므로 복사한 자료를 가져갑니다.',
  },
  {
    id: 'r3',
    section: 'reading',
    passageJa:
      'たなかさんへ\nあしたの会議は午後二時からです。場所が三階の会議室にかわりました。しりょうを二十部、コピーして持ってきてください。\nやまだ',
    promptJa: '会議について、正しいものはどれですか。',
    choices: [
      '会議は午前中に始まる',
      '場所が三階にかわった',
      'しりょうはいらない',
      '会議は中止になった',
    ],
    answerIndex: 1,
    explanationKo: '"場所が三階の会議室にかわりました"에서 장소가 3층으로 바뀌었음을 알 수 있습니다. 회의는 오후 2시, 자료는 필요합니다.',
  },
  {
    id: 'r4',
    section: 'reading',
    passageJa:
      'キムさんは去年、日本に来ました。はじめは日本語がぜんぜん話せなくて、こまりました。でも、毎日アルバイトのお店でお客さんと話して、少しずつ上手になりました。今は友だちもたくさんできて、日本の生活がとても楽しいです。',
    promptJa: 'キムさんの日本語は、どうして上手になりましたか。',
    choices: [
      '学校でたくさん勉強したから',
      '毎日お店でお客さんと話したから',
      '日本人の友だちが教えたから',
      'テレビを毎日見たから',
    ],
    answerIndex: 1,
    explanationKo: '"毎日アルバイトのお店でお客さんと話して、少しずつ上手になりました"가 이유입니다. 가게에서 손님과 매일 대화한 것이 실력 향상의 원인입니다.',
  },
  {
    id: 'r5',
    section: 'reading',
    passageJa:
      'キムさんは去年、日本に来ました。はじめは日本語がぜんぜん話せなくて、こまりました。でも、毎日アルバイトのお店でお客さんと話して、少しずつ上手になりました。今は友だちもたくさんできて、日本の生活がとても楽しいです。',
    promptJa: '今のキムさんについて、正しいものはどれですか。',
    choices: [
      '日本語がぜんぜん話せない',
      '日本の生活がつまらない',
      '友だちがたくさんいる',
      '国に帰りたがっている',
    ],
    answerIndex: 2,
    explanationKo: '"今は友だちもたくさんできて、日本の生活がとても楽しいです"라고 했으므로 지금은 친구가 많고 생활이 즐겁습니다.',
  },

  // ---------- 문자·어휘 추가 (21-26) ----------
  {
    id: 'v9',
    section: 'vocab',
    promptJa: '毎日、日記を書いています。',
    promptTokens: [
      { b: '毎', r: 'まい' },
      { b: '日', r: 'にち' },
      { b: '、' },
      { b: '日', r: 'にっ' },
      { b: '記', r: 'き' },
      { b: 'を' },
      { b: '書', r: 'か' },
      { b: 'いて' },
      { b: 'います' },
      { b: '。' },
    ],
    choices: ['にっき', 'にちき', 'にっぎ', 'にちぎ'],
    answerIndex: 0,
    explanationKo: '日記(にっき)는 "일기". 日+記가 이어질 때 촉음화되어 にっき로 읽습니다. 탁음은 붙지 않습니다.',
  },
  {
    id: 'v10',
    section: 'vocab',
    promptJa: '会社まで電車で行きます。',
    promptTokens: [
      { b: '会', r: 'かい' },
      { b: '社', r: 'しゃ' },
      { b: 'まで' },
      { b: '電', r: 'でん' },
      { b: '車', r: 'しゃ' },
      { b: 'で' },
      { b: '行', r: 'い' },
      { b: 'きます' },
      { b: '。' },
    ],
    choices: ['でんしゃ', 'でんしゃあ', 'てんしゃ', 'でんじゃ'],
    answerIndex: 0,
    explanationKo: '電車(でんしゃ)는 "전철". 電=でん, 車=しゃ. 첫소리는 탁음 で이며 て가 아닙니다.',
  },
  {
    id: 'v11',
    section: 'vocab',
    promptJa: 'あの人はとても親切です。',
    promptTokens: [
      { b: 'あの' },
      { b: '人', r: 'ひと' },
      { b: 'は' },
      { b: 'とても' },
      { b: '親', r: 'しん' },
      { b: '切', r: 'せつ' },
      { b: 'です' },
      { b: '。' },
    ],
    choices: ['しんせつ', 'しんせち', 'ちんせつ', 'しんぜつ'],
    answerIndex: 0,
    explanationKo: '親切(しんせつ)는 "친절". 親=しん, 切=せつ. 切는 여기서 せつ로 읽으며 せち가 아닙니다.',
  },
  {
    id: 'v12',
    section: 'vocab',
    promptJa: 'つぎのえきで電車を（　）ください。',
    choices: ['おりて', 'のって', 'あがって', 'はいって'],
    answerIndex: 0,
    explanationKo: '전철에서 내리는 것은 おりる(降りる). "다음 역에서 내려 주세요". のる=타다, あがる=오르다, はいる=들어가다.',
  },
  {
    id: 'v13',
    section: 'vocab',
    promptJa: '手をあらってから、ごはんを（　）。',
    choices: ['食べます', '飲みます', '読みます', '見ます'],
    answerIndex: 0,
    explanationKo: 'ごはん(밥)에 어울리는 동사는 食べる(먹다). 飲む=마시다, 読む=읽다, 見る=보다로 문맥에 맞지 않습니다.',
  },
  {
    id: 'v14',
    section: 'vocab',
    promptJa: 'この道はせまいので、車は（　）です。',
    choices: ['あぶない', 'おいしい', 'うれしい', 'たのしい'],
    answerIndex: 0,
    explanationKo: 'せまい道(좁은 길)에서 차와 어울리는 형용사는 あぶない(위험하다). おいしい=맛있다, うれしい=기쁘다, たのしい=즐겁다.',
  },

  // ---------- 문법 추가 (27-32) ----------
  {
    id: 'g8',
    section: 'grammar',
    promptJa: 'いま宿題を（　）ところです。',
    choices: ['している', 'した', 'する', 'しない'],
    answerIndex: 0,
    explanationKo: '"지금 막 ～하고 있는 중이다"는 동사 て형 + いる + ところ. 「しているところ」= 하고 있는 중. 진행을 나타냅니다.',
  },
  {
    id: 'g9',
    section: 'grammar',
    promptJa: '大きい声で話す（　）してください。',
    choices: ['ように', 'ために', 'そうに', 'みたいに'],
    answerIndex: 0,
    explanationKo: '"～하도록 해 주세요"라는 지시·목표에는 ～ようにする. 「話すようにしてください」= 큰 소리로 말하도록 하세요.',
  },
  {
    id: 'g10',
    section: 'grammar',
    promptJa: '部屋のでんきが（　）います。だれもいないのに。',
    choices: ['ついて', 'つけて', 'けして', 'きえて'],
    answerIndex: 0,
    explanationKo: '불이 켜져 있는 상태는 자동사 つく의 て형 + いる = ついている. つける는 타동사(켜다)로 여기서는 맞지 않습니다.',
  },
  {
    id: 'g11',
    section: 'grammar',
    promptJa: 'この店のケーキは高い（　）、おいしいです。',
    choices: ['し', 'から', 'のに', 'ても'],
    answerIndex: 0,
    explanationKo: '이유를 두 개 이상 나열할 때 ～し. "비싸기도 하고, 맛있기도 하다". のに는 역접, から는 단일 이유입니다.',
  },
  {
    id: 'g12',
    section: 'grammar',
    promptJa: '弟にへやのそうじを（　）。',
    choices: ['させました', 'されました', 'できました', 'なりました'],
    answerIndex: 0,
    explanationKo: '내가 동생에게 청소를 시킨 사역이므로 する의 사역형 させる의 과거 させました. "동생에게 청소를 시켰다".',
  },
  {
    id: 'g13',
    section: 'grammar',
    promptJa: '先生が来る前に、教室を（　）おきましょう。',
    choices: ['そうじして', 'そうじした', 'そうじする', 'そうじし'],
    answerIndex: 0,
    explanationKo: '"미리 ～해 두다"는 동사 て형 + おく. 「そうじしておく」= 미리 청소해 두다. て형 접속이 필요합니다.',
  },

  // ---------- 독해 추가 (33-36) ----------
  {
    id: 'r6',
    section: 'reading',
    passageJa:
      'あたらしいとしょかんが、駅の近くにできました。朝九時から夜八時まで開いています。日曜日は休みですが、土曜日は開いています。本を借りるときは、カードが必要です。カードは受付で作れます。',
    promptJa: 'このとしょかんについて、正しいものはどれですか。',
    choices: [
      '日曜日も開いている',
      '土曜日は休みだ',
      '本を借りるにはカードがいる',
      '夜十時まで開いている',
    ],
    answerIndex: 2,
    explanationKo: '"本を借りるときは、カードが必要です"라고 했으므로 책을 빌리려면 카드가 필요합니다. 일요일은 휴관, 토요일은 개관, 밤 8시까지입니다.',
  },
  {
    id: 'r7',
    section: 'reading',
    passageJa:
      'あたらしいとしょかんが、駅の近くにできました。朝九時から夜八時まで開いています。日曜日は休みですが、土曜日は開いています。本を借りるときは、カードが必要です。カードは受付で作れます。',
    promptJa: 'カードは、どこで作れますか。',
    choices: ['駅', '受付', '教室', '本屋'],
    answerIndex: 1,
    explanationKo: '"カードは受付で作れます"라고 나옵니다. 카드는 접수처(受付)에서 만들 수 있습니다.',
  },
  {
    id: 'r8',
    section: 'reading',
    passageJa:
      'きのう、友だちとやまにのぼりました。天気がよくて、山の上からまちがぜんぶ見えました。おべんとうを食べたあと、写真をたくさんとりました。かえりのバスは人が多くて、ずっと立っていました。すこしつかれましたが、とても楽しい一日でした。',
    promptJa: 'この人は、やまの上で何をしましたか。',
    choices: [
      'バスに乗った',
      'おべんとうを食べて写真をとった',
      '本を読んだ',
      '友だちとわかれた',
    ],
    answerIndex: 1,
    explanationKo: '"おべんとうを食べたあと、写真をたくさんとりました"라고 했으므로 산 위에서 도시락을 먹고 사진을 찍었습니다.',
  },
  {
    id: 'r9',
    section: 'reading',
    passageJa:
      'きのう、友だちとやまにのぼりました。天気がよくて、山の上からまちがぜんぶ見えました。おべんとうを食べたあと、写真をたくさんとりました。かえりのバスは人が多くて、ずっと立っていました。すこしつかれましたが、とても楽しい一日でした。',
    promptJa: 'かえりのバスは、どうでしたか。',
    choices: [
      '人がすくなくてすわれた',
      '人が多くてずっと立っていた',
      'こなかった',
      'とてもはやかった',
    ],
    answerIndex: 1,
    explanationKo: '"かえりのバスは人が多くて、ずっと立っていました"라고 했으므로 돌아오는 버스는 사람이 많아 계속 서 있었습니다.',
  },
];
