// Demo STT outcomes. Because there is no real speech backend yet, the speaking
// loop must NOT always show 100% — that would teach a false "your pronunciation
// is perfect". Instead we rotate through realistic outcomes (perfect / partial
// errors / failures) so the diff, accuracy, and failure-state UI are exercised.
export type SttStatus = 'perfect' | 'partial' | 'fail';

export type SttOutcome = {
  status: SttStatus;
  transcript: string; // what was "heard" (empty on fail)
  warning?: 'no_speech' | 'too_noisy' | 'mic_permission_denied' | 'timeout';
  note: string; // short KO explanation shown to the learner
};

// Outcomes for the tired_today target 「今日めっちゃ疲れた」.
const OUTCOMES: SttOutcome[] = [
  { status: 'perfect', transcript: '今日めっちゃ疲れた', note: '깔끔해요! 발음이 정확합니다.' },
  { status: 'partial', transcript: '今日めっちゃ疲た', note: '「れ」가 빠졌어요. 「つか-れ-た」 3박을 또박또박.' },
  { status: 'partial', transcript: '今日めちゃ疲れた', note: '「っ」촉음이 약했어요. 살짝 멈췄다 가기.' },
  { status: 'partial', transcript: 'きょうめっちゃつかれた', note: '뜻은 맞지만 한자 대신 가나로 들렸어요. 천천히 또렷하게.' },
  { status: 'fail', transcript: '', warning: 'no_speech', note: '소리가 잘 안 들렸어요. 마이크에 가까이서 다시 한 번.' },
];

// Rotate by attempt index so repeated taps show different results.
export function sttOutcomeFor(attempt: number): SttOutcome {
  return OUTCOMES[attempt % OUTCOMES.length];
}
