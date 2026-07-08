// Hand-authored JLPT N5 mock exam (20 questions). Easier companion set to the N4
// paper. No network fetch — the data ships with the app. Sections mirror the real
// N5 paper: 문자·어휘 (kanji reading / word meaning), 문법 (grammar), 독해 (short
// passage + comprehension question).
//
// Shape is identical to the N4 exam (examData.ts) so the screen can reuse the same
// rendering. promptTokens drives FuriganaTokens; passageJa is the short reading text;
// answerIndex is 0-based into choices (always 4 options). Kept self-contained: this
// file does not import from examData.ts.

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
export const N5_PASS_RATIO = 0.6;

export const SECTION_LABEL_N5: Record<ExamSection, string> = {
  vocab: '문자·어휘',
  grammar: '문법',
  reading: '독해',
};

export const MOCK_EXAM_N5: ExamQuestion[] = [
  // ---------- 문자·어휘 (1-8) ----------
  {
    id: 'n5v1',
    section: 'vocab',
    promptJa: 'まいにち、水をのみます。',
    promptTokens: [
      { b: 'まいにち' },
      { b: '、' },
      { b: '水', r: 'みず' },
      { b: 'を' },
      { b: 'のみます' },
      { b: '。' },
    ],
    choices: ['みず', 'みづ', 'すい', 'みす'],
    answerIndex: 0,
    explanationKo: '水(みず)는 "물". 단독으로 쓸 때는 훈독 みず로 읽습니다. すい는 水よう日(수요일) 같은 음독 낱말에 쓰입니다.',
  },
  {
    id: 'n5v2',
    section: 'vocab',
    promptJa: 'きょうは山にのぼります。',
    promptTokens: [
      { b: 'きょうは' },
      { b: '山', r: 'やま' },
      { b: 'に' },
      { b: 'のぼります' },
      { b: '。' },
    ],
    choices: ['やま', 'かわ', 'さん', 'いし'],
    answerIndex: 0,
    explanationKo: '山(やま)는 "산". 단독 낱말은 훈독 やま로 읽습니다. さん은 富士山(ふじさん)처럼 음독 낱말에 쓰입니다.',
  },
  {
    id: 'n5v3',
    section: 'vocab',
    promptJa: 'ともだちと学校へ行きます。',
    promptTokens: [
      { b: 'ともだちと' },
      { b: '学', r: 'がっ' },
      { b: '校', r: 'こう' },
      { b: 'へ' },
      { b: '行', r: 'い' },
      { b: 'きます' },
      { b: '。' },
    ],
    choices: ['がっこう', 'がくこう', 'がっこ', 'かっこう'],
    answerIndex: 0,
    explanationKo: '学校(がっこう)는 "학교". 学+校가 이어질 때 촉음화되어 がっこう로 읽습니다.',
  },
  {
    id: 'n5v4',
    section: 'vocab',
    promptJa: '木の下でやすみます。',
    promptTokens: [
      { b: '木', r: 'き' },
      { b: 'の' },
      { b: '下', r: 'した' },
      { b: 'で' },
      { b: 'やすみます' },
      { b: '。' },
    ],
    choices: ['した', 'うえ', 'なか', 'そと'],
    answerIndex: 0,
    explanationKo: '下(した)는 "아래". うえ=위, なか=안, そと=밖. 나무 아래에서 쉰다는 뜻입니다.',
  },
  {
    id: 'n5v5',
    section: 'vocab',
    promptJa: 'あついので、（　）をあけます。',
    choices: ['まど', 'いす', 'つくえ', 'かばん'],
    answerIndex: 0,
    explanationKo: '더워서 여는 것은 まど(창문)입니다. いす=의자, つくえ=책상, かばん=가방으로 문맥에 맞지 않습니다.',
  },
  {
    id: 'n5v6',
    section: 'vocab',
    promptJa: 'このりんごは（　）です。',
    choices: ['あかい', 'たかい', 'ながい', 'はやい'],
    answerIndex: 0,
    explanationKo: 'りんご(사과)의 색을 나타내는 형용사는 あかい(빨갛다)가 자연스럽습니다. たかい=비싸다/높다, ながい=길다, はやい=빠르다.',
  },
  {
    id: 'n5v7',
    section: 'vocab',
    promptJa: 'あさ、かおを（　）。',
    choices: ['あらいます', 'たべます', 'ききます', 'よみます'],
    answerIndex: 0,
    explanationKo: 'かお(얼굴)와 어울리는 동사는 あらう(씻다). "얼굴을 씻습니다". たべる=먹다, きく=듣다, よむ=읽다.',
  },
  {
    id: 'n5v8',
    section: 'vocab',
    promptJa: 'この本は（　）です。ぜんぶよめました。',
    choices: ['やさしい', 'むずかしい', 'おもい', 'せまい'],
    answerIndex: 0,
    explanationKo: '"전부 읽을 수 있었다"와 이어지려면 쉬웠다는 뜻이 자연스럽습니다. やさしい=쉽다. むずかしい=어렵다, おもい=무겁다, せまい=좁다.',
  },

  // ---------- 문법 (9-15) ----------
  {
    id: 'n5g1',
    section: 'grammar',
    promptJa: 'つくえの上（　）本があります。',
    choices: ['に', 'を', 'へ', 'と'],
    answerIndex: 0,
    explanationKo: '사물이 있는 장소를 나타낼 때는 ～に + あります. "책상 위에 책이 있습니다". を는 목적, へ는 방향, と는 나열입니다.',
  },
  {
    id: 'n5g2',
    section: 'grammar',
    promptJa: 'わたしは まいあさ コーヒー（　）のみます。',
    choices: ['を', 'に', 'が', 'で'],
    answerIndex: 0,
    explanationKo: 'のむ(마시다)의 목적어에는 조사 を. "커피를 마십니다". 타동사의 대상은 を로 표시합니다.',
  },
  {
    id: 'n5g3',
    section: 'grammar',
    promptJa: 'きのうは あめ（　）ふりませんでした。',
    choices: ['が', 'を', 'に', 'へ'],
    answerIndex: 0,
    explanationKo: 'ふる(내리다)는 자동사라 주어를 が로 표시합니다. "비가 내리지 않았습니다".',
  },
  {
    id: 'n5g4',
    section: 'grammar',
    promptJa: 'A「ここに 犬が いますか。」 B「いいえ、（　）。」',
    choices: ['いません', 'ありません', 'います', 'あります'],
    answerIndex: 0,
    explanationKo: '犬(개)는 생물이므로 いる를 씁니다. 없다는 부정은 いません. 무생물에는 ありません을 씁니다.',
  },
  {
    id: 'n5g5',
    section: 'grammar',
    promptJa: 'この へやは あかるくて（　）です。',
    choices: ['きれい', 'きれいだ', 'きれいに', 'きれいで'],
    answerIndex: 0,
    explanationKo: '형용동사가 문장 끝에서 です와 이어질 때는 어간 + です. 「きれいです」가 맞고, きれいだです처럼 だ를 붙이지 않습니다.',
  },
  {
    id: 'n5g6',
    section: 'grammar',
    promptJa: 'あした ともだちと えいがを（　）。',
    choices: ['みます', 'みました', 'みています', 'みません'],
    answerIndex: 0,
    explanationKo: 'あした(내일)는 미래이므로 미래·현재형 みます가 맞습니다. みました는 과거라 시제가 맞지 않습니다.',
  },
  {
    id: 'n5g7',
    section: 'grammar',
    promptJa: 'テストの まえに、たくさん（　）ください。',
    choices: ['べんきょうして', 'べんきょうする', 'べんきょうし', 'べんきょうした'],
    answerIndex: 0,
    explanationKo: '"～해 주세요"는 동사 て형 + ください. する의 て형은 して이므로 べんきょうしてください가 맞습니다.',
  },

  // ---------- 독해 (16-20) ----------
  {
    id: 'n5r1',
    section: 'reading',
    passageJa:
      'わたしの いえは えきから ちかいです。あるいて 五分ぐらいです。まいあさ、えきまで あるいて、でんしゃに のります。',
    promptJa: 'この人は、えきまで どうやって 行きますか。',
    choices: ['でんしゃで 行く', 'あるいて 行く', 'バスで 行く', 'くるまで 行く'],
    answerIndex: 1,
    explanationKo: '본문에 "えきまで あるいて"라고 나옵니다. 역까지는 걸어서 갑니다. 전철은 역에서 탑니다.',
  },
  {
    id: 'n5r2',
    section: 'reading',
    passageJa:
      'きょうは にちようびです。あさ、そうじを しました。ひるごはんを たべてから、こうえんで さんぽを しました。よるは 本を よみました。',
    promptJa: 'この人は、ひるごはんの あとに 何を しましたか。',
    choices: ['そうじを した', 'こうえんで さんぽを した', '本を よんだ', 'かいものを した'],
    answerIndex: 1,
    explanationKo: '"ひるごはんを たべてから、こうえんで さんぽを しました"라고 했으므로 점심 후에 공원에서 산책을 했습니다. 청소는 아침, 독서는 저녁입니다.',
  },
  {
    id: 'n5r3',
    section: 'reading',
    passageJa:
      'たなかさんへ\nあした いっしょに ひるごはんを たべませんか。十二時に 学校の 前で あいましょう。\nキム',
    promptJa: '二人は、どこで あいますか。',
    choices: ['えきの 前', '学校の 前', 'こうえん', 'レストラン'],
    answerIndex: 1,
    explanationKo: '메모에 "十二時に 学校の 前で あいましょう"라고 했으므로 학교 앞에서 만납니다.',
  },
  {
    id: 'n5r4',
    section: 'reading',
    passageJa:
      'わたしは ねこが 二ひき います。一ぴきは しろくて、一ぴきは くろいです。しろい ねこは よく ねます。くろい ねこは よく あそびます。',
    promptJa: 'くろい ねこは、どんな ねこですか。',
    choices: ['よく ねる', 'よく あそぶ', 'ごはんを たべない', 'そとに いる'],
    answerIndex: 1,
    explanationKo: '"くろい ねこは よく あそびます"라고 했으므로 검은 고양이는 잘 놉니다. 잘 자는 것은 흰 고양이입니다.',
  },
  {
    id: 'n5r5',
    section: 'reading',
    passageJa:
      'わたしは まいにち 六時に おきます。しごとは 九時から 五時までです。しごとの あと、ときどき ともだちと ばんごはんを たべます。',
    promptJa: 'この人の しごとは、何時に おわりますか。',
    choices: ['六時', '九時', '五時', '十二時'],
    answerIndex: 2,
    explanationKo: '"しごとは 九時から 五時まで"라고 했으므로 일은 5시에 끝납니다. 六時는 기상 시간, 九時는 시작 시간입니다.',
  },
];
