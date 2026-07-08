// Weekly learning report — pure derivations from LOCAL data only.
// No backend, no daily history store exists yet, so anything "weekly" here is
// derived from today's snapshot + streak. Screens must label estimates honestly.

import type { TodayProgress } from '../../../../packages/shared/src/types';
import type { GamState } from '../gamification';
import type { SrsCard } from '../srs';

export type LevelBand = {
  key: 'seed' | 'sprout' | 'growing' | 'steady' | 'strong';
  label: string; // KO
  note: string; // KO, one line
};

export type WeeklyReport = {
  goalPct: number; // 0..1, today's spoken / dailyGoal
  spokenToday: number;
  dailyGoal: number;
  streakDays: number;
  reviewCardsSaved: number; // total saved cards
  dueCount: number; // cards due for review now
  reviewCoveragePct: number; // 0..1, (saved - due) / saved
  levelBand: LevelBand;
  encouragement: string[]; // 2-3 KO lines
  goalMet: boolean;
  hasDailyHistory: false; // honest flag: no per-day history is tracked yet
};

function clamp01(n: number): number {
  if (!Number.isFinite(n)) return 0;
  return Math.min(1, Math.max(0, n));
}

// Estimated level band from cumulative XP + streak. This is an in-app
// engagement band, NOT a JLPT level. Screens should present it as such.
export function estimateLevelBand(xp: number, streakDays: number): LevelBand {
  if (xp >= 1200 || streakDays >= 14) {
    return { key: 'strong', label: '탄탄한 습관', note: '학습 루틴이 자리 잡았어요.' };
  }
  if (xp >= 600 || streakDays >= 7) {
    return { key: 'steady', label: '꾸준한 페이스', note: '일주일 넘게 이어가는 중이에요.' };
  }
  if (xp >= 250 || streakDays >= 3) {
    return { key: 'growing', label: '자라는 중', note: '반복이 쌓이고 있어요.' };
  }
  if (xp >= 60) {
    return { key: 'sprout', label: '싹트는 중', note: '첫 습관이 만들어지고 있어요.' };
  }
  return { key: 'seed', label: '시작 단계', note: '첫 문장부터 가볍게 시작해요.' };
}

// 2-3 short Korean encouragement lines tuned to the current snapshot.
export function buildEncouragement(input: {
  goalMet: boolean;
  spokenToday: number;
  dailyGoal: number;
  streakDays: number;
  dueCount: number;
  reviewCardsSaved: number;
}): string[] {
  const { goalMet, spokenToday, dailyGoal, streakDays, dueCount, reviewCardsSaved } = input;
  const lines: string[] = [];

  if (goalMet) {
    lines.push(`오늘 목표 ${dailyGoal}문장을 채웠어요. 훌륭해요!`);
  } else if (spokenToday > 0) {
    const left = Math.max(0, dailyGoal - spokenToday);
    lines.push(`목표까지 ${left}문장 남았어요. 조금만 더!`);
  } else {
    lines.push('오늘 한 문장만 말해도 리포트가 채워져요.');
  }

  if (streakDays >= 7) {
    lines.push(`${streakDays}일 연속이에요. 이 흐름을 지켜봐요.`);
  } else if (streakDays >= 2) {
    lines.push(`${streakDays}일째 이어가는 중이에요. 내일도 이어가요.`);
  } else {
    lines.push('오늘부터 연속 기록을 만들어봐요.');
  }

  if (dueCount > 0) {
    lines.push(`복습 대기 ${dueCount}장이 기억을 굳혀줄 거예요.`);
  } else if (reviewCardsSaved > 0) {
    lines.push('밀린 복습이 없어요. 카드 관리가 깔끔해요.');
  }

  return lines.slice(0, 3);
}

// dailyGoal lives in settings (not in TodayProgress), so callers pass it in.
// It defaults to the app's default goal (5) to keep the ring divide-by-zero safe
// for callers that only hold progress.
export function buildReport(
  progress: TodayProgress,
  gam: GamState,
  srsCards: SrsCard[],
  dueCards: SrsCard[],
  dailyGoal = 5,
): WeeklyReport {
  const goal = Math.max(1, dailyGoal);
  const spokenToday = Math.max(0, progress.spokenSentenceCount);
  const goalPct = clamp01(spokenToday / goal);
  const goalMet = spokenToday >= goal;
  const reviewCardsSaved = srsCards.length;
  const dueCount = dueCards.length;
  const reviewCoveragePct =
    reviewCardsSaved > 0 ? clamp01((reviewCardsSaved - dueCount) / reviewCardsSaved) : 1;
  const levelBand = estimateLevelBand(gam.xp, progress.streakDays);
  const encouragement = buildEncouragement({
    goalMet,
    spokenToday,
    dailyGoal: goal,
    streakDays: progress.streakDays,
    dueCount,
    reviewCardsSaved,
  });

  return {
    goalPct,
    spokenToday,
    dailyGoal: goal,
    streakDays: progress.streakDays,
    reviewCardsSaved,
    dueCount,
    reviewCoveragePct,
    levelBand,
    encouragement,
    goalMet,
    hasDailyHistory: false,
  };
}
