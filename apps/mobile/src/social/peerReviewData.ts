// Peer correction (커뮤니티 교정) seed data. There is NO real social backend yet,
// so these represent other learners' recorded answers you can review. Each item is
// hand-authored with a realistic Korean-learner mistake in the Japanese answer, so
// the correction LOOP (rate 3 axes -> see suggested fix) is exercised honestly.
// This is DEMO data; screens must surface a '데모' note. Swaps to a real
// GET /community/peer-answers feed later.
import type { FuriToken } from '../i18n';

export type PeerReviewIssues = {
  naturalness: 1 | 2 | 3; // 별점 기본값 (1 낮음 ~ 3 자연스러움)
  pronunciation: 1 | 2 | 3;
  grammar: 1 | 2 | 3;
};

export type PeerReviewItem = {
  id: string;
  promptKo: string; // 상황 (what they were asked to say, in Korean)
  targetJa: string; // 모범답안 (the model / natural answer)
  tokens: FuriToken[]; // 모범답안 furigana tokens for FuriganaTokens
  learnerName: string; // pseudonymous other learner
  learnerAnswerJa: string; // what the learner actually said (contains a real mistake)
  issues: PeerReviewIssues; // suggested starting ratings on the 3 axes
  suggestedFixJa: string; // the corrected sentence
  suggestedFixKo: string; // Korean explanation of the fix
};

export const PEER_REVIEW_ITEMS: PeerReviewItem[] = [
  {
    id: 'pr_cafe_order',
    promptKo: '카페에서 아이스 아메리카노 한 잔을 주문해 보세요.',
    targetJa: 'アイスアメリカーノを一つください。',
    tokens: [
      { b: 'アイスアメリカーノ' },
      { b: 'を' },
      { b: '一', r: 'ひと' },
      { b: 'つ' },
      { b: 'ください' },
    ],
    learnerName: '민준',
    learnerAnswerJa: 'アイスアメリカーノを一個ください。',
    issues: { naturalness: 2, pronunciation: 3, grammar: 2 },
    suggestedFixJa: 'アイスアメリカーノを一つください。',
    suggestedFixKo: '음료를 셀 때는 「一個(いっこ)」보다 「一つ(ひとつ)」가 자연스러워요. 「一個」는 작은 물건에 주로 써요.',
  },
  {
    id: 'pr_self_intro',
    promptKo: '처음 만난 사람에게 자기소개를 하며 잘 부탁한다고 말해 보세요.',
    targetJa: 'はじめまして。どうぞよろしくお願いします。',
    tokens: [
      { b: 'はじめまして' },
      { b: '。' },
      { b: 'どうぞ' },
      { b: 'よろしく' },
      { b: 'お' },
      { b: '願', r: 'ねが' },
      { b: 'いします' },
    ],
    learnerName: '서연',
    learnerAnswerJa: 'はじめまして。よろしくおねがいするます。',
    issues: { naturalness: 2, pronunciation: 2, grammar: 1 },
    suggestedFixJa: 'はじめまして。どうぞよろしくお願いします。',
    suggestedFixKo: '「するます」는 없는 형태예요. 「する」의 정중형은 「します」. 「お願いします」로 붙여 써요.',
  },
  {
    id: 'pr_directions',
    promptKo: '역까지 가는 길을 물어보세요.',
    targetJa: '駅まではどう行けばいいですか。',
    tokens: [
      { b: '駅', r: 'えき' },
      { b: 'まで' },
      { b: 'は' },
      { b: 'どう' },
      { b: '行', r: 'い' },
      { b: 'けば' },
      { b: 'いいですか' },
    ],
    learnerName: '지호',
    learnerAnswerJa: '駅までどうやって行くますか。',
    issues: { naturalness: 2, pronunciation: 3, grammar: 1 },
    suggestedFixJa: '駅まではどう行けばいいですか。',
    suggestedFixKo: '「行くます」는 틀린 활용이에요. 「行く」의 정중형은 「行きます」. 길을 물을 때는 「どう行けばいいですか」가 훨씬 자연스러워요.',
  },
  {
    id: 'pr_weekend_plan',
    promptKo: '주말에 무엇을 할 계획인지 말해 보세요.',
    targetJa: '週末は友だちと映画を見に行くつもりです。',
    tokens: [
      { b: '週末', r: 'しゅうまつ' },
      { b: 'は' },
      { b: '友', r: 'とも' },
      { b: 'だちと' },
      { b: '映画', r: 'えいが' },
      { b: 'を' },
      { b: '見', r: 'み' },
      { b: 'に' },
      { b: '行', r: 'い' },
      { b: 'くつもりです' },
    ],
    learnerName: '하은',
    learnerAnswerJa: '週末は友だちと映画を見に行く予定します。',
    issues: { naturalness: 2, pronunciation: 3, grammar: 2 },
    suggestedFixJa: '週末は友だちと映画を見に行くつもりです。',
    suggestedFixKo: '「予定します」는 어색해요. 계획을 말할 땐 「〜つもりです」나 「〜予定です」를 써요. 「見に行く」는 잘 썼어요!',
  },
  {
    id: 'pr_apology_late',
    promptKo: '약속에 늦어서 사과해 보세요.',
    targetJa: '遅れてすみません。',
    tokens: [
      { b: '遅', r: 'おく' },
      { b: 'れて' },
      { b: 'すみません' },
    ],
    learnerName: '도윤',
    learnerAnswerJa: '遅いですごめんなさい。',
    issues: { naturalness: 1, pronunciation: 3, grammar: 2 },
    suggestedFixJa: '遅れてすみません。',
    suggestedFixKo: '「遅いです」는 "느리다"는 뜻이라 상황과 안 맞아요. 늦은 것을 사과할 땐 「遅れてすみません」이라고 해요.',
  },
  {
    id: 'pr_restaurant_reco',
    promptKo: '점원에게 이 가게에서 추천 메뉴가 뭔지 물어보세요.',
    targetJa: 'おすすめは何ですか。',
    tokens: [
      { b: 'おすすめ' },
      { b: 'は' },
      { b: '何', r: 'なん' },
      { b: 'ですか' },
    ],
    learnerName: '수아',
    learnerAnswerJa: 'おすすめは何ありますか。',
    issues: { naturalness: 2, pronunciation: 3, grammar: 2 },
    suggestedFixJa: 'おすすめは何ですか。',
    suggestedFixKo: '「何ありますか」는 조사가 빠졌어요. 「おすすめは何ですか」가 자연스럽고, 「おすすめは何がありますか」도 괜찮아요.',
  },
  {
    id: 'pr_feeling_tired',
    promptKo: '친구에게 오늘 너무 피곤하다고 말해 보세요.',
    targetJa: '今日はめっちゃ疲れた。',
    tokens: [
      { b: '今日', r: 'きょう' },
      { b: 'は' },
      { b: 'めっちゃ' },
      { b: '疲', r: 'つか' },
      { b: 'れた' },
    ],
    learnerName: '예준',
    learnerAnswerJa: '今日はとても疲れました。',
    issues: { naturalness: 2, pronunciation: 3, grammar: 3 },
    suggestedFixJa: '今日はめっちゃ疲れた。',
    suggestedFixKo: '문법은 맞지만 친구 사이엔 너무 딱딱해요. 반말로 「今日はめっちゃ疲れた」라고 하면 훨씬 친근해요.',
  },
  {
    id: 'pr_asking_price',
    promptKo: '가게에서 이거 얼마냐고 물어보세요.',
    targetJa: 'これはいくらですか。',
    tokens: [
      { b: 'これ' },
      { b: 'は' },
      { b: 'いくら' },
      { b: 'ですか' },
    ],
    learnerName: '지우',
    learnerAnswerJa: 'これはいくらお金ですか。',
    issues: { naturalness: 2, pronunciation: 3, grammar: 2 },
    suggestedFixJa: 'これはいくらですか。',
    suggestedFixKo: '「いくら」에 이미 "얼마"라는 뜻이 있어서 「お金」은 빼야 해요. 「これはいくらですか」로 충분해요.',
  },
  {
    id: 'pr_can_i_have',
    promptKo: '물 한 잔만 달라고 정중하게 부탁해 보세요.',
    targetJa: 'お水を一杯もらえますか。',
    tokens: [
      { b: 'お' },
      { b: '水', r: 'みず' },
      { b: 'を' },
      { b: '一杯', r: 'いっぱい' },
      { b: 'もらえますか' },
    ],
    learnerName: '채원',
    learnerAnswerJa: 'お水を一杯くれる？',
    issues: { naturalness: 2, pronunciation: 3, grammar: 2 },
    suggestedFixJa: 'お水を一杯もらえますか。',
    suggestedFixKo: '「くれる？」는 너무 반말이라 점원에겐 실례가 될 수 있어요. 정중하게는 「もらえますか」를 써요.',
  },
];

export const PEER_REVIEW_TOTAL = PEER_REVIEW_ITEMS.length;

// Prompts the user can pick in the '내 답변' demo tab (record + share is 데모).
export const MY_ANSWER_PROMPTS = PEER_REVIEW_ITEMS.map((it) => ({
  id: it.id,
  promptKo: it.promptKo,
  targetJa: it.targetJa,
  tokens: it.tokens,
}));
