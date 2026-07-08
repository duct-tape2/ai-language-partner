// Static skill map for the mastery dashboard. Ties the app's many learning
// modules together and drives the weak-area recommendation engine. Pure data +
// a deterministic recommendNext() helper; no backend, no side effects.
//
// navKey MUST be a valid store `Screen` value so app.navigate(navKey) stays
// type-safe. Only screens that exist in the Screen union are referenced here.
import type { Screen } from '../store';
import type { TodayProgress } from '../../../../packages/shared/src/types';

export type MasterySkill = {
  key: string;
  labelKo: string;
  icon: string;
  navKey: Screen;
  blurbKo: string;
  // Rough difficulty tier (1=foundation .. 3=advanced). Used to order the grid
  // and to bias early recommendations toward foundations.
  tier: 1 | 2 | 3;
};

// Ordered foundation -> advanced. Each entry maps to a real learning screen.
export const SKILLS: MasterySkill[] = [
  { key: 'kana', labelKo: '가나 (히라가나·가타카나)', icon: '🈂️', navKey: 'kanaChart', blurbKo: '모든 학습의 출발점. 46자 발음과 표를 눈에 익혀요.', tier: 1 },
  { key: 'kanji', labelKo: '한자', icon: '🈷️', navKey: 'kanji', blurbKo: '음훈독·부수·획수·니모닉으로 한자를 통째로 잡아요.', tier: 2 },
  { key: 'vocab', labelKo: '테마별 어휘', icon: '🗂️', navKey: 'vocab', blurbKo: '일상·음식·여행 등 주제별 100+ 단어를 묶어서 외워요.', tier: 1 },
  { key: 'grammar', labelKo: '문법 문형', icon: '📘', navKey: 'grammar', blurbKo: 'N5·N4 핵심 문형의 의미·접속·예문을 정리해요.', tier: 2 },
  { key: 'conjugation', labelKo: '활용', icon: '🔀', navKey: 'conjugation', blurbKo: '동사·형용사 활용을 반복 드릴로 손에 익혀요.', tier: 2 },
  { key: 'counters', labelKo: '조수사', icon: '🔢', navKey: 'counters', blurbKo: '개·명·마리처럼 세는 말의 읽기를 헷갈리지 않게 잡아요.', tier: 2 },
  { key: 'numbers', labelKo: '숫자·시간·날짜', icon: '🕐', navKey: 'numbers', blurbKo: '자주 틀리는 숫자·시각·날짜 읽기를 한번에 정리해요.', tier: 1 },
  { key: 'pitch', labelKo: '피치 악센트', icon: '🎵', navKey: 'pitch', blurbKo: '억양 패턴을 눈으로 보고 자연스러운 발음으로 굳혀요.', tier: 3 },
  { key: 'keigo', labelKo: '존댓말·경어', icon: '🙇', navKey: 'keigo', blurbKo: '존경어·겸양어를 상황별로 구분해서 써요.', tier: 3 },
  { key: 'dialogue', labelKo: '회화 섀도잉', icon: '🗣️', navKey: 'dialogueshadow', blurbKo: '실전 대화를 듣고 곧바로 따라 말하며 입에 붙여요.', tier: 3 },
  { key: 'dailytalk', labelKo: '일상 대화', icon: '💬', navKey: 'dailytalk', blurbKo: '실제 대화처럼 말하고 바로 답을 들으며 감을 키워요.', tier: 3 },
  { key: 'exam', labelKo: 'N4 모의고사', icon: '📝', navKey: 'exam', blurbKo: '20문항 실전 문제와 해설로 지금 실력을 점검해요.', tier: 3 },
  { key: 'reading', labelKo: '독해', icon: '📖', navKey: 'reading', blurbKo: '짧은 지문을 읽고 문제로 이해도를 확인해요.', tier: 2 },
  { key: 'pitfalls', labelKo: '자주 틀리는 표현', icon: '⚠️', navKey: 'pitfalls', blurbKo: '한국인이 헷갈리는 조사·경어·한자어를 바로잡아요.', tier: 2 },
  { key: 'pronunciation', labelKo: '발음 채점', icon: '🎙️', navKey: 'pronunciation', blurbKo: '문장을 읽고 발음 피드백으로 정확도를 높여요.', tier: 3 },
  { key: 'situations', labelKo: '상황별 표현', icon: '🧳', navKey: 'situations', blurbKo: '공항·호텔·식당 등 상황별 바로 쓰는 문장을 익혀요.', tier: 2 },
  { key: 'mistakes', labelKo: '오답노트', icon: '🔁', navKey: 'mistakes', blurbKo: '틀린 문제만 모아 다시 풀며 약점을 지워요.', tier: 2 },
];

// Convenience lookups for the dashboard grid / recommendation cards.
export const SKILL_BY_KEY: Record<string, MasterySkill> = SKILLS.reduce(
  (acc, s) => {
    acc[s.key] = s;
    return acc;
  },
  {} as Record<string, MasterySkill>,
);

// Deterministic weak-area picker.
//
// Signals available on TodayProgress (all local, no backend):
//   spokenSentenceCount  -> how much active speaking practice happened
//   reviewCardsCreated   -> how many review cards the learner has banked
//   streakDays           -> momentum / how far along they are overall
//
// Heuristic (documented so the ordering is auditable, not magic):
//   * Brand-new learner (little activity)  -> foundations first: 가나 -> 어휘 -> 문법.
//   * Almost no review cards               -> steer toward exam + grammar to
//     surface gaps worth banking as cards.
//   * Little speaking practice             -> steer toward speaking-heavy skills
//     (dailytalk / dialogue shadowing).
//   * Otherwise (engaged learner)          -> push advanced polish: 피치 / 경어 / 모의고사.
// Returns 2-3 skills, no duplicates, in priority order.
export function recommendNext(progress: TodayProgress): MasterySkill[] {
  const spoken = progress.spokenSentenceCount ?? 0;
  const cards = progress.reviewCardsCreated ?? 0;
  const streak = progress.streakDays ?? 0;

  const picks: string[] = [];
  const push = (key: string) => {
    if (!picks.includes(key) && SKILL_BY_KEY[key]) picks.push(key);
  };

  const isBeginner = streak <= 2 && spoken < 3;

  if (isBeginner) {
    // Foundations before anything else.
    push('kana');
    push('vocab');
    push('grammar');
  } else {
    if (spoken < 5) {
      // Not enough active output -> speaking-forward modes.
      push('dailytalk');
      push('dialogue');
    }
    if (cards < 5) {
      // Thin review bank -> find and bank gaps.
      push('grammar');
      push('exam');
    }
    // Engaged learners get advanced polish.
    push('pitch');
    push('keigo');
    push('conjugation');
  }

  // Always return 2-3. Backfill from tier order if the heuristics were sparse.
  for (const s of SKILLS) {
    if (picks.length >= 3) break;
    push(s.key);
  }

  return picks.slice(0, 3).map((k) => SKILL_BY_KEY[k]);
}
