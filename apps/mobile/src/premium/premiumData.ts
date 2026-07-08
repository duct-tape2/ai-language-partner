// About / Premium / Privacy content for the packaging screen.
// Hand-authored Korean copy. No backend, no real payment. Purely presentational.

export type AboutDiff = { icon: string; title: string; body: string };
export type PlanFeature = { title: string; free: boolean; premium: boolean; note?: string };
export type PrivacyPoint = { icon: string; title: string; body: string };

// One-line pitch shown at the top of the About card.
export const APP_ABOUT = {
  tagline: '한국인을 위한 오프라인 일본어 회화 파트너',
  summary:
    '설치만 하면 서버 없이도 말하고 듣고 교정받는, 한국어 화자에 맞춘 일본어 학습 앱이에요. 발음 인식과 음성 합성이 기기 안에서 돌아가 대화가 끊기지 않습니다.',
  // Differentiators vs. generic language apps.
  diffs: [
    {
      icon: '声',
      title: '기기 내 음성 인식·합성',
      body: '발음 채점(STT)과 예문 읽어주기(TTS)가 로컬에서 처리돼요. 녹음 파일을 서버로 보내지 않습니다.',
    },
    {
      icon: '話',
      title: '사전 합성 대화팩',
      body: '자주 쓰는 상황 대화를 미리 준비해 두어, 네트워크가 없어도 자연스러운 흐름으로 연습할 수 있어요.',
    },
    {
      icon: '圏',
      title: '완전 오프라인 학습',
      body: '지하철, 비행기, 해외 로밍 없이도 전 과정이 동작해요. 데이터 요금 걱정 없이 매일 이어갈 수 있습니다.',
    },
    {
      icon: '韓',
      title: '한국인 특화 설계',
      body: '한국어 화자가 자주 틀리는 발음, 조사, 장단음, 청음·탁음을 겨냥한 교정과 함정 노트를 담았어요.',
    },
    {
      icon: '記',
      title: 'FSRS 간격 반복',
      body: '최신 FSRS 알고리즘으로 잊을 때쯤 복습을 띄워, 적은 카드로도 오래 기억에 남게 도와줘요.',
    },
  ] as AboutDiff[],
};

// Free vs Premium comparison (checklist). Honest: premium items are planned, not shipped.
export const FREE_FEATURES: string[] = [
  '기본 대화팩과 오늘의 학습',
  '기기 내 발음 채점(STT)',
  '예문 음성 재생(TTS)',
  'FSRS 복습 카드',
  '가나·기초 문법·기초 어휘',
];

export const PREMIUM_FEATURES: string[] = [
  '고급 대화팩(비즈니스·여행 심화)',
  '발음 정밀 분석(음소별 상세 피드백)',
  '전체 모의고사(회차 무제한)',
  '심화 문법·경어 마스터 코스',
];

// Row-level comparison used by the checklist table.
export const PLAN_FEATURES: PlanFeature[] = [
  { title: '기본 대화팩·오늘의 학습', free: true, premium: true },
  { title: '기기 내 발음 채점(STT)', free: true, premium: true },
  { title: '예문 음성 재생(TTS)', free: true, premium: true },
  { title: 'FSRS 복습 카드', free: true, premium: true },
  { title: '고급 대화팩(비즈니스·여행 심화)', free: false, premium: true },
  { title: '발음 정밀 분석(음소별 피드백)', free: false, premium: true },
  { title: '전체 모의고사(회차 무제한)', free: false, premium: true, note: '무료는 맛보기 1회' },
  { title: '심화 문법·경어 마스터 코스', free: false, premium: true },
];

// Privacy / voice-processing points. Emphasize local processing and offline benefit.
export const PRIVACY_POINTS: PrivacyPoint[] = [
  {
    icon: '端',
    title: '음성은 기기에서 처리돼요',
    body: '발음 인식과 읽어주기는 앱 안에서 실행됩니다. 녹음된 목소리를 외부 서버로 업로드하지 않아요.',
  },
  {
    icon: '蓄',
    title: '저장은 최소한으로',
    body: '학습 진도와 복습 일정은 기기 저장소에만 남아요. 계정 없이도 쓸 수 있고, 앱을 지우면 함께 사라집니다.',
  },
  {
    icon: '圏',
    title: '오프라인이라 더 안전해요',
    body: '네트워크 연결 자체가 필요 없으니 전송 중 노출 위험이 없어요. 개인정보가 기기 밖으로 나갈 통로가 없습니다.',
  },
];
