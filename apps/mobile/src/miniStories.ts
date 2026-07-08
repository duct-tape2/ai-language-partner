// Mini Story (맥락 이해 루프) content. Mirrors Codex's public story shape exactly
// (src/ai_language_partner: _public_story_item) so this swaps to the real
// GET/POST /practice-hub/stories endpoint without changing the screen:
//   { id, contextNote, promptKo, lines:[{speaker,text,reading}],
//     choices:[{id,label}], correctChoiceId, summaryKo, xpReward }
// `reading` is a full-line kana gloss (Codex supplies this per line). speaker is
// 'Learner' for the user's line, otherwise the partner's name.
export type StoryLine = { speaker: string; text: string; reading: string };
export type StoryChoice = { id: string; label: string };
export type MiniStory = {
  id: string;
  contextNote: string;
  promptKo: string;
  lines: StoryLine[];
  choices: StoryChoice[];
  correctChoiceId: string;
  summaryKo: string;
  xpReward: number;
};

export const MINI_STORIES: MiniStory[] = [
  {
    id: 'story_daily_tired',
    contextNote: '오늘 하루 어땠는지 짧은 대화 안에서 이해하기',
    promptKo: '학습자는 오늘 하루를 어떻게 느꼈나요?',
    lines: [
      { speaker: 'Yui', text: '今日はどうだった？', reading: 'きょうはどうだった？' },
      { speaker: 'Learner', text: '今日めっちゃ疲れた。', reading: 'きょうめっちゃつかれた。' },
      { speaker: 'Yui', text: 'そっか、ゆっくり休んでね。', reading: 'そっか、ゆっくりやすんでね。' },
    ],
    choices: [
      { id: 'choice_0', label: '아주 피곤했다' },
      { id: 'choice_1', label: '아주 신났다' },
      { id: 'choice_2', label: '배가 고팠다' },
    ],
    correctChoiceId: 'choice_0',
    summaryKo: "학습자는 '오늘 너무 피곤했어(今日めっちゃ疲れた)'라고 말했고, 유이가 푹 쉬라고 답했어요.",
    xpReward: 15,
  },
  {
    id: 'story_daily_food',
    contextNote: '배고플 때 표현을 대화 안에서 이해하기',
    promptKo: '두 사람은 이제 무엇을 하려고 하나요?',
    lines: [
      { speaker: 'Yui', text: 'おなかすいた？', reading: 'おなかすいた？' },
      { speaker: 'Learner', text: 'うん、何か食べよう。', reading: 'うん、なにかたべよう。' },
      { speaker: 'Yui', text: 'いいね、ラーメンにする？', reading: 'いいね、ラーメンにする？' },
    ],
    choices: [
      { id: 'choice_0', label: '뭔가 먹으려 한다' },
      { id: 'choice_1', label: '잠을 자려 한다' },
      { id: 'choice_2', label: '공부하려 한다' },
    ],
    correctChoiceId: 'choice_0',
    summaryKo: "학습자가 '뭐 좀 먹자(何か食べよう)'라고 했고, 유이가 라멘을 제안했어요.",
    xpReward: 15,
  },
  {
    id: 'story_daily_cheer',
    contextNote: '서로 응원하는 대화 이해하기',
    promptKo: '학습자는 내일에 대해 어떤 태도인가요?',
    lines: [
      { speaker: 'Yui', text: '明日もテストだよね。', reading: 'あしたもテストだよね。' },
      { speaker: 'Learner', text: 'うん、でも頑張ろうね。', reading: 'うん、でもがんばろうね。' },
      { speaker: 'Yui', text: 'うん、一緒に頑張ろう！', reading: 'うん、いっしょにがんばろう！' },
    ],
    choices: [
      { id: 'choice_0', label: '함께 힘내자는 태도' },
      { id: 'choice_1', label: '포기하려는 태도' },
      { id: 'choice_2', label: '시험이 없다고 생각' },
    ],
    correctChoiceId: 'choice_0',
    summaryKo: "학습자가 '내일도 힘내자(頑張ろうね)'라며 함께 응원하는 태도를 보였어요.",
    xpReward: 15,
  },
];

export const MINI_STORY_TOTAL = MINI_STORIES.length;
