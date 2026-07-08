import React from 'react';
import { Text, View, Pressable } from 'react-native';
import Svg, { Circle, Line, Path } from 'react-native-svg';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Button, Card, Fade, FuriganaTokens, Muted, Pill, Row, Title } from '../components';
import { PITCH_WORDS, PITCH_WORD_TOTAL, type PitchPattern, type PitchWord } from '../pitch/pitchTrainerData';
import type { AppController } from '../store';

// Pitch-accent trainer (피치 악센트). A Renshuu-style differentiator: show the
// Tokyo High/Low contour for common words, let the learner hear it, and quiz the
// four accent-pattern types. Contour is derived from `accentPosition` so the data
// stays the single source of truth.

const KO_LABEL: Record<PitchPattern, string> = {
  heiban: '헤이반 (平板)',
  atamadaka: '아타마다카 (頭高)',
  nakadaka: '나카다카 (中高)',
  odaka: '오다카 (尾高)',
};

const KO_HINT: Record<PitchPattern, string> = {
  heiban: '첫 박만 낮고, 이후 계속 높음 (뒤 조사도 높음)',
  atamadaka: '첫 박만 높고, 바로 떨어짐',
  nakadaka: '낮게 시작해 올랐다가 단어 중간에서 떨어짐',
  odaka: '끝까지 높지만, 뒤에 붙는 조사에서 떨어짐',
};

const PATTERN_ORDER: PitchPattern[] = ['heiban', 'atamadaka', 'nakadaka', 'odaka'];

// Split a kana reading into mora: a small kana (ゃゅょ / ぁぃぅぇぉ / ゎ) attaches
// to the preceding kana; everything else (including っ and ー) is its own mora.
const SMALL = new Set(['ゃ', 'ゅ', 'ょ', 'ぁ', 'ぃ', 'ぅ', 'ぇ', 'ぉ', 'ゎ', 'ゃ']);
function splitMora(reading: string): string[] {
  const out: string[] = [];
  for (const ch of Array.from(reading)) {
    if (SMALL.has(ch) && out.length > 0) {
      out[out.length - 1] += ch;
    } else {
      out.push(ch);
    }
  }
  return out;
}

// Derive a High/Low value per mora from the standard accent number.
//   0  heiban    : L H H H ...
//   1  atamadaka : H L L L ...
//   k  drop after mora k (2..n): L H..H(k) L..L  (odaka when k === n)
function contour(mora: string[], accentPosition: number): boolean[] {
  const n = mora.length;
  const highs: boolean[] = new Array(n).fill(false);
  if (accentPosition === 0) {
    for (let i = 0; i < n; i++) highs[i] = i > 0; // L then all H
  } else if (accentPosition === 1) {
    highs[0] = true; // H then all L
  } else {
    for (let i = 0; i < n; i++) highs[i] = i > 0 && i < accentPosition; // L, rise, drop after k
  }
  return highs;
}

function PitchContour({ word, color }: { word: PitchWord; color: string }) {
  const { theme } = useTheme();
  const mora = splitMora(word.reading);
  const highs = contour(mora, word.accentPosition);
  // A trailing "particle" slot shows the odaka/heiban distinction after the word.
  const particleHigh = word.accentPosition === 0; // heiban keeps particle high
  const cells = mora.length + 1; // +1 for the particle marker
  const stepX = 34;
  const W = cells * stepX;
  const H = 60;
  const yHigh = 14;
  const yLow = 38;
  const wordPts = highs.map((h, i) => ({ x: stepX * i + stepX / 2, y: h ? yHigh : yLow }));
  const particleX = stepX * mora.length + stepX / 2;
  const particleY = particleHigh ? yHigh : yLow;

  let d = '';
  wordPts.forEach((p, i) => {
    d += i === 0 ? `M ${p.x} ${p.y}` : ` L ${p.x} ${p.y}`;
  });
  // dashed connector into the particle slot
  const lastWord = wordPts[wordPts.length - 1];

  return (
    <View style={{ marginTop: 8, alignItems: 'center' }}>
      <Svg width={W} height={H}>
        <Line x1={0} y1={yLow + 12} x2={W} y2={yLow + 12} stroke={theme.colors.border} strokeWidth={1} />
        <Path d={d} stroke={color} strokeWidth={2.5} fill="none" />
        <Line
          x1={lastWord.x}
          y1={lastWord.y}
          x2={particleX}
          y2={particleY}
          stroke={theme.colors.subtext}
          strokeWidth={1.5}
          strokeDasharray="3 3"
        />
        {wordPts.map((p, i) => (
          <Circle key={i} cx={p.x} cy={p.y} r={4.5} fill={color} />
        ))}
        <Circle cx={particleX} cy={particleY} r={4} fill="none" stroke={theme.colors.subtext} strokeWidth={1.5} />
      </Svg>
      <View style={{ flexDirection: 'row', width: W }}>
        {mora.map((m, i) => (
          <Text key={i} style={{ width: stepX, textAlign: 'center', fontSize: 13, color: theme.colors.text, fontWeight: '600' }}>
            {m}
          </Text>
        ))}
        <Text style={{ width: stepX, textAlign: 'center', fontSize: 13, color: theme.colors.subtext }}>が</Text>
      </View>
    </View>
  );
}

export function PitchAccentScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const color = personaColor(app.selectedPersonaId);

  const [mode, setMode] = React.useState<'browse' | 'quiz'>('browse');
  const [index, setIndex] = React.useState(0);
  // quiz state
  const [choices, setChoices] = React.useState<PitchPattern[]>(PATTERN_ORDER);
  const [picked, setPicked] = React.useState<PitchPattern | null>(null);
  const [score, setScore] = React.useState(0);
  const [answered, setAnswered] = React.useState(0);

  const word = PITCH_WORDS[index];

  const speakWord = () => app.speak(word.reading);

  const goBrowse = () => {
    setMode('browse');
    setPicked(null);
  };

  const startQuiz = () => {
    setMode('quiz');
    setIndex(0);
    setScore(0);
    setAnswered(0);
    setPicked(null);
    setChoices(shuffle(PATTERN_ORDER));
    app.track('pitch_practice', { mode: 'quiz', total: PITCH_WORD_TOTAL });
  };

  const nextBrowse = () => {
    app.track('pitch_practice', { mode: 'browse', wordJa: word.wordJa, pattern: word.pattern });
    setIndex((i) => (i + 1) % PITCH_WORD_TOTAL);
  };
  const prevBrowse = () => setIndex((i) => (i - 1 + PITCH_WORD_TOTAL) % PITCH_WORD_TOTAL);

  const pick = (p: PitchPattern) => {
    if (picked) return;
    setPicked(p);
    const correct = p === word.pattern;
    if (correct) setScore((s) => s + 1);
    setAnswered((a) => a + 1);
    app.track('pitch_practice', { mode: 'quiz', wordJa: word.wordJa, guess: p, correct });
  };

  const nextQuiz = () => {
    setPicked(null);
    setChoices(shuffle(PATTERN_ORDER));
    setIndex((i) => (i + 1) % PITCH_WORD_TOTAL);
  };

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>피치 악센트</Title>
          <Pill label={mode === 'browse' ? `${index + 1}/${PITCH_WORD_TOTAL}` : `점수 ${score}/${answered}`} color={color} />
        </View>
        <Muted>도쿄 표준 억양(고저)을 눈과 귀로 익혀요. 젓가락(箸)과 다리(橋)의 차이!</Muted>
      </Fade>

      {/* mode toggle */}
      <Fade delay={40}>
        <View style={{ flexDirection: 'row', marginTop: 12, marginBottom: 4 }}>
          <ModeTab label="둘러보기" active={mode === 'browse'} color={color} onPress={goBrowse} />
          <View style={{ width: 8 }} />
          <ModeTab label="퀴즈" active={mode === 'quiz'} color={color} onPress={startQuiz} />
        </View>
      </Fade>

      {/* word card */}
      <Fade delay={80}>
        <Card style={{ alignItems: 'center', paddingVertical: 24 }}>
          <FuriganaTokens tokens={word.tokens} size={34} color={color} />
          <Text style={{ fontSize: 15, color: theme.colors.subtext, marginTop: 6 }}>{word.reading}</Text>
          <Text style={{ fontSize: 17, color: theme.colors.text, fontWeight: '700', marginTop: 4 }}>{word.meaningKo}</Text>

          <PitchContour word={word} color={color} />

          <View style={{ marginTop: 12 }}>
            <Button icon="speaker" title="발음 듣기" onPress={speakWord} secondary color={color} />
          </View>

          {mode === 'browse' ? (
            <View style={{ alignItems: 'center', marginTop: 12 }}>
              <View style={{ backgroundColor: color, borderRadius: 999, paddingHorizontal: 16, paddingVertical: 7 }}>
                <Text style={{ color: '#fff', fontWeight: '800', fontSize: 15 }}>{KO_LABEL[word.pattern]}</Text>
              </View>
              <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 8, textAlign: 'center', paddingHorizontal: 6 }}>
                {KO_HINT[word.pattern]}
              </Text>
            </View>
          ) : null}
        </Card>
      </Fade>

      {/* mode-specific controls */}
      {mode === 'browse' ? (
        <Fade delay={120}>
          <Row>
            <View style={{ flex: 1, marginRight: 6 }}>
              <Button title="◀ 이전" onPress={prevBrowse} secondary color={color} />
            </View>
            <View style={{ flex: 1, marginLeft: 6 }}>
              <Button title="다음" onPress={nextBrowse} color={color} />
            </View>
          </Row>
        </Fade>
      ) : (
        <Fade delay={120}>
          <Muted>이 단어의 억양 패턴은?</Muted>
          <View style={{ marginTop: 8 }}>
            {choices.map((p) => {
              const isPicked = picked === p;
              const isAnswer = p === word.pattern;
              const revealed = picked != null;
              const bg =
                revealed && isAnswer
                  ? theme.colors.good
                  : revealed && isPicked
                  ? theme.colors.bad
                  : theme.colors.card;
              const fg = revealed && (isAnswer || isPicked) ? '#fff' : theme.colors.text;
              const border = revealed && isAnswer ? theme.colors.good : revealed && isPicked ? theme.colors.bad : theme.colors.border;
              return (
                <Pressable
                  key={p}
                  onPress={() => pick(p)}
                  accessibilityRole="button"
                  accessibilityLabel={KO_LABEL[p]}
                  accessibilityState={{ selected: isPicked }}
                >
                  <View
                    style={{
                      backgroundColor: bg,
                      borderColor: border,
                      borderWidth: 1.5,
                      borderRadius: theme.radius.md,
                      paddingVertical: 14,
                      paddingHorizontal: 16,
                      marginVertical: 5,
                    }}
                  >
                    <Text style={{ color: fg, fontSize: 16, fontWeight: '700' }}>
                      {KO_LABEL[p]}
                      {revealed && isAnswer ? '  ✓' : revealed && isPicked ? '  ✗' : ''}
                    </Text>
                    {revealed && isAnswer ? (
                      <Text style={{ color: '#fff', fontSize: 12, marginTop: 4, opacity: 0.9 }}>{KO_HINT[p]}</Text>
                    ) : null}
                  </View>
                </Pressable>
              );
            })}
          </View>
          {picked ? (
            <View style={{ marginTop: 8 }}>
              <Button title="다음 문제" onPress={nextQuiz} color={color} />
            </View>
          ) : null}
        </Fade>
      )}

      <Fade delay={160}>
        <View style={{ marginTop: 6 }}>
          <Button title="홈으로" onPress={() => app.navigate('home')} secondary />
        </View>
      </Fade>
    </View>
  );
}

function ModeTab({ label, active, color, onPress }: { label: string; active: boolean; color: string; onPress: () => void }) {
  const { theme } = useTheme();
  return (
    <Pressable onPress={onPress} accessibilityRole="button" accessibilityLabel={label} accessibilityState={{ selected: active }} style={{ flex: 1 }}>
      <View
        style={{
          backgroundColor: active ? color : theme.colors.card,
          borderColor: active ? color : theme.colors.border,
          borderWidth: 1.5,
          borderRadius: theme.radius.md,
          paddingVertical: 11,
          alignItems: 'center',
        }}
      >
        <Text style={{ color: active ? '#fff' : theme.colors.subtext, fontWeight: '800', fontSize: 15 }}>{label}</Text>
      </View>
    </Pressable>
  );
}

function shuffle<T>(arr: T[]): T[] {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}
