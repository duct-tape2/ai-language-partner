// Listening (듣기) content. Hear the Japanese (TTS), pick the correct Korean
// meaning. Mirrors Codex's practice-hub/listening comprehension shape
// (item + choices[{id,label}] + correctChoiceId), so it swaps to
// GET/POST /practice-hub/listening later without screen changes.
export type ListeningChoice = { id: string; label: string };
export type ListeningItem = {
  id: string;
  ja: string;
  reading: string;
  promptKo: string;
  choices: ListeningChoice[];
  correctChoiceId: string;
  noteKo: string;
  xpReward: number;
};

export const LISTENING_ITEMS: ListeningItem[] = [
  {
    id: 'listen_tired',
    ja: '今日めっちゃ疲れた。',
    reading: 'きょうめっちゃつかれた。',
    promptKo: '방금 들은 문장의 뜻은?',
    choices: [
      { id: 'choice_0', label: '오늘 너무 피곤했어' },
      { id: 'choice_1', label: '오늘 정말 즐거웠어' },
      { id: 'choice_2', label: '오늘 좀 배고파' },
    ],
    correctChoiceId: 'choice_0',
    noteKo: '疲れた(つかれた)=피곤하다. めっちゃ는 회화체 강조예요.',
    xpReward: 12,
  },
  {
    id: 'listen_rest',
    ja: 'ちょっと休もうかな。',
    reading: 'ちょっとやすもうかな。',
    promptKo: '방금 들은 문장의 뜻은?',
    choices: [
      { id: 'choice_0', label: '좀 쉬어야겠다' },
      { id: 'choice_1', label: '좀 걸어야겠다' },
      { id: 'choice_2', label: '좀 자야겠다' },
    ],
    correctChoiceId: 'choice_0',
    noteKo: '休む(やすむ)=쉬다. 寝る(자다)와 구분하세요.',
    xpReward: 12,
  },
  {
    id: 'listen_eat',
    ja: 'お腹すいた、何か食べよう。',
    reading: 'おなかすいた、なにかたべよう。',
    promptKo: '방금 들은 문장의 뜻은?',
    choices: [
      { id: 'choice_0', label: '배고파, 뭐 좀 먹자' },
      { id: 'choice_1', label: '목말라, 물 좀 마시자' },
      { id: 'choice_2', label: '졸려, 좀 자자' },
    ],
    correctChoiceId: 'choice_0',
    noteKo: 'お腹すいた=배고프다, 食べよう(たべよう)=먹자.',
    xpReward: 12,
  },
  {
    id: 'listen_cheer',
    ja: '明日も頑張ろうね。',
    reading: 'あしたもがんばろうね。',
    promptKo: '방금 들은 문장의 뜻은?',
    choices: [
      { id: 'choice_0', label: '내일도 힘내자' },
      { id: 'choice_1', label: '오늘은 그만 쉬자' },
      { id: 'choice_2', label: '이제 집에 가자' },
    ],
    correctChoiceId: 'choice_0',
    noteKo: '頑張ろう(がんばろう)=힘내자, 明日(あした)=내일.',
    xpReward: 12,
  },
];

export const LISTENING_TOTAL = LISTENING_ITEMS.length;
