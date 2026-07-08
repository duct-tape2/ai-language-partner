import React from 'react';
import { Text, View, Pressable } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Card, Button, Title, Muted, Pill, Fade, Row, FuriganaTokens } from '../components';
import type { AppController } from '../store';
import { PLACEMENT_QUESTIONS, PLACEMENT_TOTAL, PLACEMENT_N4_THRESHOLD } from '../exam/placementData';

// Placement Test (배치 테스트): a quick 6-question level check for onboarding.
// intro -> one question at a time -> result (recommended level, 정답률, weak
// skill tags, and CTAs). Local UI state only; no persistence needed here.
type Phase = 'intro' | 'quiz' | 'result';

const KO = {
  title: '배치 테스트',
  introLead: '6문제로 지금 실력을 빠르게 확인해요.',
  introBody: 'N5(기초)부터 N4(초중급)까지 조금씩 어려워져요. 편하게 골라 보세요 — 몰라도 괜찮아요.',
  introMeta: '약 2분 · 6문제 · 언제든 다시 볼 수 있어요',
  start: '테스트 시작',
  later: '나중에 할게요',
  next: '다음 문제 →',
  finish: '결과 보기 🎉',
  resultTitle: '결과가 나왔어요',
  recPrefix: '추천 시작 레벨',
  accuracy: '정답률',
  correctOf: (c: number, t: number) => `${c} / ${t} 정답`,
  weakTitle: '집중하면 좋은 부분',
  weakNone: '약점이 거의 없어요. 아주 좋아요!',
  ctaStart: '추천 코스로 시작',
  ctaHome: '홈으로',
  retry: '다시 풀기',
  progress: (i: number, t: number) => `${i} / ${t}`,
};

const LEVEL_BLURB: Record<'N5' | 'N4', string> = {
  N5: '기초 인사와 조사, 기본 동사부터 탄탄하게 시작해요.',
  N4: '기본기가 좋아요. 동사 활용과 일상 회화 위주로 올려봐요.',
};

export function PlacementTestScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const color = personaColor(app.selectedPersonaId);

  const [phase, setPhase] = React.useState<Phase>('intro');
  const [index, setIndex] = React.useState(0);
  const [answers, setAnswers] = React.useState<(number | null)[]>(
    () => PLACEMENT_QUESTIONS.map(() => null),
  );

  const q = PLACEMENT_QUESTIONS[index];
  const picked = answers[index];
  const answered = picked != null;
  const isLast = index >= PLACEMENT_TOTAL - 1;

  const pick = (choiceIndex: number) => {
    if (answered) return;
    setAnswers((prev) => {
      const next = prev.slice();
      next[index] = choiceIndex;
      return next;
    });
  };

  const advance = () => {
    if (isLast) {
      finish();
    } else {
      setIndex((i) => i + 1);
    }
  };

  const finish = () => {
    let correct = 0;
    PLACEMENT_QUESTIONS.forEach((item, i) => {
      if (answers[i] === item.answerIndex) correct += 1;
    });
    const recommendedLevel = correct >= PLACEMENT_N4_THRESHOLD ? 'N4' : 'N5';
    app.track('placement_completed', { recommendedLevel, correct });
    setPhase('result');
  };

  const restart = () => {
    setAnswers(PLACEMENT_QUESTIONS.map(() => null));
    setIndex(0);
    setPhase('intro');
  };

  // ---------- intro ----------
  if (phase === 'intro') {
    return (
      <View>
        <Fade>
          <Title>{KO.title}</Title>
          <Muted>{KO.introLead}</Muted>
        </Fade>
        <Fade delay={60}>
          <Card>
            <Text style={{ fontSize: 15, color: theme.colors.text, lineHeight: 23 }}>{KO.introBody}</Text>
            <Row>
              <Pill label="N5 → N4" color={color} />
              <Pill label="6문제" />
              <Pill label="약 2분" />
            </Row>
            <Text style={{ marginTop: 10, fontSize: 13, color: theme.colors.subtext }}>{KO.introMeta}</Text>
          </Card>
        </Fade>
        <Fade delay={120}>
          <Button title={KO.start} onPress={() => setPhase('quiz')} color={color} />
          <Button title={KO.later} onPress={() => app.navigate('home')} secondary />
        </Fade>
      </View>
    );
  }

  // ---------- result ----------
  if (phase === 'result') {
    let correct = 0;
    const weak = new Map<string, number>();
    PLACEMENT_QUESTIONS.forEach((item, i) => {
      if (answers[i] === item.answerIndex) correct += 1;
      else weak.set(item.skillTagKo, (weak.get(item.skillTagKo) ?? 0) + 1);
    });
    const recommendedLevel: 'N5' | 'N4' = correct >= PLACEMENT_N4_THRESHOLD ? 'N4' : 'N5';
    const pct = Math.round((correct / PLACEMENT_TOTAL) * 100);
    const weakTags = Array.from(weak.entries()).sort((a, b) => b[1] - a[1]);

    return (
      <View>
        <Fade>
          <Title>{KO.resultTitle}</Title>
        </Fade>

        <Fade delay={60}>
          <Card style={{ borderColor: color, borderWidth: 1.5, alignItems: 'center' }}>
            <Text style={{ fontSize: 13, color: theme.colors.subtext, fontWeight: '700' }}>{KO.recPrefix}</Text>
            <Text style={{ fontSize: 46, fontWeight: '900', color, marginTop: 2 }}>{recommendedLevel}</Text>
            <Text style={{ fontSize: 14, color: theme.colors.text, lineHeight: 21, textAlign: 'center', marginTop: 4 }}>
              {LEVEL_BLURB[recommendedLevel]}
            </Text>
          </Card>
        </Fade>

        <Fade delay={110}>
          <Card>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text }}>{KO.accuracy}</Text>
              <Text style={{ fontSize: 22, fontWeight: '900', color: theme.colors.text }}>{pct}%</Text>
            </View>
            <View style={{ height: 10, borderRadius: 999, backgroundColor: theme.colors.track, marginTop: 10, overflow: 'hidden' }}>
              <View style={{ width: `${pct}%`, height: '100%', backgroundColor: color, borderRadius: 999 }} />
            </View>
            <Text style={{ marginTop: 8, fontSize: 13, color: theme.colors.subtext }}>{KO.correctOf(correct, PLACEMENT_TOTAL)}</Text>
          </Card>
        </Fade>

        <Fade delay={160}>
          <Card>
            <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text, marginBottom: 4 }}>{KO.weakTitle}</Text>
            {weakTags.length === 0 ? (
              <Muted>{KO.weakNone}</Muted>
            ) : (
              <Row>
                {weakTags.map(([tag, miss]) => (
                  <View
                    key={tag}
                    style={{
                      flexDirection: 'row',
                      alignItems: 'center',
                      backgroundColor: theme.colors.bad + '18',
                      borderColor: theme.colors.bad,
                      borderWidth: 1,
                      borderRadius: 999,
                      paddingHorizontal: 12,
                      paddingVertical: 6,
                      marginRight: 8,
                      marginTop: 8,
                    }}
                  >
                    <Text style={{ color: theme.colors.bad, fontSize: 13, fontWeight: '700' }}>{tag}</Text>
                    <Text style={{ color: theme.colors.subtext, fontSize: 12, marginLeft: 6 }}>{miss}개 틀림</Text>
                  </View>
                ))}
              </Row>
            )}
          </Card>
        </Fade>

        <Fade delay={210}>
          <Button title={KO.ctaStart} onPress={() => app.navigate('hub')} color={color} />
          <Button title={KO.ctaHome} onPress={() => app.navigate('home')} secondary />
          <Pressable onPress={restart} accessibilityRole="button" style={{ alignItems: 'center', paddingVertical: 8 }}>
            <Text style={{ color: theme.colors.subtext, fontSize: 14, fontWeight: '600' }}>{KO.retry}</Text>
          </Pressable>
        </Fade>
      </View>
    );
  }

  // ---------- quiz ----------
  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>{KO.title}</Title>
          <Pill label={KO.progress(index + 1, PLACEMENT_TOTAL)} />
        </View>
        <View style={{ height: 6, borderRadius: 999, backgroundColor: theme.colors.track, marginTop: 4, overflow: 'hidden' }}>
          <View style={{ width: `${((index + 1) / PLACEMENT_TOTAL) * 100}%`, height: '100%', backgroundColor: color, borderRadius: 999 }} />
        </View>
      </Fade>

      <Fade delay={60}>
        <Card>
          <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 12 }}>
            <View style={{ backgroundColor: q.level === 'N5' ? theme.colors.good + '22' : theme.colors.accentSoft, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 4 }}>
              <Text style={{ color: q.level === 'N5' ? theme.colors.good : theme.colors.accentDark, fontSize: 12, fontWeight: '800' }}>{q.level}</Text>
            </View>
            <Text style={{ color: theme.colors.subtext, fontSize: 12, fontWeight: '600', marginLeft: 8 }}>{q.skillTagKo}</Text>
          </View>
          {q.promptTokens ? (
            <FuriganaTokens tokens={q.promptTokens} size={24} color={theme.colors.text} />
          ) : (
            <Text style={{ fontSize: 22, fontWeight: '700', color: theme.colors.text }}>{q.promptJa}</Text>
          )}
        </Card>
      </Fade>

      <Fade delay={110}>
        <Card>
          {q.choices.map((choice, ci) => {
            const chosen = picked === ci;
            const showCorrect = answered && ci === q.answerIndex;
            const showWrong = answered && chosen && ci !== q.answerIndex;
            const bg = showCorrect ? theme.colors.good + '22' : showWrong ? theme.colors.bad + '22' : theme.colors.card;
            const bd = showCorrect ? theme.colors.good : showWrong ? theme.colors.bad : theme.colors.border;
            return (
              <Pressable
                key={ci}
                onPress={() => pick(ci)}
                disabled={answered}
                accessibilityRole="button"
                style={{
                  borderWidth: 1.5,
                  borderColor: bd,
                  backgroundColor: bg,
                  borderRadius: 12,
                  paddingVertical: 14,
                  paddingHorizontal: 16,
                  marginTop: 8,
                  flexDirection: 'row',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <Text style={{ fontSize: 20, color: theme.colors.text, fontWeight: chosen || showCorrect ? '800' : '500' }}>{choice}</Text>
                {showCorrect ? (
                  <Text style={{ color: theme.colors.good, fontWeight: '900', fontSize: 18 }}>✓</Text>
                ) : showWrong ? (
                  <Text style={{ color: theme.colors.bad, fontWeight: '900', fontSize: 18 }}>✕</Text>
                ) : null}
              </Pressable>
            );
          })}
        </Card>
      </Fade>

      <Fade delay={150}>
        <Button
          title={isLast ? KO.finish : KO.next}
          onPress={advance}
          color={color}
          disabled={!answered}
        />
        <Button title={KO.ctaHome} onPress={() => app.navigate('home')} secondary />
      </Fade>
    </View>
  );
}
