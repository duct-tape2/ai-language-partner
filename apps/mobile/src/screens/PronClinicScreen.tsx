import React from 'react';
import { Text, View, Pressable } from 'react-native';
import type { AppController } from '../store';
import { useTheme } from '../ThemeContext';
import { Card, Button, Title, Muted, Pill, Fade, FuriganaTokens } from '../components';
import { Icon } from '../icons';
import { personaColor } from '../personaStyle';
import { CLINIC, type ClinicCategory, type ClinicPair, type ClinicWord } from '../pronclinic/pronClinicData';

const KO = {
  title: '발음 클리닉',
  intro: '한국인이 헷갈리기 쉬운 발음을 최소대립쌍(비슷한 두 단어)으로 연습합니다. 카테고리를 골라 들어보세요.',
  demo: '데모: 모델 음성은 기기 TTS로 재생됩니다. 실제 발음 채점 백엔드는 없어요.',
  pairCount: (n: number) => `${n}개 대립쌍`,
  listenTap: '탭하면 발음이 재생돼요',
  diff: '차이',
  study: '학습',
  quiz: '듣고 구분하기',
  quizIntro: '한 단어를 들려드립니다. 방금 들은 쪽을 골라보세요.',
  playAgain: '다시 듣기',
  whichHeard: '어느 쪽을 들으셨나요?',
  correct: '정답',
  wrong: '오답',
  next: '다음 문제',
  score: (c: number, t: number) => `점수 ${c} / ${t}`,
  reset: '처음부터',
  back: '닫기',
  home: '홈으로',
};

const CAT_ICON: Record<string, string> = {
  chouon: '長',
  sokuon: 'ッ',
  hatsuon: 'ン',
  devoicing: '無',
  youon: '拗',
  accent: '高',
};

type Mode = 'study' | 'quiz';

export function PronClinicScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const accent = personaColor(app.selectedPersonaId);
  const [openKey, setOpenKey] = React.useState<string | null>(null);
  const [mode, setMode] = React.useState<Mode>('study');

  const open = openKey ? CLINIC.find((c) => c.key === openKey) ?? null : null;

  const openCat = (c: ClinicCategory) => {
    setOpenKey(c.key);
    setMode('study');
    app.track('pronclinic_opened', { key: c.key });
  };

  if (open) {
    return (
      <View>
        <Fade>
          <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <Title>{open.titleKo}</Title>
            <Pressable onPress={() => setOpenKey(null)} accessibilityRole="button" accessibilityLabel={KO.back}>
              <Text style={{ fontSize: 14, fontWeight: '700', color: theme.colors.subtext, paddingHorizontal: 8, paddingVertical: 4 }}>
                {KO.back}
              </Text>
            </Pressable>
          </View>
          <Muted>{open.explainKo}</Muted>
        </Fade>

        <View style={{ flexDirection: 'row', marginTop: 14, marginBottom: 8 }}>
          <ModeTab label={KO.study} active={mode === 'study'} accent={accent} onPress={() => setMode('study')} />
          <ModeTab label={KO.quiz} active={mode === 'quiz'} accent={accent} onPress={() => setMode('quiz')} />
        </View>

        {mode === 'study' ? (
          <StudyView cat={open} accent={accent} onSpeak={(w) => app.speak(w.ja)} />
        ) : (
          <QuizView cat={open} accent={accent} onSpeak={(w) => app.speak(w.ja)} />
        )}

        <View style={{ marginTop: 8, marginBottom: 24 }}>
          <Button title={KO.home} secondary onPress={() => app.navigate('home')} />
        </View>
      </View>
    );
  }

  return (
    <View>
      <Fade>
        <Title>{KO.title}</Title>
        <Muted>{KO.intro}</Muted>
      </Fade>

      <View
        style={{
          marginTop: 12,
          marginBottom: 6,
          backgroundColor: theme.colors.chip,
          borderRadius: theme.radius.md,
          paddingVertical: 8,
          paddingHorizontal: 12,
        }}
      >
        <Text style={{ fontSize: 12, color: theme.colors.chipText, fontWeight: '600', lineHeight: 18 }}>{KO.demo}</Text>
      </View>

      {CLINIC.map((c, i) => (
        <Fade key={c.key} delay={Math.min(i, 8) * 24}>
          <Pressable onPress={() => openCat(c)} accessibilityRole="button" accessibilityLabel={c.titleKo}>
            <View
              style={{
                backgroundColor: theme.colors.card,
                borderRadius: theme.radius.md,
                borderWidth: 1,
                borderColor: theme.colors.border,
                paddingVertical: 14,
                paddingHorizontal: 16,
                marginBottom: 10,
                flexDirection: 'row',
                alignItems: 'center',
              }}
            >
              <View
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: 10,
                  backgroundColor: theme.colors.chip,
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginRight: 12,
                }}
              >
                <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.chipText }}>{CAT_ICON[c.key] ?? '音'}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text }}>{c.titleKo}</Text>
                <Text style={{ fontSize: 12, color: theme.colors.subtext, marginTop: 2 }}>{KO.pairCount(c.pairs.length)}</Text>
              </View>
              <Text style={{ fontSize: 20, color: theme.colors.subtext, marginLeft: 8 }}>{'>'}</Text>
            </View>
          </Pressable>
        </Fade>
      ))}

      <View style={{ marginTop: 8, marginBottom: 24 }}>
        <Button title={KO.home} secondary onPress={() => app.navigate('home')} />
      </View>
    </View>
  );
}

function ModeTab({ label, active, accent, onPress }: { label: string; active: boolean; accent: string; onPress: () => void }) {
  const { theme } = useTheme();
  return (
    <Pressable onPress={onPress} style={{ flex: 1 }} accessibilityRole="button" accessibilityLabel={label} accessibilityState={{ selected: active }}>
      <View
        style={{
          paddingVertical: 10,
          alignItems: 'center',
          marginHorizontal: 3,
          borderRadius: theme.radius.md,
          backgroundColor: active ? accent : theme.colors.chip,
          borderWidth: 1,
          borderColor: active ? accent : theme.colors.border,
        }}
      >
        <Text style={{ color: active ? '#fff' : theme.colors.chipText, fontSize: 14, fontWeight: '800' }}>{label}</Text>
      </View>
    </Pressable>
  );
}

function WordCard({ word, accent, onSpeak }: { word: ClinicWord; accent: string; onSpeak: () => void }) {
  const { theme } = useTheme();
  return (
    <Pressable onPress={onSpeak} accessibilityRole="button" accessibilityLabel={`${word.ja}, ${word.ko}`}>
      <View
        style={{
          flex: 1,
          backgroundColor: theme.colors.card,
          borderRadius: theme.radius.md,
          borderWidth: 1.5,
          borderColor: accent,
          padding: 12,
          minHeight: 96,
          justifyContent: 'space-between',
        }}
      >
        <FuriganaTokens tokens={word.tokens} size={24} color={accent} />
        <Text style={{ fontSize: 13, color: theme.colors.text, marginTop: 8, fontWeight: '600' }}>{word.ko}</Text>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 6 }}>
          <Icon name="play" size={11} color={theme.colors.subtext} />
          <Text style={{ fontSize: 11, color: theme.colors.subtext, marginLeft: 6 }}>{KO.listenTap}</Text>
        </View>
      </View>
    </Pressable>
  );
}

function StudyView({ cat, accent, onSpeak }: { cat: ClinicCategory; accent: string; onSpeak: (w: ClinicWord) => void }) {
  const { theme } = useTheme();
  return (
    <View>
      {cat.pairs.map((p, i) => (
        <Fade key={i} delay={Math.min(i, 8) * 24}>
          <Card>
            <View style={{ flexDirection: 'row' }}>
              <View style={{ flex: 1, marginRight: 6 }}>
                <WordCard word={p.a} accent={accent} onSpeak={() => onSpeak(p.a)} />
              </View>
              <View style={{ flex: 1, marginLeft: 6 }}>
                <WordCard word={p.b} accent={accent} onSpeak={() => onSpeak(p.b)} />
              </View>
            </View>
            <View
              style={{
                marginTop: 12,
                backgroundColor: theme.colors.accentSoft,
                borderRadius: theme.radius.md,
                padding: 12,
                borderWidth: 1,
                borderColor: theme.colors.border,
              }}
            >
              <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.accentDark, marginBottom: 4 }}>{KO.diff}</Text>
              <Text style={{ fontSize: 14, color: theme.colors.text, lineHeight: 22 }}>{p.hintKo}</Text>
            </View>
          </Card>
        </Fade>
      ))}
    </View>
  );
}

type QuizState = {
  idx: number; // index into cat.pairs
  answer: 'a' | 'b'; // which side is the correct answer for this round
  picked: 'a' | 'b' | null;
  correct: number;
  answered: number;
};

function makeRound(idx: number): Pick<QuizState, 'idx' | 'answer' | 'picked'> {
  return { idx, answer: Math.random() < 0.5 ? 'a' : 'b', picked: null };
}

function QuizView({ cat, accent, onSpeak }: { cat: ClinicCategory; accent: string; onSpeak: (w: ClinicWord) => void }) {
  const { theme } = useTheme();
  const [st, setSt] = React.useState<QuizState>(() => ({ ...makeRound(0), correct: 0, answered: 0 }));

  const pair: ClinicPair = cat.pairs[st.idx];
  const target = st.answer === 'a' ? pair.a : pair.b;
  const revealed = st.picked != null;
  const isRight = st.picked === st.answer;

  const play = () => onSpeak(target);

  const pick = (side: 'a' | 'b') => {
    if (revealed) return;
    const ok = side === st.answer;
    setSt((s) => ({ ...s, picked: side, correct: s.correct + (ok ? 1 : 0), answered: s.answered + 1 }));
  };

  const next = () => {
    const nextIdx = (st.idx + 1) % cat.pairs.length;
    setSt((s) => ({ ...s, ...makeRound(nextIdx) }));
  };

  const reset = () => setSt({ ...makeRound(0), correct: 0, answered: 0 });

  // Auto-play once when a new round mounts.
  React.useEffect(() => {
    play();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [st.idx, st.answer]);

  const optionStyle = (side: 'a' | 'b') => {
    if (!revealed) return { border: theme.colors.border, bg: theme.colors.card };
    if (side === st.answer) return { border: theme.colors.good, bg: theme.colors.card };
    if (side === st.picked) return { border: theme.colors.bad, bg: theme.colors.card };
    return { border: theme.colors.border, bg: theme.colors.card };
  };

  return (
    <View>
      <Card>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <Muted>{KO.quizIntro}</Muted>
          <Pill label={KO.score(st.correct, st.answered)} color={accent} />
        </View>

        <Button icon="play" title={KO.playAgain} onPress={play} color={accent} />

        <Text style={{ fontSize: 13, fontWeight: '800', color: theme.colors.accentDark, marginTop: 14, marginBottom: 8 }}>
          {KO.whichHeard}
        </Text>

        <View style={{ flexDirection: 'row' }}>
          {(['a', 'b'] as const).map((side) => {
            const w = side === 'a' ? pair.a : pair.b;
            const s = optionStyle(side);
            return (
              <View key={side} style={{ flex: 1, marginLeft: side === 'a' ? 0 : 6, marginRight: side === 'a' ? 6 : 0 }}>
                <Pressable onPress={() => pick(side)} accessibilityRole="button" accessibilityLabel={`${w.ja}, ${w.ko}`} accessibilityState={{ disabled: revealed }}>
                  <View
                    style={{
                      backgroundColor: s.bg,
                      borderRadius: theme.radius.md,
                      borderWidth: 2,
                      borderColor: s.border,
                      padding: 12,
                      minHeight: 92,
                      justifyContent: 'space-between',
                    }}
                  >
                    <FuriganaTokens tokens={w.tokens} size={22} color={accent} />
                    <Text style={{ fontSize: 13, color: theme.colors.text, marginTop: 8, fontWeight: '600' }}>{w.ko}</Text>
                  </View>
                </Pressable>
              </View>
            );
          })}
        </View>

        {revealed ? (
          <Fade>
            <View
              style={{
                marginTop: 14,
                backgroundColor: isRight ? theme.colors.accentSoft : theme.colors.card,
                borderRadius: theme.radius.md,
                borderWidth: 1,
                borderColor: isRight ? theme.colors.good : theme.colors.bad,
                padding: 12,
              }}
            >
              <Text style={{ fontSize: 14, fontWeight: '900', color: isRight ? theme.colors.good : theme.colors.bad, marginBottom: 6 }}>
                {isRight ? KO.correct : KO.wrong}
              </Text>
              <Text style={{ fontSize: 13, color: theme.colors.subtext, marginBottom: 8 }}>
                {'정답: ' + target.ja + ' (' + target.ko + ')'}
              </Text>
              <Text style={{ fontSize: 14, color: theme.colors.text, lineHeight: 22 }}>{pair.hintKo}</Text>
              <View style={{ marginTop: 10 }}>
                <Button title={KO.next} onPress={next} color={accent} />
              </View>
            </View>
          </Fade>
        ) : null}

        <View style={{ marginTop: 12 }}>
          <Button title={KO.reset} secondary onPress={reset} />
        </View>
      </Card>
    </View>
  );
}
