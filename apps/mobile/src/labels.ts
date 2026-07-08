// Maps raw backend identifiers (course levels, recommendation action ids) to
// user-facing Korean copy so internal slugs never leak into the UI.
const COURSE_LEVEL: Record<string, string> = {
  beginner: '입문',
  beginner_to_low_intermediate: '입문~초중급',
  beginner_travel: '여행 입문',
  low_intermediate: '초중급',
  intermediate: '중급',
};

export function courseLevelLabel(level: string): string {
  return COURSE_LEVEL[level] ?? level.replace(/_/g, ' ');
}

// Backend course titles are English; show Korean to learners (keyed by course id,
// fallback to the backend title).
const COURSE_TITLE_KO: Record<string, string> = {
  jp_beginner_speaking_ko: '한국어로 시작하는 일본어 말하기 기초',
  jp_travel_survival_ko: '여행 일본어 서바이벌',
};

export function courseTitle(id: string, fallback: string): string {
  return COURSE_TITLE_KO[id] ?? fallback;
}

const NEXT_ACTION: Record<string, string> = {
  start_practice_room: '오늘의 연습방으로 시작하기',
  review_due_cards: '복습 카드부터 복습하기',
  continue_course: '코스 이어서 학습하기',
  daily_mission: '오늘의 3분 미션 시작하기',
};

export function nextActionLabel(action: string, fallbackRoomTitle?: string): string {
  if (NEXT_ACTION[action]) return NEXT_ACTION[action];
  if (fallbackRoomTitle) return `오늘은 「${fallbackRoomTitle}」로 시작해요`;
  return '오늘의 3분 미션 시작하기';
}

// Localize known reward catalog keys to Korean; fall back to backend copy.
const REWARD_KO: Record<string, { title: string; desc: string }> = {
  xp_boost_2x_15m: { title: '2배 XP 부스트 (15분)', desc: '15분 동안 받는 XP가 2배로 적립돼요.' },
  streak_freeze_1: { title: '스트릭 프리즈', desc: '하루 빠져도 연속 학습일이 유지돼요.' },
};

export function rewardTitle(key: string, fallback: string): string {
  return REWARD_KO[key]?.title ?? fallback;
}

export function rewardDesc(key: string, fallback?: string | null): string | null {
  return REWARD_KO[key]?.desc ?? fallback ?? null;
}

// Why a learner was recommended as a friend; raw reasonCodes -> natural Korean.
// Keys match the backend's emitted codes (store.py friend recommendation builder).
const FRIEND_REASON: Record<string, string> = {
  target_language_match: '같은 언어를 배워요',
  level_match: '비슷한 레벨이에요',
  similar_weekly_xp: '학습량이 비슷해요',
  shared_practice_sources: '같은 연습을 했어요',
  active_this_week: '이번 주에 학습했어요',
};

// Backend learner ids (e.g. "friend_08846e81", "local-dev") must never appear in
// the UI. The contract has no nickname field, so derive a stable friendly alias.
const ALIAS_POOL = ['유키', '하루', '소라', '리쿠', '아오이', '사쿠라', '카이', '메이', '준', '노아', '미오', '하나', '유나', '신', '레이', '토우'];

export function learnerName(id: string, isSelf = false): string {
  if (isSelf || id === 'local-dev') return '나';
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  return ALIAS_POOL[h % ALIAS_POOL.length];
}

// Pronunciation/correction feedback: raw backend category·severity -> Korean.
const CORRECTION_CATEGORY: Record<string, string> = {
  grammar: '문법', vocabulary: '어휘', vocab: '어휘', naturalness: '자연스러움',
  pronunciation: '발음', particle: '조사', politeness: '공손도', word_order: '어순', spelling: '표기',
};
const SEVERITY_KO: Record<string, string> = {
  minor: '가벼운 교정', major: '중요 교정', critical: '꼭 고쳐요', info: '참고',
};
export function correctionLabel(category: string, severity: string): string {
  const c = CORRECTION_CATEGORY[category] ?? '교정';
  const s = SEVERITY_KO[severity];
  return s ? `${c} · ${s}` : c;
}

export function friendReason(reasonCodes: string[], sharedSources: string[]): string {
  for (const c of reasonCodes) {
    if (FRIEND_REASON[c]) return FRIEND_REASON[c];
  }
  if (sharedSources.length) return `공통 관심: ${sharedSources.slice(0, 2).join(', ')}`;
  return '나와 비슷한 학습자예요';
}
