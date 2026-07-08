import type { Course, Persona, PracticeRoom, ReviewCard, TodayProgress, Entitlement } from './types';

export const PERSONAS: Persona[] = [
  {
    id: 'yui',
    displayName: '유이',
    japaneseName: 'ゆい',
    role: '다정한 일본인 친구',
    voiceStyle: '밝고 부드러운 20대 여성 보이스',
    teachingStyle: '초보자 친화, 칭찬 많음, 한국어 설명 40%',
    avatarEmoji: '🌸',
    defaultLanguageMix: { ko: 40, ja: 60 },
  },
  {
    id: 'haruka',
    displayName: '하루카 센세',
    japaneseName: 'はるか先生',
    role: '차분한 일본어 선생님',
    voiceStyle: '차분하고 명료한 선생님 보이스',
    teachingStyle: '문법, 뉘앙스, JLPT, 발음 교정 중심',
    avatarEmoji: '📘',
    defaultLanguageMix: { ko: 55, ja: 45 },
  },
  {
    id: 'ren',
    displayName: '렌 선배',
    japaneseName: 'レン先輩',
    role: '장난기 있는 애니풍 선배',
    voiceStyle: '청량하고 자신감 있는 남성 보이스',
    teachingStyle: '애니 말투와 현실 일본어 차이를 재밌게 설명',
    avatarEmoji: '⚡',
    defaultLanguageMix: { ko: 35, ja: 65 },
  },
];

export const PRACTICE_ROOMS: PracticeRoom[] = [
  {
    id: 'tired_today',
    title: '오늘 너무 피곤했어',
    primaryPhraseKo: '오늘 너무 피곤했어',
    primaryPhraseJa: '今日めっちゃ疲れた',
    alternativePhrasesJa: ['今日はすごく疲れた', '今日ちょっとしんどい'],
    personaId: 'yui',
    scenario: '친구에게 오늘 힘들었다고 말하기',
    openingMessage: '오늘은 「今日めっちゃ疲れた」를 실제 친구한테 말하듯 연습해보자.',
    courseId: 'jp_beginner_speaking_ko',
    courseTitle: 'Korean-first Japanese Speaking Foundations',
    unitId: 'unit_daily_feelings',
    unitTitle: '하루 컨디션과 감정 말하기',
    unitOrder: 1,
    lessonId: 'lesson_tired_feelings',
    lessonTitle: '피곤함과 멘탈 표현',
    lessonOrder: 1,
    roomOrder: 1,
    tags: ['감정표현', '친구말투', '일상'],
  },
  {
    id: 'mental_tired',
    title: '멘탈 나갔어',
    primaryPhraseKo: '오늘 멘탈 나갔어',
    primaryPhraseJa: '今日メンタルやられた',
    alternativePhrasesJa: ['今日ちょっとしんどい', 'もう無理かも'],
    personaId: 'yui',
    scenario: '일본인 친구에게 힘든 하루 설명하기',
    openingMessage: '이 표현은 뉘앙스가 중요해. 너무 과하지 않게 말하는 법을 연습하자.',
    courseId: 'jp_beginner_speaking_ko',
    courseTitle: 'Korean-first Japanese Speaking Foundations',
    unitId: 'unit_daily_feelings',
    unitTitle: '하루 컨디션과 감정 말하기',
    unitOrder: 1,
    lessonId: 'lesson_tired_feelings',
    lessonTitle: '피곤함과 멘탈 표현',
    lessonOrder: 1,
    roomOrder: 2,
    tags: ['감정표현', '현실표현'],
  },
];

export const COURSE_CATALOG: Course[] = [
  {
    id: 'jp_beginner_speaking_ko',
    title: 'Korean-first Japanese Speaking Foundations',
    targetLanguage: 'ja',
    nativeLanguage: 'ko',
    level: 'beginner_to_low_intermediate',
    descriptionKo: '한국어 사고에서 바로 일본어 일상 대화로 넘어가기 위한 첫 코스',
    units: [
      {
        id: 'unit_daily_feelings',
        title: '하루 컨디션과 감정 말하기',
        order: 1,
        skillTags: ['감정표현', '컨디션', '친구말투'],
        lessons: [
          {
            id: 'lesson_tired_feelings',
            title: '피곤함과 멘탈 표현',
            order: 1,
            practiceRoomIds: ['tired_today', 'mental_tired'],
          },
        ],
      },
    ],
  },
];

export const INITIAL_REVIEW_CARD: ReviewCard = {
  id: 'card_tired_today_001',
  learnerId: 'local-dev',
  front: '오늘 너무 피곤했어',
  back: '今日めっちゃ疲れた。',
  example: 'A: 今日どうだった？ B: 今日めっちゃ疲れた。',
  tags: ['감정표현', '친구말투', '일상'],
};

export const TODAY_PROGRESS: TodayProgress = {
  date: '2026-06-29',
  streakDays: 1,
  completedMissions: 0,
  spokenSentenceCount: 0,
  reviewCardsCreated: 0,
};

export const MASTER_ENTITLEMENT: Entitlement = {
  plan: 'master_sandbox',
  voiceMinutesPerMonth: 'unlimited_for_master_sandbox',
  maxPersonas: 'unlimited',
  customPersona: true,
  reviewCardsLimit: 'unlimited',
  premiumVoices: true,
};
