import React from 'react';
import { Text, View, Pressable } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Card, Button, Title, Muted, Pill, Fade, Row, FuriganaTokens } from '../components';
import {
  CONJUGATIONS,
  CONJ_TOTAL,
  FORM_LABEL,
  TYPE_LABEL,
  TYPE_RULES,
  wordsByType,
  type ConjWord,
  type FormKey,
  type WordType,
} from '../conjugation/conjugationData';
import type { AppController } from '../store';

// 동사 형용사 활용 드릴 (Conjugation). 두 모드:
//  - drill: 단어 + 목표 형태(예: 'て형') 제시 -> 탭하면 정답 + 맞음/틀림 자가채점, 점수 누적
//  - browse: 활용 규칙을 타입별로 설명
// 정적 데이터만 사용, 네트워크 없음.

const UI = {
  title: '활용 드릴',
  subtitle: '동사와 형용사를 활용해서 말하는 연습이에요.',
  drillTab: '드릴',
  browseTab: '규칙 보기',
  reveal: '정답 보기',
  gotIt: '맞음',
  missed: '틀림',
  next: '다음 문제',
  restart: '다시 시작',
  home: '홈으로',
  answerLabel: '정답',
  targetLabel: '목표 형태',
  scoreLabel: '점수',
  streakLabel: '연속',
  progressOf: (i: number, n: number) => `${i} / ${n}`,
  accuracy: (correct: number, done: number) => (done === 0 ? '0%' : `${Math.round((correct / done) * 100)}%`),
  doneTitle: '한 바퀴 끝!',
  doneBody: (correct: number, total: number) => `${total}문제 중 ${correct}문제 맞혔어요.`,
  listen: '음성으로 듣기',
  ruleHint: '각 타입의 활용 규칙과 예시를 확인하세요.',
  example: '예시',
};

// The form keys a drill can ask for. Adjectives have no potential form, so the
// question generator skips 'potential' for adjectives.
const VERB_FORMS: FormKey[] = ['masu', 'te', 'nai', 'ta', 'potential'];
const ADJ_FORMS: FormKey[] = ['masu', 'te', 'nai', 'ta'];

type Question = { word: ConjWord; form: FormKey };

function isAdj(t: WordType): boolean {
  return t === 'i-adj' || t === 'na-adj';
}

// Deterministic-ish shuffle using Math.random once at build time. Each word
// contributes exactly one question with a randomly chosen applicable form, so a
// round is CONJ_TOTAL questions long and every word appears once.
function buildDeck(): Question[] {
  const deck: Question[] = CONJUGATIONS.map((word) => {
    const pool = isAdj(word.type) ? ADJ_FORMS : VERB_FORMS;
    const form = pool[Math.floor(Math.random() * pool.length)];
    return { word, form };
  });
  // Fisher-Yates
  for (let i = deck.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [deck[i], deck[j]] = [deck[j], deck[i]];
  }
  return deck;
}

export function ConjugationScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const accent = personaColor(app.selectedPersonaId);
  const [mode, setMode] = React.useState<'drill' | 'browse'>('drill');

  // drill state
  const [deck, setDeck] = React.useState<Question[]>(() => buildDeck());
  const [idx, setIdx] = React.useState(0);
  const [revealed, setRevealed] = React.useState(false);
  const [correct, setCorrect] = React.useState(0);
  const [done, setDone] = React.useState(0);
  const [streak, setStreak] = React.useState(0);
  const [finished, setFinished] = React.useState(false);

  // browse state
  const [openType, setOpenType] = React.useState<WordType | null>(null);

  const restart = () => {
    setDeck(buildDeck());
    setIdx(0);
    setRevealed(false);
    setCorrect(0);
    setDone(0);
    setStreak(0);
    setFinished(false);
  };

  const grade = (ok: boolean) => {
    const q = deck[idx];
    app.track('conjugation_drill', { type: q.word.type, form: q.form, correct: ok });
    const nextDone = done + 1;
    setDone(nextDone);
    if (ok) {
      setCorrect((c) => c + 1);
      setStreak((s) => s + 1);
    } else {
      setStreak(0);
    }
    if (idx + 1 >= deck.length) {
      setFinished(true);
    } else {
      setIdx(idx + 1);
      setRevealed(false);
    }
  };

  const switchMode = (m: 'drill' | 'browse') => {
    setMode(m);
    if (m === 'browse') setOpenType(null);
  };

  // ---------- shared header: mode toggle ----------
  const ModeToggle = (
    <View style={{ flexDirection: 'row', backgroundColor: theme.colors.track, borderRadius: 999, padding: 4, marginTop: 12, marginBottom: 12 }}>
      {([
        { value: 'drill' as const, label: UI.drillTab },
        { value: 'browse' as const, label: UI.browseTab },
      ]).map((t) => {
        const active = t.value === mode;
        return (
          <Pressable
            key={t.value}
            onPress={() => switchMode(t.value)}
            style={{ flex: 1 }}
            accessibilityRole="button"
            accessibilityLabel={t.label}
            accessibilityState={{ selected: active }}
          >
            <View style={{ paddingVertical: 8, alignItems: 'center', borderRadius: 999, backgroundColor: active ? theme.colors.card : 'transparent' }}>
              <Text style={{ fontWeight: active ? '800' : '500', color: active ? theme.colors.accentDark : theme.colors.subtext, fontSize: 14 }}>{t.label}</Text>
            </View>
          </Pressable>
        );
      })}
    </View>
  );

  // ================= BROWSE MODE =================
  if (mode === 'browse') {
    return (
      <View>
        <Fade>
          <Title>{UI.title}</Title>
          <Muted>{UI.ruleHint}</Muted>
          {ModeToggle}
        </Fade>

        {TYPE_RULES.map((rule, i) => {
          const open = openType === rule.type;
          const sample = CONJUGATIONS.find((w) => w.id === rule.sampleId);
          return (
            <Fade key={rule.type} delay={Math.min(60 + i * 40, 260)}>
              <Pressable
                onPress={() => setOpenType(open ? null : rule.type)}
                accessibilityRole="button"
                accessibilityLabel={rule.title}
                accessibilityState={{ expanded: open }}
              >
                <View
                  style={{
                    backgroundColor: theme.colors.card,
                    borderRadius: theme.radius.lg,
                    borderWidth: 1,
                    borderColor: theme.colors.border,
                    borderLeftWidth: 4,
                    borderLeftColor: accent,
                    padding: 16,
                    marginBottom: 10,
                  }}
                >
                  <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text style={{ fontSize: 18, fontWeight: '900', color: theme.colors.text }}>{rule.title}</Text>
                    <Text style={{ fontSize: 18, color: theme.colors.subtext }}>{open ? '−' : '+'}</Text>
                  </View>

                  {open ? (
                    <View style={{ marginTop: 12 }}>
                      {rule.rulesKo.map((line, k) => (
                        <View key={k} style={{ flexDirection: 'row', marginBottom: 8 }}>
                          <Text style={{ color: accent, fontWeight: '900', marginRight: 8, fontSize: 14 }}>{'•'}</Text>
                          <Text style={{ flex: 1, fontSize: 14, color: theme.colors.text, lineHeight: 21 }}>{line}</Text>
                        </View>
                      ))}
                      {sample ? (
                        <View style={{ marginTop: 6, paddingTop: 12, borderTopWidth: 1, borderTopColor: theme.colors.border }}>
                          <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.subtext, letterSpacing: 1, marginBottom: 8 }}>
                            {UI.example} ({sample.meaningKo})
                          </Text>
                          {(['masu', 'te', 'nai', 'ta', 'potential'] as FormKey[]).map((fk) => {
                            const form = sample.forms[fk];
                            if (!form) return null;
                            return (
                              <View key={fk} style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 6 }}>
                                <Text style={{ width: 64, fontSize: 12, fontWeight: '700', color: theme.colors.subtext }}>{FORM_LABEL[fk]}</Text>
                                <FuriganaTokens tokens={form.tokens} size={20} color={accent} />
                              </View>
                            );
                          })}
                        </View>
                      ) : null}
                    </View>
                  ) : (
                    <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 6 }}>
                      {wordsByType(rule.type).length}개 단어 수록
                    </Text>
                  )}
                </View>
              </Pressable>
            </Fade>
          );
        })}

        <Fade delay={300}>
          <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
        </Fade>
      </View>
    );
  }

  // ================= DRILL MODE =================
  if (finished) {
    return (
      <View>
        <Fade>
          <Title>{UI.title}</Title>
          {ModeToggle}
        </Fade>
        <Fade delay={60}>
          <Card style={{ alignItems: 'center' }}>
            <Text style={{ fontSize: 22, fontWeight: '900', color: theme.colors.text, marginBottom: 6 }}>{UI.doneTitle}</Text>
            <Text style={{ fontSize: 15, color: theme.colors.subtext, marginBottom: 16, textAlign: 'center' }}>{UI.doneBody(correct, deck.length)}</Text>
            <View style={{ flexDirection: 'row', width: '100%', justifyContent: 'space-around' }}>
              <View style={{ alignItems: 'center' }}>
                <Text style={{ fontSize: 30, fontWeight: '900', color: accent }}>{correct}</Text>
                <Text style={{ fontSize: 12, color: theme.colors.subtext }}>{UI.gotIt}</Text>
              </View>
              <View style={{ alignItems: 'center' }}>
                <Text style={{ fontSize: 30, fontWeight: '900', color: theme.colors.accentDark }}>{UI.accuracy(correct, done)}</Text>
                <Text style={{ fontSize: 12, color: theme.colors.subtext }}>{UI.scoreLabel}</Text>
              </View>
            </View>
          </Card>
        </Fade>
        <Fade delay={120}>
          <Button title={UI.restart} onPress={restart} color={accent} />
          <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
        </Fade>
      </View>
    );
  }

  const q = deck[idx];
  const answer = q.word.forms[q.form];
  const typeColor = isAdj(q.word.type) ? theme.colors.good : accent;

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>{UI.title}</Title>
          <Pill label={UI.progressOf(idx + 1, deck.length)} color={accent} />
        </View>
        {ModeToggle}
      </Fade>

      {/* scoreboard */}
      <Fade delay={40}>
        <View style={{ flexDirection: 'row', marginBottom: 12 }}>
          <View style={{ flex: 1, alignItems: 'center', backgroundColor: theme.colors.card, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.border, paddingVertical: 10, marginRight: 6 }}>
            <Text style={{ fontSize: 20, fontWeight: '900', color: accent }}>{correct}</Text>
            <Text style={{ fontSize: 11, color: theme.colors.subtext }}>{UI.gotIt}</Text>
          </View>
          <View style={{ flex: 1, alignItems: 'center', backgroundColor: theme.colors.card, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.border, paddingVertical: 10, marginHorizontal: 3 }}>
            <Text style={{ fontSize: 20, fontWeight: '900', color: theme.colors.accentDark }}>{UI.accuracy(correct, done)}</Text>
            <Text style={{ fontSize: 11, color: theme.colors.subtext }}>{UI.scoreLabel}</Text>
          </View>
          <View style={{ flex: 1, alignItems: 'center', backgroundColor: theme.colors.card, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.border, paddingVertical: 10, marginLeft: 6 }}>
            <Text style={{ fontSize: 20, fontWeight: '900', color: theme.colors.near }}>{streak}</Text>
            <Text style={{ fontSize: 11, color: theme.colors.subtext }}>{UI.streakLabel}</Text>
          </View>
        </View>
      </Fade>

      {/* question card */}
      <Fade delay={80}>
        <Card style={{ alignItems: 'center', paddingVertical: 28 }}>
          <Row>
            <Pill label={TYPE_LABEL[q.word.type]} color={typeColor} />
            <Pill label={q.word.meaningKo} />
          </Row>

          <View style={{ marginTop: 18, marginBottom: 6, alignItems: 'center' }}>
            <FuriganaTokens tokens={q.word.tokens} size={34} color={theme.colors.text} />
          </View>

          <View style={{ marginTop: 10, backgroundColor: theme.colors.chip, borderRadius: 999, paddingHorizontal: 16, paddingVertical: 8 }}>
            <Text style={{ fontSize: 12, color: theme.colors.subtext, textAlign: 'center' }}>{UI.targetLabel}</Text>
            <Text style={{ fontSize: 20, fontWeight: '900', color: theme.colors.accentDark, textAlign: 'center' }}>{FORM_LABEL[q.form]}</Text>
          </View>

          {revealed && answer ? (
            <Fade>
              <View style={{ marginTop: 22, alignItems: 'center', paddingTop: 18, borderTopWidth: 1, borderTopColor: theme.colors.border, width: 240 }}>
                <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.subtext, letterSpacing: 1, marginBottom: 8 }}>{UI.answerLabel}</Text>
                <FuriganaTokens tokens={answer.tokens} size={30} color={accent} />
                <View style={{ marginTop: 12, alignSelf: 'stretch' }}>
                  <Button title={UI.listen} onPress={() => app.speak(answer.ja)} secondary color={accent} />
                </View>
              </View>
            </Fade>
          ) : null}
        </Card>
      </Fade>

      {/* actions */}
      <Fade delay={120}>
        {!revealed ? (
          <Button title={UI.reveal} onPress={() => setRevealed(true)} color={accent} />
        ) : (
          <View style={{ flexDirection: 'row' }}>
            <View style={{ flex: 1, marginRight: 6 }}>
              <Button title={UI.gotIt} onPress={() => grade(true)} tone="good" />
            </View>
            <View style={{ flex: 1, marginLeft: 6 }}>
              <Button title={UI.missed} onPress={() => grade(false)} tone="bad" />
            </View>
          </View>
        )}
        <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
      </Fade>
    </View>
  );
}
