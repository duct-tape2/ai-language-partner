import React from 'react';
import { Text, View, Pressable } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Button, Card, Fade, FuriganaTokens, Muted, Pill, Row, Title } from '../components';
import type { AppController } from '../store';
import { READING_PASSAGES, type ReadingPassage } from '../reading/readingData';

// 독해 연습 (Reading comprehension). Self-contained: local state only, reads the
// hand-authored passage bank. List -> passage (furigana + 낭독 듣기 + 번역 toggle
// + 4-choice questions with reveal/explanation/score) -> 홈으로.
const UI = {
  screenTitle: '독해 연습',
  screenSub: '짧은 지문을 읽고 이해했는지 확인해요. (N5 -> N4)',
  listen: '낭독 듣기',
  showTr: '한국어 번역 보기',
  hideTr: '한국어 번역 숨기기',
  translation: '한국어 번역',
  questions: '이해 확인',
  correct: '정답!',
  wrong: '오답',
  score: (c: number, t: number) => `점수 ${c} / ${t}`,
  allDone: '모든 문제를 풀었어요',
  back: '목록으로',
  home: '홈으로',
};

function LevelPill({ level }: { level: 'N5' | 'N4' }) {
  const { theme } = useTheme();
  const c = level === 'N5' ? theme.colors.good : theme.colors.accent;
  return (
    <View style={{ backgroundColor: c + '22', borderColor: c, borderWidth: 1, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 3 }}>
      <Text style={{ color: c, fontSize: 12, fontWeight: '800' }}>{level}</Text>
    </View>
  );
}

// The passage list has 141 entries; render a page at a time so it paints instantly
// instead of mounting 141 animated cards up front.
const PAGE = 40;

export function ReadingScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const color = personaColor(app.selectedPersonaId);
  const [openId, setOpenId] = React.useState<string | null>(null);
  const [limit, setLimit] = React.useState(PAGE);
  const [showTr, setShowTr] = React.useState(false);
  // per-question chosen index, keyed by question position within the open passage
  const [answers, setAnswers] = React.useState<Record<number, number>>({});

  const passage: ReadingPassage | undefined = openId ? READING_PASSAGES.find((p) => p.id === openId) : undefined;

  const openPassage = (p: ReadingPassage) => {
    setOpenId(p.id);
    setShowTr(false);
    setAnswers({});
    app.track('reading_opened', { id: p.id });
  };

  const closePassage = () => {
    setOpenId(null);
    setShowTr(false);
    setAnswers({});
  };

  const choose = (qIdx: number, cIdx: number) => {
    setAnswers((prev) => (prev[qIdx] != null ? prev : { ...prev, [qIdx]: cIdx }));
  };

  // ---------------- list view ----------------
  if (!passage) {
    return (
      <View>
        <Fade>
          <Title>{UI.screenTitle}</Title>
          <Muted>{UI.screenSub}</Muted>
        </Fade>
        {READING_PASSAGES.slice(0, limit).map((p) => (
          <Pressable key={p.id} onPress={() => openPassage(p)} accessibilityRole="button">
            <Card style={{ marginBottom: 10 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
                <Text style={{ fontSize: 17, fontWeight: '800', color: theme.colors.text, flex: 1, marginRight: 10 }}>{p.titleKo}</Text>
                <LevelPill level={p.level} />
              </View>
              <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 6 }}>
                {`${p.questions.length}문항 · ${p.passageJa.length}자`}
              </Text>
            </Card>
          </Pressable>
        ))}
        {limit < READING_PASSAGES.length ? (
          <Button title={`더 보기 (${READING_PASSAGES.length - limit}개 남음)`} onPress={() => setLimit((n) => n + PAGE * 2)} secondary color={color} />
        ) : null}
        <Fade delay={60}>
          <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
        </Fade>
      </View>
    );
  }

  // ---------------- passage view ----------------
  const total = passage.questions.length;
  const answeredCount = Object.keys(answers).length;
  const correctCount = passage.questions.reduce(
    (n, q, i) => (answers[i] === q.answerIndex ? n + 1 : n),
    0,
  );
  const allDone = answeredCount >= total;

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
          <Title>{passage.titleKo}</Title>
          <LevelPill level={passage.level} />
        </View>
      </Fade>

      {/* passage with furigana */}
      <Fade delay={40}>
        <Card>
          <FuriganaTokens tokens={passage.passageTokens} size={22} />
          <View style={{ marginTop: 14 }}>
            <Button title={app.speaking ? '재생 중...' : UI.listen} onPress={() => app.speak(passage.passageJa)} color={color} />
            <Pressable onPress={() => setShowTr((v) => !v)} accessibilityRole="button" style={{ marginTop: 4 }}>
              <Text style={{ color: color, fontSize: 14, fontWeight: '700', textAlign: 'center', paddingVertical: 8 }}>
                {showTr ? UI.hideTr : UI.showTr}
              </Text>
            </Pressable>
          </View>
          {showTr && (
            <View style={{ marginTop: 6, backgroundColor: theme.colors.chip, borderRadius: 12, padding: 12 }}>
              <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.subtext, marginBottom: 4 }}>{UI.translation}</Text>
              <Text style={{ fontSize: 15, color: theme.colors.text, lineHeight: 23 }}>{passage.translationKo}</Text>
            </View>
          )}
        </Card>
      </Fade>

      {/* questions */}
      <Fade delay={80}>
        <Row>
          <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text, marginRight: 8 }}>{UI.questions}</Text>
          <Pill label={UI.score(correctCount, total)} />
        </Row>
      </Fade>

      {passage.questions.map((q, qi) => {
        const chosen = answers[qi];
        const answered = chosen != null;
        return (
          <Fade key={qi} delay={100 + qi * 40}>
            <Card>
              <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text, marginBottom: 8 }}>
                {`${qi + 1}. ${q.q}`}
              </Text>
              {q.choices.map((c, ci) => {
                const isChosen = chosen === ci;
                const showCorrect = answered && ci === q.answerIndex;
                const showWrong = answered && isChosen && ci !== q.answerIndex;
                const bg = showCorrect ? theme.colors.good + '22' : showWrong ? theme.colors.bad + '22' : theme.colors.card;
                const bd = showCorrect ? theme.colors.good : showWrong ? theme.colors.bad : theme.colors.border;
                return (
                  <Pressable
                    key={ci}
                    onPress={() => choose(qi, ci)}
                    disabled={answered}
                    accessibilityRole="button"
                    style={{
                      borderWidth: 1.5,
                      borderColor: bd,
                      backgroundColor: bg,
                      borderRadius: 12,
                      paddingVertical: 12,
                      paddingHorizontal: 14,
                      marginTop: 8,
                      flexDirection: 'row',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <Text style={{ fontSize: 15, color: theme.colors.text, fontWeight: isChosen || showCorrect ? '800' : '500', flex: 1, marginRight: 8 }}>
                      {c}
                    </Text>
                    {showCorrect ? (
                      <Text style={{ color: theme.colors.good, fontWeight: '900' }}>O</Text>
                    ) : showWrong ? (
                      <Text style={{ color: theme.colors.bad, fontWeight: '900' }}>X</Text>
                    ) : null}
                  </Pressable>
                );
              })}
              {answered && (
                <View style={{ marginTop: 10, borderLeftWidth: 3, borderLeftColor: chosen === q.answerIndex ? theme.colors.good : color, paddingLeft: 10 }}>
                  <Text style={{ fontSize: 14, fontWeight: '800', color: chosen === q.answerIndex ? theme.colors.good : theme.colors.accentDark, marginBottom: 3 }}>
                    {chosen === q.answerIndex ? UI.correct : UI.wrong}
                  </Text>
                  <Text style={{ fontSize: 14, color: theme.colors.text, lineHeight: 21 }}>{q.explanationKo}</Text>
                </View>
              )}
            </Card>
          </Fade>
        );
      })}

      {allDone && (
        <Fade delay={60}>
          <Card style={{ borderColor: color, borderWidth: 1.5 }}>
            <Text style={{ fontSize: 17, fontWeight: '900', color: theme.colors.accentDark, textAlign: 'center' }}>
              {`${UI.allDone} — ${UI.score(correctCount, total)}`}
            </Text>
          </Card>
        </Fade>
      )}

      <Fade delay={80}>
        <Button title={UI.back} onPress={closePassage} color={color} />
        <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
      </Fade>
    </View>
  );
}
