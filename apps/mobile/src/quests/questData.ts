// Daily quest definitions for the retention economy.
//
// HONEST SCOPE: these are local goals derived from today's on-device progress
// (app.progress). There are NO real reward transactions here - completing a
// quest does not grant XP, gems, or unlock anything on a server. The optional
// server-backed quests live in app.serverGam?.dailyQuests (see DailyQuest type
// in @shared/types); DailyQuestScreen prefers those when present and falls back
// to this local set otherwise.

export type QuestKey =
  | 'speak'
  | 'review'
  | 'newPattern'
  | 'listening';

export type QuestDef = {
  key: QuestKey;
  labelKo: string;
  target: number;
  icon: string; // emoji, ASCII-safe source (the emoji itself is a string literal)
  tip: string; // KO one-line encouragement / how-to
};

export type BuiltQuest = QuestDef & {
  current: number; // computed from today's progress
  done: boolean;
  navTarget: 'dailytalk' | 'review' | 'hub' | 'choukai';
};

// Local progress shape we read from (subset of app.progress). Kept structural so
// this file has no import dependency on the store.
export type QuestProgress = {
  spokenSentenceCount: number;
  reviewCardsCreated: number;
  completedMissions: number;
};

// Where each quest sends the learner when tapped.
const NAV: Record<QuestKey, BuiltQuest['navTarget']> = {
  speak: 'dailytalk',
  review: 'review',
  newPattern: 'hub',
  listening: 'choukai',
};

export const DEFAULT_QUESTS: QuestDef[] = [
  {
    key: 'speak',
    labelKo: '문장 5개 말하기',
    target: 5,
    icon: '🗣',
    tip: '오늘의 대화에서 소리 내어 5문장만 말해보세요.',
  },
  {
    key: 'review',
    labelKo: '복습 카드 3장',
    target: 3,
    icon: '🃏',
    tip: '틀린 문장을 카드로 저장하면 오래 기억돼요.',
  },
  {
    key: 'newPattern',
    labelKo: '새 문형 2개',
    target: 2,
    icon: '🧩',
    tip: '연습 허브에서 새로운 문형을 익혀보세요.',
  },
  {
    key: 'listening',
    labelKo: '청해 1회',
    target: 1,
    icon: '🎧',
    tip: '짧은 청해 한 세트로 귀를 열어보세요.',
  },
];

// Map a quest to its current value from today's local progress.
// NOTE: the on-device progress object only tracks spokenSentenceCount,
// reviewCardsCreated, and completedMissions. There is no separate
// per-skill counter yet, so "새 문형" and "청해" both read completedMissions
// as an honest proxy (any completed mission counts). This is a local
// approximation, not a server-verified metric.
function currentFor(def: QuestDef, p: QuestProgress): number {
  switch (def.key) {
    case 'speak':
      return p.spokenSentenceCount;
    case 'review':
      return p.reviewCardsCreated;
    case 'newPattern':
      return p.completedMissions;
    case 'listening':
      return p.completedMissions;
    default:
      return 0;
  }
}

// Build the local quest list with computed progress. `progress` is app.progress.
export function buildQuests(progress: QuestProgress): BuiltQuest[] {
  return DEFAULT_QUESTS.map((def) => {
    const current = Math.max(0, currentFor(def, progress));
    return {
      ...def,
      current,
      done: current >= def.target,
      navTarget: NAV[def.key],
    };
  });
}

// Explainer strings (KO). These describe features honestly as either available
// or not-yet-built, so the UI never implies a reward that does not exist.
export const STREAK_REPAIR_INFO =
  '스트릭 프리즈/리페어(하루 빠져도 연속 기록 지키기)는 준비 중이에요. 지금은 매일 한 문장이라도 말하면 연속일이 이어져요.';

export const RETURN_BONUS_INFO =
  '복귀 보너스(오래 쉬었다 돌아오면 가볍게 다시 시작하도록 목표를 낮춰주는 기능)도 준비 중이에요. 지금은 실제 보상 지급 없이 목표와 응원만 드려요.';
