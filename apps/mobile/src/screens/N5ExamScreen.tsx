import React from 'react';
import { Text, View, Pressable } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Card, Button, Title, Muted, Pill, Fade, Row, FuriganaTokens } from '../components';
import type { AppController } from '../store';
import { MOCK_EXAM_N5, N5_PASS_RATIO, SECTION_LABEL_N5 } from '../exam/examN5Data';
import type { ExamSection } from '../exam/examN5Data';

// JLPT N5 모의고사 (N4보다 쉬운 두 번째 세트). Intro -> 한 문제씩(영역 배지 +
// 지문/문제 + 4지선다) -> 정답 피드백 + 해설 -> 60% 합격 기준의 결과 + 영역별 요약.
// 로컬 UI 상태만 사용하며 N4 데이터는 가져오지 않는 자립형 화면입니다.

const SECTION_COLOR: Record<ExamSection, 'accent' | 'good' | 'near'> = {
  vocab: 'accent',
  grammar: 'good',
  reading: 'near',
};

type Phase = 'intro' | 'quiz' | 'result';

export function N5ExamScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const accent = personaColor(app.selectedPersonaId);
  const total = MOCK_EXAM_N5.length;

  const [phase, setPhase] = React.useState<Phase>('intro');
  const [index, setIndex] = React.useState(0);
  const [picked, setPicked] = React.useState<number | null>(null);
  const [answers, setAnswers] = React.useState<number[]>([]);

  const q = MOCK_EXAM_N5[index];
  const answered = picked !== null;
  const isLast = index >= total - 1;

  const start = () => {
    app.track('n5_exam_started', { total });
    setAnswers([]);
    setIndex(0);
    setPicked(null);
    setPhase('quiz');
  };

  const pick = (i: number) => {
    if (answered) return;
    setPicked(i);
  };

  const next = () => {
    if (picked === null) return;
    const nextAnswers = [...answers, picked];
    setAnswers(nextAnswers);
    if (isLast) {
      const score = nextAnswers.reduce((s, a, i) => s + (a === MOCK_EXAM_N5[i].answerIndex ? 1 : 0), 0);
      app.track('n5_exam_finished', { score });
      setPhase('result');
    } else {
      setIndex(index + 1);
      setPicked(null);
    }
  };

  // ---------- intro ----------
  if (phase === 'intro') {
    const counts = MOCK_EXAM_N5.reduce(
      (acc, item) => {
        acc[item.section] += 1;
        return acc;
      },
      { vocab: 0, grammar: 0, reading: 0 } as Record<ExamSection, number>,
    );
    return (
      <View>
        <Fade>
          <Row>
            <Title>N5 모의고사</Title>
          </Row>
          <Muted>N4보다 쉬운 입문용 세트예요. JLPT N5 형식의 {total}문항 모의고사입니다.</Muted>
        </Fade>
        <Fade delay={60}>
          <Card style={{ borderColor: accent, borderWidth: 1.5 }}>
            <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text, marginBottom: 8 }}>구성</Text>
            <Row>
              <Pill label={`문자·어휘 ${counts.vocab}`} color={theme.colors.accentDark} />
              <Pill label={`문법 ${counts.grammar}`} color={theme.colors.good} />
              <Pill label={`독해 ${counts.reading}`} color={theme.colors.near} />
            </Row>
            <View style={{ height: 12 }} />
            <Muted>합격 기준: {Math.round(N5_PASS_RATIO * 100)}% 이상 ({Math.ceil(total * N5_PASS_RATIO)}/{total})</Muted>
            <Text style={{ fontSize: 14, color: theme.colors.subtext, marginTop: 6, lineHeight: 21 }}>
              한 문제씩 풀고, 답을 고르면 바로 정답과 해설을 볼 수 있어요. 청해는 포함되지 않습니다.
            </Text>
          </Card>
        </Fade>
        <Fade delay={120}>
          <Button title="시작하기" onPress={start} color={accent} />
          <Button title="홈으로" onPress={() => app.navigate('home')} secondary />
        </Fade>
      </View>
    );
  }

  // ---------- result ----------
  if (phase === 'result') {
    const score = answers.reduce((s, a, i) => s + (a === MOCK_EXAM_N5[i].answerIndex ? 1 : 0), 0);
    const pct = Math.round((score / total) * 100);
    const passed = score / total >= N5_PASS_RATIO;

    const bySection = (['vocab', 'grammar', 'reading'] as ExamSection[]).map((sec) => {
      const idxs = MOCK_EXAM_N5.map((item, i) => ({ item, i })).filter((x) => x.item.section === sec);
      const got = idxs.reduce((s, x) => s + (answers[x.i] === x.item.answerIndex ? 1 : 0), 0);
      return { sec, got, count: idxs.length };
    });

    return (
      <View>
        <Fade>
          <Title>결과</Title>
        </Fade>
        <Fade delay={60}>
          <Card
            style={{
              alignItems: 'center',
              borderColor: passed ? theme.colors.good : theme.colors.bad,
              borderWidth: 1.5,
              backgroundColor: theme.colors.accentSoft,
            }}
          >
            <Text style={{ fontSize: 44, fontWeight: '900', color: passed ? theme.colors.good : theme.colors.bad }}>
              {passed ? '합격' : '불합격'}
            </Text>
            <Text style={{ fontSize: 30, fontWeight: '900', color: theme.colors.text, marginTop: 4 }}>
              {score} / {total}
            </Text>
            <Text style={{ fontSize: 16, fontWeight: '700', color: theme.colors.subtext, marginTop: 2 }}>
              정답률 {pct}% (합격 {Math.round(N5_PASS_RATIO * 100)}%)
            </Text>
          </Card>
        </Fade>
        <Fade delay={120}>
          <Card>
            <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text, marginBottom: 4 }}>영역별 결과</Text>
            {bySection.map((b) => (
              <View
                key={b.sec}
                style={{
                  flexDirection: 'row',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  paddingVertical: 8,
                  borderBottomWidth: 1,
                  borderBottomColor: theme.colors.border,
                }}
              >
                <Text style={{ fontSize: 15, fontWeight: '700', color: theme.colors.text }}>{SECTION_LABEL_N5[b.sec]}</Text>
                <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.accentDark }}>
                  {b.got} / {b.count}
                </Text>
              </View>
            ))}
          </Card>
        </Fade>
        <Fade delay={180}>
          <Button title="다시 풀기" onPress={start} color={accent} />
          <Button title="홈으로" onPress={() => app.navigate('home')} secondary />
        </Fade>
      </View>
    );
  }

  // ---------- quiz ----------
  const secTone = SECTION_COLOR[q.section];
  const secColor =
    secTone === 'good' ? theme.colors.good : secTone === 'near' ? theme.colors.near : theme.colors.accentDark;

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>N5 모의고사</Title>
          <Pill label={`${index + 1}/${total}`} />
        </View>
        <Row>
          <Pill label={SECTION_LABEL_N5[q.section]} color={secColor} />
        </Row>
      </Fade>

      {q.passageJa ? (
        <Fade delay={40}>
          <Card style={{ backgroundColor: theme.colors.chip, borderColor: theme.colors.border }}>
            <Muted>지문</Muted>
            <Text style={{ fontSize: 17, color: theme.colors.text, lineHeight: 28, marginTop: 6 }}>{q.passageJa}</Text>
          </Card>
        </Fade>
      ) : null}

      <Fade delay={80}>
        <Card style={{ borderColor: secColor, borderWidth: 1.5 }}>
          {q.promptTokens ? (
            <FuriganaTokens tokens={q.promptTokens} size={22} color={theme.colors.text} />
          ) : (
            <Text style={{ fontSize: 19, fontWeight: '700', color: theme.colors.text, lineHeight: 30 }}>{q.promptJa}</Text>
          )}
        </Card>
      </Fade>

      <Fade delay={120}>
        {q.choices.map((c, i) => {
          const isCorrect = i === q.answerIndex;
          const isPicked = i === picked;
          let borderColor = theme.colors.border;
          let bg = theme.colors.card;
          let labelColor = theme.colors.text;
          if (answered) {
            if (isCorrect) {
              borderColor = theme.colors.good;
              bg = theme.colors.accentSoft;
              labelColor = theme.colors.good;
            } else if (isPicked) {
              borderColor = theme.colors.bad;
              labelColor = theme.colors.bad;
            }
          }
          const mark = answered ? (isCorrect ? '○ ' : isPicked ? '✕ ' : '') : '';
          return (
            <Pressable
              key={i}
              onPress={() => pick(i)}
              accessibilityRole="button"
              accessibilityLabel={`${i + 1}번. ${c}`}
              accessibilityState={{ selected: isPicked, disabled: answered }}
            >
              <View
                style={{
                  flexDirection: 'row',
                  alignItems: 'center',
                  backgroundColor: bg,
                  borderColor,
                  borderWidth: 1.5,
                  borderRadius: theme.radius.md,
                  paddingVertical: 14,
                  paddingHorizontal: 16,
                  marginBottom: 10,
                }}
              >
                <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.subtext, marginRight: 10 }}>{i + 1}</Text>
                <Text style={{ flex: 1, fontSize: 17, fontWeight: '600', color: labelColor }}>
                  {mark}
                  {c}
                </Text>
              </View>
            </Pressable>
          );
        })}
      </Fade>

      {answered ? (
        <Fade>
          <Card
            style={{
              borderColor: picked === q.answerIndex ? theme.colors.good : theme.colors.bad,
              borderWidth: 1.5,
            }}
          >
            <Text
              style={{
                fontSize: 16,
                fontWeight: '900',
                color: picked === q.answerIndex ? theme.colors.good : theme.colors.bad,
                marginBottom: 6,
              }}
            >
              {picked === q.answerIndex ? '정답입니다' : '틀렸습니다'}
            </Text>
            <Text style={{ fontSize: 15, color: theme.colors.text, lineHeight: 23 }}>{q.explanationKo}</Text>
          </Card>
          <Button title={isLast ? '결과 보기' : '다음 문제'} onPress={next} color={accent} />
        </Fade>
      ) : (
        <Fade>
          <Muted>답을 고르면 정답과 해설이 나와요.</Muted>
        </Fade>
      )}
    </View>
  );
}
