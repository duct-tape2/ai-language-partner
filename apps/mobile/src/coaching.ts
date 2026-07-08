// Per-persona coaching voice. The persona is the product's core, so the SAME
// situation must read differently per persona — not just a color swap. These
// are local fixtures (no LLM/backend) but make 유이/하루카/렌 feel distinct in
// the practice + voice screens.
import type { SttStatus } from './sttFixtures';

export type Coaching = {
  opening: string;
  onPerfect: string;
  onPartial: string;
  onFail: string;
  retryCta: string;
};

const COACHING: Record<string, Coaching> = {
  yui: {
    opening: '오늘은 「今日めっちゃ疲れた」를 친구한테 말하듯 가볍게 가보자!',
    onPerfect: '오 완벽해! 진짜 친구처럼 자연스러웠어 😊',
    onPartial: '거의 다 왔어! 여기만 한 번 더 같이 해보자.',
    onFail: '괜찮아, 천천히 다시 해보자. 나 잘 듣고 있어!',
    retryCta: '한 번 더 같이!',
  },
  haruka: {
    opening: '今日めっちゃ疲れた의 「っ」(촉음)과 「れ」를 정확히 구분해 발음해 보세요.',
    onPerfect: '정확합니다. 박자와 장단음이 잘 잡혔어요.',
    onPartial: '촉음/장음에서 한 박이 흔들렸어요. 모라 단위로 다시 연습합시다.',
    onFail: '입력이 인식되지 않았습니다. 조용한 곳에서 또렷하게 한 번 더.',
    retryCta: '다시 발음',
  },
  ren: {
    opening: '이 표현 캐주얼해서 친구한테 딱이야. 자신감 있게 던져봐, 선배가 봐줄게.',
    onPerfect: '오 좀 치는데? 그 톤 그대로 가면 돼 👍',
    onPartial: '느낌은 왔어. 끝을 살짝 흘리듯 다시 가보자.',
    onFail: '안 들렸어 ㅋㅋ 다시, 이번엔 좀 크게.',
    retryCta: '다시 가보자',
  },
};

export function personaCoaching(id: string): Coaching {
  return COACHING[id] ?? COACHING.yui;
}

export function coachingLine(id: string, status: SttStatus): string {
  const c = personaCoaching(id);
  return status === 'perfect' ? c.onPerfect : status === 'partial' ? c.onPartial : c.onFail;
}
