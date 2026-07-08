// Client-side spaced-repetition using the open FSRS algorithm (ts-fsrs).
// No backend: each card carries its own FSRS scheduling state, persisted in
// AsyncStorage. This is the scheduling "brain" the leader (kana-dojo) lacks.
import {
  createEmptyCard,
  fsrs,
  generatorParameters,
  Rating,
  type Card as FsrsCard,
  type Grade as FsrsGrade,
} from 'ts-fsrs';
import type { ReviewCard } from '../../../packages/shared/src/types';

const engine = fsrs(generatorParameters({ enable_fuzz: true }));

export type Grade = 'again' | 'hard' | 'good' | 'easy';

const RATING: Record<Grade, FsrsGrade> = {
  again: Rating.Again,
  hard: Rating.Hard,
  good: Rating.Good,
  easy: Rating.Easy,
};

// A review card plus its FSRS scheduling state, as stored locally.
export type SrsCard = ReviewCard & { fsrs: FsrsCard; addedAt: string };

// ts-fsrs Card holds Date objects; revive them after JSON round-trips.
function reviveDates(c: FsrsCard): FsrsCard {
  return {
    ...c,
    due: new Date(c.due),
    last_review: c.last_review ? new Date(c.last_review) : undefined,
  } as FsrsCard;
}

export function makeSrsCard(card: ReviewCard, now: Date = new Date()): SrsCard {
  return { ...card, fsrs: createEmptyCard(now), addedAt: now.toISOString() };
}

export function gradeSrsCard(card: SrsCard, grade: Grade, now: Date = new Date()): SrsCard {
  const fsrsState = reviveDates(card.fsrs);
  const next = engine.next(fsrsState, now, RATING[grade]).card;
  return { ...card, fsrs: next };
}

export function isDue(card: SrsCard, now: Date = new Date()): boolean {
  return new Date(card.fsrs.due).getTime() <= now.getTime();
}

export function dueCount(cards: SrsCard[], now: Date = new Date()): number {
  return cards.filter((c) => isDue(c, now)).length;
}

// Human label for the next interval a given grade would produce, e.g. "10분", "1일".
export function previewIntervalLabel(card: SrsCard, grade: Grade, now: Date = new Date()): string {
  const next = engine.next(reviveDates(card.fsrs), now, RATING[grade]).card;
  const ms = new Date(next.due).getTime() - now.getTime();
  return humanInterval(ms);
}

export function humanInterval(ms: number): string {
  const min = Math.round(ms / 60000);
  if (min < 60) return `${Math.max(1, min)}분`;
  const hr = Math.round(min / 60);
  if (hr < 24) return `${hr}시간`;
  const day = Math.round(hr / 24);
  if (day < 30) return `${day}일`;
  const mon = Math.round(day / 30);
  if (mon < 12) return `${mon}개월`;
  return `${Math.round(mon / 12)}년`;
}

export function reviveCards(cards: SrsCard[]): SrsCard[] {
  return cards.map((c) => ({ ...c, fsrs: reviveDates(c.fsrs) }));
}
