import React from 'react';
import { Text, View, Pressable } from 'react-native';
import * as Speech from 'expo-speech';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Button, Card, Fade, FuriganaTokens, Muted, Pill, Row, Title } from '../components';
import { Icon } from '../icons';
import type { AppController } from '../store';
import { CHOUKAI_ITEMS, CHOUKAI_TOTAL, type ChoukaiItem } from '../choukai/choukaiData';

// 청해 (Listening comprehension). Self-contained: local state only, reads the
// hand-authored dialogue bank. List -> item: '▶ 대화 듣기' plays every line in
// order via app.speak (A then B, chained), then the question + 4 choices reveal
// the answer + explanation. After answering you can show the transcript
// (FuriganaTokens). Distinct from the dictation/듣기 screen: here you follow a
// two-speaker conversation and answer a "누가/언제/얼마/어디" style question.
//
// Chaining note: app.speak() calls Speech.stop() on every call and exposes no
// onDone hook, so lines are chained with setTimeout using a length-based
// duration estimate. Not word-perfect timing, but each line is fully spoken
// before the next starts. Timers are cleared on unmount and when leaving an item.

const UI = {
  screenTitle: '청해 연습',
  screenSub: '짧은 대화를 듣고 질문에 답해요. (N5 -> N4)',
  play: '대화 듣기',
  playing: '재생 중...',
  replay: '다시 듣기',
  question: '질문',
  showScript: '대화 스크립트 보기',
  hideScript: '대화 스크립트 숨기기',
  script: '대화 스크립트',
  correct: '정답!',
  wrong: '오답',
  explanation: '해설',
  score: (c: number, t: number) => `점수 ${c} / ${t}`,
  answered: (n: number, t: number) => `푼 문제 ${n} / ${t}`,
  back: '목록으로',
  home: '홈으로',
};

// Rough spoken duration for a JA line via device TTS, in ms. Kana/kanji are
// slower than latin punctuation; clamp so very short/long lines stay sane.
function estimateMs(ja: string): number {
  const base = 700;
  const perChar = 130;
  return Math.min(6000, Math.max(1200, base + ja.length * perChar));
}

function LevelPill({ level }: { level: 'N5' | 'N4' }) {
  const { theme } = useTheme();
  const c = level === 'N5' ? theme.colors.good : theme.colors.accent;
  return (
    <View style={{ backgroundColor: c + '22', borderColor: c, borderWidth: 1, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 3 }}>
      <Text style={{ color: c, fontSize: 12, fontWeight: '800' }}>{level}</Text>
    </View>
  );
}

export function ChoukaiScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const color = personaColor(app.selectedPersonaId);
  const [openId, setOpenId] = React.useState<string | null>(null);
  const [chosen, setChosen] = React.useState<number | null>(null);
  const [showScript, setShowScript] = React.useState(false);
  const [playing, setPlaying] = React.useState(false);
  // ids of items answered correctly at least once this session (for the score)
  const [correctIds, setCorrectIds] = React.useState<Record<string, boolean>>({});
  const [answeredIds, setAnsweredIds] = React.useState<Record<string, boolean>>({});

  const timers = React.useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearTimers = React.useCallback(() => {
    timers.current.forEach((t) => clearTimeout(t));
    timers.current = [];
    Speech.stop(); // halt the utterance already speaking, not just pending line timers
    setPlaying(false);
  }, []);

  React.useEffect(() => {
    return () => {
      timers.current.forEach((t) => clearTimeout(t));
      Speech.stop();
    };
  }, []);

  const item: ChoukaiItem | undefined = openId ? CHOUKAI_ITEMS.find((i) => i.id === openId) : undefined;

  const openItem = (i: ChoukaiItem) => {
    clearTimers();
    setOpenId(i.id);
    setChosen(null);
    setShowScript(false);
    app.track('choukai_opened', { id: i.id });
  };

  const closeItem = () => {
    clearTimers();
    setOpenId(null);
    setChosen(null);
    setShowScript(false);
  };

  const playDialogue = (it: ChoukaiItem) => {
    clearTimers();
    setPlaying(true);
    let delay = 0;
    it.lines.forEach((line, idx) => {
      const t = setTimeout(() => app.speak(line.ja), delay);
      timers.current.push(t);
      delay += estimateMs(line.ja) + 350; // small gap between speakers
      if (idx === it.lines.length - 1) {
        const end = setTimeout(() => setPlaying(false), delay);
        timers.current.push(end);
      }
    });
  };

  const choose = (it: ChoukaiItem, idx: number) => {
    if (chosen != null) return;
    clearTimers();
    setChosen(idx);
    const isCorrect = idx === it.answerIndex;
    if (!answeredIds[it.id]) setAnsweredIds((p) => ({ ...p, [it.id]: true }));
    if (isCorrect) setCorrectIds((p) => ({ ...p, [it.id]: true }));
    app.track('choukai_answered', { id: it.id, correct: isCorrect });
  };

  // ---------------- list view ----------------
  if (!item) {
    const correctCount = Object.keys(correctIds).length;
    const answeredCount = Object.keys(answeredIds).length;
    return (
      <View>
        <Fade>
          <Title>{UI.screenTitle}</Title>
          <Muted>{UI.screenSub}</Muted>
          <Row>
            <Pill label={UI.answered(answeredCount, CHOUKAI_TOTAL)} />
            <Pill label={UI.score(correctCount, CHOUKAI_TOTAL)} />
          </Row>
        </Fade>

        {CHOUKAI_ITEMS.map((i, n) => {
          const done = answeredIds[i.id];
          const ok = correctIds[i.id];
          return (
            <Fade key={i.id} delay={40 + n * 20}>
              <Pressable onPress={() => openItem(i)} accessibilityRole="button" accessibilityLabel={`${i.situationKo}, ${i.level}`}>
                <Card>
                  <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                    <View style={{ flex: 1, paddingRight: 10 }}>
                      <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text, lineHeight: 22 }}>{i.situationKo}</Text>
                      <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 4 }}>
                        {i.lines.length}턴 대화 · 4지선다
                      </Text>
                    </View>
                    <View style={{ alignItems: 'flex-end' }}>
                      <LevelPill level={i.level} />
                      {done ? (
                        <Text style={{ marginTop: 6, fontSize: 16, fontWeight: '900', color: ok ? theme.colors.good : theme.colors.bad }}>
                          {ok ? '✓' : '✕'}
                        </Text>
                      ) : null}
                    </View>
                  </View>
                </Card>
              </Pressable>
            </Fade>
          );
        })}

        <Fade delay={120}>
          <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
        </Fade>
      </View>
    );
  }

  // ---------------- item view ----------------
  const answered = chosen != null;
  const isCorrect = answered && chosen === item.answerIndex;

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>{UI.screenTitle}</Title>
          <LevelPill level={item.level} />
        </View>
        <Muted>{item.situationKo}</Muted>
      </Fade>

      <Fade delay={60}>
        <Card style={{ alignItems: 'center' }}>
          <Pressable
            onPress={() => playDialogue(item)}
            accessibilityRole="button"
            accessibilityLabel={playing ? UI.playing : UI.play}
            style={{
              backgroundColor: playing ? theme.colors.card : color,
              borderColor: color,
              borderWidth: 1.5,
              borderRadius: 999,
              paddingVertical: 14,
              paddingHorizontal: 26,
              alignItems: 'center',
            }}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              {!playing ? <Icon name="play" size={16} color={'#fff'} /> : null}
              <Text style={{ fontSize: 17, fontWeight: '800', color: playing ? color : '#fff', marginLeft: playing ? 0 : 6 }}>
                {playing ? UI.playing : answered ? UI.replay : UI.play}
              </Text>
            </View>
          </Pressable>
          <Text style={{ marginTop: 10, color: theme.colors.subtext, fontSize: 13, textAlign: 'center' }}>
            A와 B의 대화가 순서대로 재생돼요. 스크립트는 답을 고른 뒤 볼 수 있어요.
          </Text>
        </Card>
      </Fade>

      <Fade delay={100}>
        <Card>
          <Text style={{ fontSize: 13, fontWeight: '800', color: theme.colors.subtext, marginBottom: 6 }}>{UI.question}</Text>
          <Text style={{ fontSize: 17, fontWeight: '800', color: theme.colors.text, lineHeight: 24, marginBottom: 6 }}>{item.question}</Text>
          {item.choices.map((c, idx) => {
            const isChosen = chosen === idx;
            const showCorrect = answered && idx === item.answerIndex;
            const showWrong = answered && isChosen && !isCorrect;
            const bg = showCorrect ? theme.colors.good + '22' : showWrong ? theme.colors.bad + '22' : theme.colors.card;
            const bd = showCorrect ? theme.colors.good : showWrong ? theme.colors.bad : theme.colors.border;
            return (
              <Pressable
                key={idx}
                onPress={() => choose(item, idx)}
                disabled={answered}
                accessibilityRole="button"
                accessibilityLabel={c}
                accessibilityState={{ selected: isChosen }}
                style={{
                  borderWidth: 1.5,
                  borderColor: bd,
                  backgroundColor: bg,
                  borderRadius: 12,
                  paddingVertical: 13,
                  paddingHorizontal: 14,
                  marginTop: 8,
                  flexDirection: 'row',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <Text style={{ fontSize: 16, color: theme.colors.text, fontWeight: isChosen || showCorrect ? '800' : '500' }}>{c}</Text>
                {showCorrect ? (
                  <Text style={{ color: theme.colors.good, fontWeight: '900' }}>✓</Text>
                ) : showWrong ? (
                  <Text style={{ color: theme.colors.bad, fontWeight: '900' }}>✕</Text>
                ) : null}
              </Pressable>
            );
          })}
        </Card>
      </Fade>

      {answered && (
        <Fade delay={60}>
          <Card style={{ borderColor: isCorrect ? theme.colors.good : color, borderWidth: 1.5 }}>
            <Text style={{ fontSize: 16, fontWeight: '800', color: isCorrect ? theme.colors.good : theme.colors.accentDark }}>
              {isCorrect ? UI.correct : UI.wrong}
            </Text>
            <Text style={{ fontSize: 13, fontWeight: '800', color: theme.colors.subtext, marginTop: 10, marginBottom: 4 }}>{UI.explanation}</Text>
            <Text style={{ fontSize: 15, color: theme.colors.text, lineHeight: 22 }}>{item.explanationKo}</Text>
          </Card>
        </Fade>
      )}

      {answered && (
        <Fade delay={90}>
          <Card>
            <Pressable
              onPress={() => setShowScript((s) => !s)}
              accessibilityRole="button"
              accessibilityLabel={showScript ? UI.hideScript : UI.showScript}
              style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}
            >
              <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.accentDark }}>{showScript ? UI.hideScript : UI.showScript}</Text>
              <Text style={{ fontSize: 15, fontWeight: '900', color: theme.colors.accentDark }}>{showScript ? '−' : '+'}</Text>
            </Pressable>
            {showScript && (
              <View style={{ marginTop: 12 }}>
                <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.subtext, marginBottom: 8 }}>{UI.script}</Text>
                {item.lines.map((line, idx) => (
                  <View key={idx} style={{ flexDirection: 'row', marginBottom: 12 }}>
                    <View
                      style={{
                        width: 26,
                        height: 26,
                        borderRadius: 13,
                        backgroundColor: line.speaker === 'A' ? color : theme.colors.subtext,
                        alignItems: 'center',
                        justifyContent: 'center',
                        marginRight: 10,
                        marginTop: 2,
                      }}
                    >
                      <Text style={{ color: '#fff', fontSize: 13, fontWeight: '900' }}>{line.speaker}</Text>
                    </View>
                    <View style={{ flex: 1 }}>
                      <FuriganaTokens tokens={line.tokens} size={20} />
                      <Pressable
                        onPress={() => app.speak(line.ja)}
                        accessibilityRole="button"
                        accessibilityLabel={`${line.speaker} 다시 듣기`}
                        style={{ marginTop: 4, alignSelf: 'flex-start' }}
                      >
                        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                          <Icon name="speaker" size={14} color={color} />
                          <Text style={{ fontSize: 13, color: color, fontWeight: '700', marginLeft: 6 }}>이 줄 듣기</Text>
                        </View>
                      </Pressable>
                    </View>
                  </View>
                ))}
              </View>
            )}
          </Card>
        </Fade>
      )}

      <Fade delay={120}>
        <Button title={UI.back} onPress={closeItem} color={color} />
        <Button title={UI.home} onPress={() => { clearTimers(); app.navigate('home'); }} secondary />
      </Fade>
    </View>
  );
}
