import React from 'react';
import { Text, View, Pressable } from 'react-native';
import type { AppController } from '../store';
import { useTheme } from '../ThemeContext';
import { Card, Button, Title, Muted, Pill, Fade, Row, FuriganaTokens } from '../components';
import { personaColor } from '../personaStyle';
import { MISTAKE_ITEMS, ROUND_SIZE } from '../mistakes/mistakesData';
import type { MistakeItem, SkillKo } from '../mistakes/mistakesData';

const KO = {
  title: '오답노트',
  subtitle: '틀린 문제만 모아 다시 풀며 약점을 지워요.',
  skillLabels: '어휘 · 문법 · 한자 · 표현 섞어서',
  question: '문제',
  ofRound: (i: number, n: number) => `${i} / ${n}`,
  score: '점수',
  streak: '연속',
  next: '다음 문제',
  finishRound: '결과 보기',
  roundTitle: '오답 정리',
  perfect: '전부 맞혔어요! 오답이 없습니다 🎉',
  wrongCount: (n: number) => `이번 라운드 오답 ${n}개`,
  correctAnswer: '정답',
  yourPick: '내 선택',
  redoWrong: '틀린 것만 다시 풀기',
  redoingTitle: '오답 다시 풀기',
  clearedAll: '오답을 모두 정리했어요! 잘했어요 👏',
  newRound: '새 라운드 시작',
  home: '홈으로',
  correct: '정답!',
  wrong: '오답',
  streakLabel: (n: number) => `${n}연속 정답`,
  explain: '해설',
};

const SKILL_EMOJI: Record<SkillKo, string> = {
  어휘: '📖',
  문법: '🧩',
  한자: '🈶',
  표현: '💬',
};

function shuffle<T>(arr: T[]): T[] {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const t = a[i];
    a[i] = a[j];
    a[j] = t;
  }
  return a;
}

type Phase = 'quiz' | 'summary';

export function MistakesScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const accent = personaColor(app.selectedPersonaId);

  // The pool for the current round. First round = a fresh shuffled slice of the
  // full bank; redo rounds = only the items missed last round.
  const [pool, setPool] = React.useState<MistakeItem[]>(() => shuffle(MISTAKE_ITEMS).slice(0, ROUND_SIZE));
  const [redoing, setRedoing] = React.useState(false);
  const [idx, setIdx] = React.useState(0);
  const [phase, setPhase] = React.useState<Phase>('quiz');
  const [picked, setPicked] = React.useState<number | null>(null);
  const [score, setScore] = React.useState(0);
  const [streak, setStreak] = React.useState(0);
  const [bestStreak, setBestStreak] = React.useState(0);
  // Missed items for THIS round, with the wrong choice the learner picked.
  const [missed, setMissed] = React.useState<{ item: MistakeItem; pick: number }[]>([]);

  const total = pool.length;
  const current = pool[idx];

  const onPick = (i: number) => {
    if (picked !== null || !current) return;
    setPicked(i);
    if (i === current.answerIndex) {
      setScore((s) => s + 1);
      setStreak((st) => {
        const next = st + 1;
        setBestStreak((b) => (next > b ? next : b));
        return next;
      });
      app.speak(current.promptJa.replace(/____/g, ''));
    } else {
      setStreak(0);
      setMissed((m) => [...m, { item: current, pick: i }]);
    }
  };

  const onNext = () => {
    if (idx + 1 >= total) {
      app.track('mistakes_round_done', { wrong: missed.length });
      setPhase('summary');
    } else {
      setIdx((n) => n + 1);
      setPicked(null);
    }
  };

  const startRound = (items: MistakeItem[], isRedo: boolean) => {
    setPool(items);
    setRedoing(isRedo);
    setIdx(0);
    setPhase('quiz');
    setPicked(null);
    setScore(0);
    setStreak(0);
    setBestStreak(0);
    setMissed([]);
  };

  const redoWrong = () => startRound(shuffle(missed.map((m) => m.item)), true);
  const newRound = () => startRound(shuffle(MISTAKE_ITEMS).slice(0, ROUND_SIZE), false);

  // ---------- summary ----------
  if (phase === 'summary') {
    const cleared = missed.length === 0;
    return (
      <View>
        <Fade>
          <Title>{KO.roundTitle}</Title>
          <Muted>{redoing ? KO.redoingTitle : KO.skillLabels}</Muted>
        </Fade>

        <Fade delay={60}>
          <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
            <Text style={{ fontSize: 20, fontWeight: '800', color: theme.colors.accentDark }}>
              {cleared ? (redoing ? KO.clearedAll : KO.perfect) : KO.wrongCount(missed.length)}
            </Text>
            <Row>
              <Pill label={`${KO.score} ${score}/${total}`} />
              <Pill label={KO.streakLabel(bestStreak)} />
            </Row>
          </Card>
        </Fade>

        {missed.map(({ item, pick }, k) => (
          <Fade key={item.id} delay={90 + k * 40}>
            <Card>
              <Row>
                <Pill label={`${SKILL_EMOJI[item.skillKo]} ${item.skillKo}`} color={accent} />
              </Row>
              {item.promptTokens ? (
                <View style={{ marginTop: 6 }}>
                  <FuriganaTokens tokens={item.promptTokens} size={22} color={accent} />
                </View>
              ) : (
                <Text style={{ fontSize: 20, fontWeight: '800', color: theme.colors.text, marginTop: 6 }}>{item.promptJa}</Text>
              )}
              {item.promptKo ? <Muted>{item.promptKo}</Muted> : null}

              <View style={{ marginTop: 10 }}>
                <Text style={{ fontSize: 13, color: theme.colors.bad, fontWeight: '700' }}>
                  {KO.yourPick}: {item.choices[pick]}
                </Text>
                <Text style={{ fontSize: 15, color: theme.colors.good, fontWeight: '800', marginTop: 2 }}>
                  {KO.correctAnswer}: {item.choices[item.answerIndex]}
                </Text>
              </View>

              <View
                style={{
                  marginTop: 10,
                  padding: 10,
                  borderRadius: theme.radius?.md ?? 12,
                  backgroundColor: theme.colors.chip,
                }}
              >
                <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.chipText, marginBottom: 2 }}>{KO.explain}</Text>
                <Text style={{ fontSize: 14, color: theme.colors.text, lineHeight: 21 }}>{item.explanationKo}</Text>
              </View>

              <Button title="다시 듣기" onPress={() => app.speak(item.promptJa.replace(/____/g, ''))} secondary />
            </Card>
          </Fade>
        ))}

        <Fade delay={140}>
          {missed.length > 0 ? (
            <Button title={KO.redoWrong} onPress={redoWrong} color={accent} />
          ) : (
            <Button title={KO.newRound} onPress={newRound} color={accent} />
          )}
          <Button title={KO.home} onPress={() => app.navigate('home')} secondary />
        </Fade>
      </View>
    );
  }

  // ---------- quiz ----------
  const answered = picked !== null;
  const isRight = answered && picked === current.answerIndex;

  return (
    <View>
      <Fade>
        <Title>{redoing ? KO.redoingTitle : KO.title}</Title>
        <Muted>{redoing ? '틀린 문제만 남았어요. 모두 맞히면 정리 완료!' : KO.subtitle}</Muted>
      </Fade>

      <Fade delay={50}>
        <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.accentDark }}>
              {KO.question} {KO.ofRound(idx + 1, total)}
            </Text>
            <View style={{ flexDirection: 'row' }}>
              <Text style={{ fontSize: 14, fontWeight: '800', color: theme.colors.text, marginRight: 14 }}>
                {KO.score} {score}
              </Text>
              <Text style={{ fontSize: 14, fontWeight: '800', color: streak > 0 ? theme.colors.near : theme.colors.subtext }}>
                {streak > 0 ? KO.streakLabel(streak) : `${KO.streak} 0`}
              </Text>
            </View>
          </View>
          {/* progress bar */}
          <View style={{ height: 8, borderRadius: 999, backgroundColor: theme.colors.track, marginTop: 10, overflow: 'hidden' }}>
            <View style={{ width: `${(idx / total) * 100}%`, height: 8, backgroundColor: accent }} />
          </View>
        </Card>
      </Fade>

      <Fade delay={100}>
        <Card>
          <Row>
            <Pill label={`${SKILL_EMOJI[current.skillKo]} ${current.skillKo}`} color={accent} />
          </Row>
          {current.promptTokens ? (
            <View style={{ marginTop: 10 }}>
              <FuriganaTokens tokens={current.promptTokens} size={26} color={accent} />
            </View>
          ) : (
            <Text style={{ fontSize: 24, fontWeight: '800', color: theme.colors.text, marginTop: 10 }}>{current.promptJa}</Text>
          )}
          {current.promptKo ? <Muted>{current.promptKo}</Muted> : null}

          <View style={{ marginTop: 14 }}>
            {current.choices.map((c, i) => {
              const isAnswer = i === current.answerIndex;
              const isPicked = i === picked;
              let borderColor = theme.colors.border;
              let bg = theme.colors.card;
              let fg = theme.colors.text;
              if (answered) {
                if (isAnswer) {
                  borderColor = theme.colors.good;
                  bg = theme.colors.good;
                  fg = '#fff';
                } else if (isPicked) {
                  borderColor = theme.colors.bad;
                  bg = theme.colors.bad;
                  fg = '#fff';
                }
              }
              return (
                <Pressable
                  key={i}
                  onPress={() => onPick(i)}
                  accessibilityRole="button"
                  accessibilityLabel={c}
                  accessibilityState={{ disabled: answered, selected: isPicked }}
                  disabled={answered}
                >
                  <View
                    style={{
                      borderWidth: 1.5,
                      borderColor,
                      backgroundColor: bg,
                      borderRadius: theme.radius?.md ?? 12,
                      paddingVertical: 14,
                      paddingHorizontal: 16,
                      marginVertical: 5,
                      flexDirection: 'row',
                      alignItems: 'center',
                    }}
                  >
                    <Text style={{ fontSize: 15, fontWeight: '800', color: answered && (isAnswer || isPicked) ? '#fff' : theme.colors.subtext, width: 26 }}>
                      {String.fromCharCode(65 + i)}
                    </Text>
                    <Text style={{ fontSize: 17, fontWeight: '700', color: fg, flex: 1 }}>{c}</Text>
                    {answered && isAnswer ? <Text style={{ fontSize: 16, color: '#fff' }}>○</Text> : null}
                    {answered && isPicked && !isAnswer ? <Text style={{ fontSize: 16, color: '#fff' }}>✕</Text> : null}
                  </View>
                </Pressable>
              );
            })}
          </View>

          {answered ? (
            <View style={{ marginTop: 8 }}>
              <Text style={{ fontSize: 16, fontWeight: '900', color: isRight ? theme.colors.good : theme.colors.bad }}>
                {isRight ? KO.correct : KO.wrong}
              </Text>
              <View
                style={{
                  marginTop: 6,
                  padding: 10,
                  borderRadius: theme.radius?.md ?? 12,
                  backgroundColor: theme.colors.chip,
                }}
              >
                <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.chipText, marginBottom: 2 }}>{KO.explain}</Text>
                <Text style={{ fontSize: 14, color: theme.colors.text, lineHeight: 21 }}>{current.explanationKo}</Text>
              </View>
              <Button title={idx + 1 >= total ? KO.finishRound : KO.next} onPress={onNext} color={accent} />
            </View>
          ) : null}
        </Card>
      </Fade>

      <Fade delay={150}>
        <Button title={KO.home} onPress={() => app.navigate('home')} secondary />
      </Fade>
    </View>
  );
}
