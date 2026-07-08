// Roleplay (롤플레이) content. A situation + the partner's line; the learner
// figures out how to respond, then reveals a natural reply and practices saying
// it. Mirrors Codex's roleplay item (situationKo / coachLineJa / goalKo /
// suggestedReply) so it swaps to /practice-hub/roleplay later.
export type RoleplayItem = {
  id: string;
  title: string;
  situationKo: string; // the scene / context
  partnerJa: string; // coachLineJa — what the other person says
  partnerReading: string;
  goalKo: string; // what you should accomplish
  replyJa: string; // suggestedReply
  replyReading: string;
  replyKo: string;
  xpReward: number;
};

export const ROLEPLAY_ITEMS: RoleplayItem[] = [
  {
    id: 'rp_how_was_today',
    title: '친구와 하루 이야기',
    situationKo: '친구가 오늘 하루 어땠는지 물어봐요.',
    partnerJa: '今日はどうだった？',
    partnerReading: 'きょうはどうだった？',
    goalKo: '오늘 많이 피곤했다고 답해보세요.',
    replyJa: '今日めっちゃ疲れた。',
    replyReading: 'きょうめっちゃつかれた。',
    replyKo: '오늘 너무 피곤했어.',
    xpReward: 15,
  },
  {
    id: 'rp_hungry',
    title: '배고픈 친구',
    situationKo: '친구가 배고프냐고 물어봐요.',
    partnerJa: 'おなかすいた？',
    partnerReading: 'おなかすいた？',
    goalKo: '뭔가 먹자고 제안해보세요.',
    replyJa: 'うん、何か食べよう。',
    replyReading: 'うん、なにかたべよう。',
    replyKo: '응, 뭐 좀 먹자.',
    xpReward: 15,
  },
  {
    id: 'rp_cheer_up',
    title: '시험 앞둔 친구',
    situationKo: '친구가 내일 시험이라 걱정하고 있어요.',
    partnerJa: '明日テストなんだ…。',
    partnerReading: 'あしたテストなんだ…。',
    goalKo: '함께 힘내자고 응원해보세요.',
    replyJa: '大丈夫、一緒に頑張ろう！',
    replyReading: 'だいじょうぶ、いっしょにがんばろう！',
    replyKo: '괜찮아, 같이 힘내자!',
    xpReward: 15,
  },
];

export const ROLEPLAY_TOTAL = ROLEPLAY_ITEMS.length;
