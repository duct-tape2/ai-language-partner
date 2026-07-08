// Learning insights — pure derivations from LOCAL, on-device data only.
// Honest scope: everything here comes from this device's stored progress, the
// local gamification state, and the local SRS cards. There is NO aggregate or
// server-side analytics behind these numbers. Screens must label them as
// "내 학습 데이터" (my device's own record), not community/benchmark data.

import type { TodayProgress } from '../../../../packages/shared/src/types';

// Minimal shapes we actually read, so this stays testable without the full
// AppController. The store's real objects are structurally compatible.
export type InsightGamLike = { xp: number; streakDays: number };

// A single local SRS card. We only read its FSRS scheduling fields; the numeric
// `state` mirrors ts-fsrs State (0=New, 1=Learning, 2=Review, 3=Relearning).
export type InsightSrsCardLike = {
  fsrs: { state: number; stability?: number; reps?: number; lapses?: number; due: string | Date };
};

export type InsightInput = {
  progress: TodayProgress;
  gam: InsightGamLike;
  srsCards: InsightSrsCardLike[];
  dueCards: { length: number }[] | { length: number };
  dailyGoal: number;
  level: number;
  levelPct: number; // 0..1
};

// One stat tile in the dashboard grid.
export type InsightStat = {
  key: string;
  label: string; // KO
  value: string; // formatted, unit-bearing
  hint?: string; // KO, one short line
  accent?: boolean;
};

// SRS maturity buckets derived from local FSRS state.
export type SrsMaturity = {
  total: number;
  fresh: number; // New / not yet studied
  learning: number; // Learning or Relearning, or low stability
  maturing: number; // Review with modest stability
  mature: number; // Review with strong stability
  due: number; // due for review now
};

// A tappable improvement suggestion pointing at an in-app destination.
export type InsightSuggestion = {
  key: string;
  title: string; // KO, imperative
  body: string; // KO, one line reason
  cta: string; // KO button-ish label
  target: 'review' | 'dailytalk' | 'hub' | 'home';
  tone: 'accent' | 'good' | 'near';
};

export type Insights = {
  goalPct: number; // 0..1
  spokenToday: number;
  dailyGoal: number;
  goalMet: boolean;
  streakDays: number;
  spokenTotal: number; // cumulative spoken sentences (this session/device)
  reviewCardsSaved: number;
  dueCount: number;
  level: number;
  levelPct: number; // 0..1
  xp: number;
  maturity: SrsMaturity;
  stats: InsightStat[];
  suggestions: InsightSuggestion[];
  // Honest flags about data scope.
  isLocalOnly: true;
  hasDailyHistory: false;
};

function clamp01(n: number): number {
  if (!Number.isFinite(n)) return 0;
  return Math.min(1, Math.max(0, n));
}

function dueLength(due: InsightInput['dueCards']): number {
  if (Array.isArray(due)) return due.length;
  return typeof due?.length === 'number' ? due.length : 0;
}

// Bucket local SRS cards into maturity tiers using their FSRS state + stability.
// Stability is "interval (days) at 90% recall"; thresholds are legible, not
// tuned science: <7d learning, 7-21d maturing, >21d mature.
export function computeMaturity(cards: InsightSrsCardLike[], now: Date = new Date()): SrsMaturity {
  let fresh = 0;
  let learning = 0;
  let maturing = 0;
  let mature = 0;
  let due = 0;
  for (const c of cards) {
    const f = c.fsrs;
    const stability = typeof f.stability === 'number' ? f.stability : 0;
    if (new Date(f.due).getTime() <= now.getTime()) due += 1;
    if (f.state === 0) {
      fresh += 1;
    } else if (f.state === 1 || f.state === 3) {
      learning += 1;
    } else if (stability >= 21) {
      mature += 1;
    } else if (stability >= 7) {
      maturing += 1;
    } else {
      learning += 1;
    }
  }
  return { total: cards.length, fresh, learning, maturing, mature, due };
}

// 2-3 improvement suggestions, ordered by what would help most right now.
export function buildSuggestions(input: {
  goalMet: boolean;
  spokenToday: number;
  dailyGoal: number;
  dueCount: number;
  reviewCardsSaved: number;
  streakDays: number;
}): InsightSuggestion[] {
  const { goalMet, spokenToday, dailyGoal, dueCount, reviewCardsSaved, streakDays } = input;
  const out: InsightSuggestion[] = [];

  // Backlog of due reviews is the highest-leverage fix.
  if (dueCount >= 5) {
    out.push({
      key: 'clear_due',
      title: '복습 대기부터 정리해요',
      body: `복습 대기 ${dueCount}장이 쌓였어요. 지금 채점하면 기억이 굳어져요.`,
      cta: '복습하러 가기',
      target: 'review',
      tone: 'near',
    });
  } else if (dueCount > 0) {
    out.push({
      key: 'do_due',
      title: '복습 대기 비우기',
      body: `복습 대기 ${dueCount}장이 있어요. 몇 분이면 끝나요.`,
      cta: '복습하기',
      target: 'review',
      tone: 'accent',
    });
  }

  // Low speaking volume -> nudge toward conversation practice.
  if (!goalMet) {
    const left = Math.max(0, dailyGoal - spokenToday);
    out.push({
      key: 'speak_more',
      title: spokenToday === 0 ? '오늘 첫 문장 말하기' : '오늘 목표 채우기',
      body:
        spokenToday === 0
          ? '오늘 아직 말한 문장이 없어요. 일상대화 한 마디로 시작해요.'
          : `목표까지 ${left}문장 남았어요. 일상대화로 채워봐요.`,
      cta: '일상대화 열기',
      target: 'dailytalk',
      tone: 'accent',
    });
  }

  // Few saved cards -> encourage building the review deck via practice hub.
  if (reviewCardsSaved < 3) {
    out.push({
      key: 'build_deck',
      title: '복습 카드 만들기',
      body: '저장된 복습 카드가 적어요. 연습에서 카드를 모으면 기억에 오래 남아요.',
      cta: '연습 허브 열기',
      target: 'hub',
      tone: 'good',
    });
  }

  // Everything healthy -> keep the streak going.
  if (out.length === 0) {
    out.push({
      key: 'keep_streak',
      title: '이 흐름 유지하기',
      body:
        streakDays >= 2
          ? `${streakDays}일 연속이에요. 오늘도 짧게라도 이어가요.`
          : '밀린 것도 없고 목표도 채웠어요. 오늘 연속 기록을 시작해요.',
      cta: '연습 계속하기',
      target: 'hub',
      tone: 'good',
    });
  }

  return out.slice(0, 3);
}

function buildStats(i: {
  goalPct: number;
  spokenToday: number;
  dailyGoal: number;
  streakDays: number;
  spokenTotal: number;
  reviewCardsSaved: number;
  dueCount: number;
  level: number;
  xp: number;
  maturity: SrsMaturity;
}): InsightStat[] {
  return [
    {
      key: 'goal',
      label: '오늘 목표 달성률',
      value: `${Math.round(i.goalPct * 100)}%`,
      hint: `${i.spokenToday} / ${i.dailyGoal}문장`,
      accent: true,
    },
    { key: 'streak', label: '연속일', value: `${i.streakDays}일`, accent: true },
    { key: 'spokenTotal', label: '누적 말한 문장', value: `${i.spokenTotal}문장` },
    { key: 'saved', label: '복습 카드', value: `${i.reviewCardsSaved}장` },
    { key: 'due', label: '복습 대기', value: `${i.dueCount}장`, hint: i.dueCount > 0 ? '지금 복습 가능' : '밀린 것 없음' },
    { key: 'mature', label: 'SRS 성숙 카드', value: `${i.maturity.mature}장`, hint: `학습중 ${i.maturity.learning}장` },
    { key: 'level', label: '레벨', value: `Lv.${i.level}` },
    { key: 'xp', label: '누적 XP', value: `${i.xp} XP` },
  ];
}

export function buildInsights(input: InsightInput, now: Date = new Date()): Insights {
  const goal = Math.max(1, input.dailyGoal);
  const spokenToday = Math.max(0, input.progress.spokenSentenceCount);
  const goalPct = clamp01(spokenToday / goal);
  const goalMet = spokenToday >= goal;
  const reviewCardsSaved = input.srsCards.length;
  const dueCount = dueLength(input.dueCards);
  const maturity = computeMaturity(input.srsCards, now);
  const streakDays = input.gam.streakDays;
  // spokenSentenceCount is today's counter; use it as the best available proxy
  // for cumulative spoken volume on this device (no lifetime counter is stored).
  const spokenTotal = Math.max(0, input.progress.spokenSentenceCount);

  const stats = buildStats({
    goalPct,
    spokenToday,
    dailyGoal: goal,
    streakDays,
    spokenTotal,
    reviewCardsSaved,
    dueCount,
    level: input.level,
    xp: input.gam.xp,
    maturity,
  });

  const suggestions = buildSuggestions({
    goalMet,
    spokenToday,
    dailyGoal: goal,
    dueCount,
    reviewCardsSaved,
    streakDays,
  });

  return {
    goalPct,
    spokenToday,
    dailyGoal: goal,
    goalMet,
    streakDays,
    spokenTotal,
    reviewCardsSaved,
    dueCount,
    level: input.level,
    levelPct: clamp01(input.levelPct),
    xp: input.gam.xp,
    maturity,
    stats,
    suggestions,
    isLocalOnly: true,
    hasDailyHistory: false,
  };
}
