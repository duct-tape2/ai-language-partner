// Local gamification economy (XP / levels / streak / quests / badges).
// Pure functions over a serializable state; the store persists it.

export type Quest = {
  id: string;
  label: string;
  target: number;
  progress: number;
  reward: number; // XP
};

export type Badge = { id: string; label: string; emoji: string };

export type GamState = {
  xp: number;
  lastActiveDate: string; // YYYY-MM-DD
  streakDays: number;
  streakFreezes: number;
  badgeIds: string[];
  questsDate: string;
  quests: Quest[];
};

export const ALL_BADGES: Badge[] = [
  { id: 'first_word', label: '첫 한마디', emoji: '🌱' },
  { id: 'first_card', label: '첫 복습 카드', emoji: '📇' },
  { id: 'streak_3', label: '3일 연속', emoji: '🔥' },
  { id: 'streak_7', label: '일주일 개근', emoji: '🗓' },
  { id: 'ten_cards', label: '카드 10장', emoji: '🗂' },
  { id: 'perfect', label: '완벽 발음', emoji: '⭐️' },
  { id: 'level_5', label: 'Lv.5 달성', emoji: '🏅' },
];

export function todayStr(now: Date = new Date()): string {
  // Local calendar day (not UTC) so the streak/quest boundary is local midnight
  // for the Korean (UTC+9) audience, not 09:00 KST.
  const p = (n: number) => String(n).padStart(2, '0');
  return `${now.getFullYear()}-${p(now.getMonth() + 1)}-${p(now.getDate())}`;
}

// Level curve: level n needs 100*n cumulative XP steps (gentle, legible).
export function levelForXp(xp: number): number {
  return Math.floor(Math.sqrt(xp / 50)) + 1;
}
export function xpForLevel(level: number): number {
  return 50 * (level - 1) * (level - 1);
}
export function levelProgress(xp: number): { level: number; into: number; span: number; pct: number } {
  const level = levelForXp(xp);
  const base = xpForLevel(level);
  const next = xpForLevel(level + 1);
  const span = next - base;
  const into = xp - base;
  return { level, into, span, pct: span > 0 ? into / span : 0 };
}

export function defaultQuests(date: string): Quest[] {
  return [
    { id: 'mission', label: '오늘의 미션 1개 끝내기', target: 1, progress: 0, reward: 30 },
    { id: 'shadow3', label: '따라 말하기 3번', target: 3, progress: 0, reward: 20 },
    { id: 'review2', label: '복습 카드 2장 채점', target: 2, progress: 0, reward: 20 },
  ];
}

export function initialGamState(now: Date = new Date()): GamState {
  const date = todayStr(now);
  return {
    xp: 0,
    lastActiveDate: date,
    streakDays: 1,
    streakFreezes: 1,
    badgeIds: [],
    questsDate: date,
    quests: defaultQuests(date),
  };
}

function daysBetween(a: string, b: string): number {
  const [ay, am, ad] = a.split('-').map(Number);
  const [by, bm, bd] = b.split('-').map(Number);
  const da = new Date(ay, am - 1, ad).getTime(); // local midnight
  const db = new Date(by, bm - 1, bd).getTime();
  return Math.round((db - da) / 86400000);
}

// Call once per app open. Advances streak, rolls daily quests, spends a freeze
// on a single missed day if available.
export function registerActivity(state: GamState, now: Date = new Date()): GamState {
  const date = todayStr(now);
  let next = { ...state };
  if (date !== state.lastActiveDate) {
    const gap = daysBetween(state.lastActiveDate, date);
    if (gap === 1) {
      next.streakDays = state.streakDays + 1;
    } else if (gap === 2 && state.streakFreezes > 0) {
      next.streakFreezes = state.streakFreezes - 1; // freeze covers the one missed day
      next.streakDays = state.streakDays + 1;
    } else if (gap > 1) {
      next.streakDays = 1; // streak broke
    }
    next.lastActiveDate = date;
  }
  if (next.questsDate !== date) {
    next.questsDate = date;
    next.quests = defaultQuests(date);
  }
  return awardStreakBadges(next);
}

export function addXp(state: GamState, amount: number): GamState {
  return awardLevelBadges({ ...state, xp: state.xp + amount });
}

export function bumpQuest(state: GamState, id: string, n = 1): { state: GamState; rewarded: number } {
  let rewarded = 0;
  const quests = state.quests.map((q) => {
    if (q.id !== id) return q;
    const wasDone = q.progress >= q.target;
    const progress = Math.min(q.target, q.progress + n);
    if (!wasDone && progress >= q.target) rewarded += q.reward;
    return { ...q, progress };
  });
  let next: GamState = { ...state, quests };
  if (rewarded > 0) next = addXp(next, rewarded);
  return { state: next, rewarded };
}

export function awardBadge(state: GamState, id: string): GamState {
  if (state.badgeIds.includes(id)) return state;
  return { ...state, badgeIds: [...state.badgeIds, id] };
}

function awardStreakBadges(state: GamState): GamState {
  let s = state;
  if (s.streakDays >= 3) s = awardBadge(s, 'streak_3');
  if (s.streakDays >= 7) s = awardBadge(s, 'streak_7');
  return s;
}

function awardLevelBadges(state: GamState): GamState {
  let s = state;
  if (levelForXp(s.xp) >= 5) s = awardBadge(s, 'level_5');
  return s;
}

export const XP = { speak: 10, save: 15, gradeReview: 8, mission: 30, perfect: 12 };
