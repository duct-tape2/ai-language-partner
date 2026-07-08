import React from 'react';
import { Text, View, Pressable } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Button, Card, Fade, FuriganaTokens, Muted, Pill, ProgressRing, Row, Title, DiffText } from '../components';
import { PRON_PHRASES, PRON_PHRASE_TOTAL, type PronPhrase } from '../pronunciation/pronPhrases';
import { diffChars, accuracyOf, type DiffSeg } from '../text';
import { api } from '../api/client';
import type { PronunciationScore } from '../../../../packages/shared/src/types';
import type { AppController } from '../store';

// Pronunciation feedback (발음 피드백). Targets 회화 실전성: shows a target phrase,
// lets the learner hear it, then "record & score" runs STT + the pronunciation
// scoring endpoint and returns a ProgressRing score, rating, Korean feedback, and
// a per-character diff hint. Honest: when the provider is mock we show a demo
// badge and drive the scorer with a deterministic near-miss transcript so the
// char-diff is meaningful instead of fake-perfect.

type Result = {
  score: PronunciationScore;
  said: string;
  diff: DiffSeg[];
  accuracy: number;
};

const RATING_KO: Record<string, string> = {
  excellent: '아주 좋아요',
  good: '좋아요',
  fair: '보통',
  poor: '더 연습해요',
};

function ratingLabel(rating: string): string {
  return RATING_KO[rating] ?? rating;
}

function ratingColor(score: number, theme: ReturnType<typeof useTheme>['theme']): string {
  if (score >= 85) return theme.colors.good;
  if (score >= 60) return theme.colors.near;
  return theme.colors.bad;
}

// In mock mode the STT endpoint just echoes whatever mockText we pass and the
// scorer returns a fixed demo value. To make the demo honest AND useful, derive a
// plausible near-miss transcript from the phrase so the char-diff shows real
// misses instead of a perfect match. Drops one non-punctuation character.
function mockNearMiss(ja: string): string {
  const chars = Array.from(ja);
  const dropIdx = chars.findIndex((c, i) => i >= 2 && !/[。、！？!?\s]/.test(c));
  if (dropIdx < 0) return ja;
  return chars.filter((_, i) => i !== dropIdx).join('');
}

export function PronunciationScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const color = personaColor(app.selectedPersonaId);

  const [index, setIndex] = React.useState(0);
  const [scoring, setScoring] = React.useState(false);
  const [result, setResult] = React.useState<Result | null>(null);

  const phrase: PronPhrase = PRON_PHRASES[index];
  const isDemo = result != null && result.score.provider === 'mock';
  // Track the live index so a slow (real-mode) scoring round-trip that resolves
  // after the user has navigated to another phrase is discarded, not misattributed.
  const indexRef = React.useRef(index);
  React.useEffect(() => {
    indexRef.current = index;
  }, [index]);

  const speak = () => app.speak(phrase.ja);

  const advance = (dir: 1 | -1) => {
    setResult(null);
    setIndex((i) => (i + dir + PRON_PHRASE_TOTAL) % PRON_PHRASE_TOTAL);
  };

  const scoreNow = async () => {
    if (scoring) return;
    const startIndex = index;
    setScoring(true);
    setResult(null);
    try {
      // Real mode: transcribeAudio ignores the hint and returns the actual STT
      // text. Mock mode: it echoes mockText, so feed a deterministic near-miss.
      const stt = await api.transcribeAudio(mockNearMiss(phrase.ja));
      const said = stt.text;
      const score = await api.scorePronunciation(phrase.ja, said);
      // Discard a stale result if the user navigated to another phrase mid-scoring.
      if (startIndex !== indexRef.current) return;
      const diff = diffChars(phrase.ja, said);
      const accuracy = accuracyOf(diff);
      setResult({ score, said, diff, accuracy });
      app.track('pron_scored', { id: phrase.id, score: score.score });
    } finally {
      setScoring(false);
    }
  };

  const wrongChars = result ? result.diff.filter((s) => s.status === 'wrong').map((s) => s.ch) : [];

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>발음 피드백</Title>
          <Pill label={`${index + 1}/${PRON_PHRASE_TOTAL}`} color={color} />
        </View>
        <Muted>문장을 듣고 따라 말한 뒤 채점받아요. 글자별로 어디를 틀렸는지 짚어줍니다.</Muted>
      </Fade>

      {/* target phrase */}
      <Fade delay={60}>
        <Card style={{ alignItems: 'center', paddingVertical: 24 }}>
          <Row>
            <Pill label={phrase.level} color={color} />
          </Row>
          <View style={{ marginTop: 6 }}>
            <FuriganaTokens tokens={phrase.tokens} size={30} color={color} />
          </View>
          <Text style={{ fontSize: 16, color: theme.colors.text, fontWeight: '700', marginTop: 10, textAlign: 'center' }}>{phrase.ko}</Text>
          <View style={{ marginTop: 14 }}>
            <Button icon="speaker" title="발음 듣기" onPress={speak} secondary color={color} />
          </View>
        </Card>
      </Fade>

      {/* score action */}
      <Fade delay={100}>
        <Button
          icon="mic"
          title={scoring ? '채점 중...' : '녹음해서 채점'}
          onPress={scoreNow}
          disabled={scoring}
          color={color}
        />
      </Fade>

      {/* result */}
      {result ? (
        <Fade delay={20}>
          <Card style={{ alignItems: 'center' }}>
            {isDemo ? (
              <View style={{ backgroundColor: theme.colors.chip, borderRadius: 999, paddingHorizontal: 12, paddingVertical: 5, marginBottom: 12 }}>
                <Text style={{ color: theme.colors.chipText, fontSize: 12, fontWeight: '700' }}>데모 모드 - 예시 채점 결과예요</Text>
              </View>
            ) : null}

            <ProgressRing
              pct={Math.min(1, Math.max(0, result.score.score / 100))}
              color={ratingColor(result.score.score, theme)}
              size={140}
              stroke={14}
              centerTop={`${result.score.score}`}
              centerBottom="점"
            />

            <View style={{ backgroundColor: ratingColor(result.score.score, theme), borderRadius: 999, paddingHorizontal: 16, paddingVertical: 7, marginTop: 12 }}>
              <Text style={{ color: '#fff', fontWeight: '800', fontSize: 15 }}>{ratingLabel(result.score.rating)}</Text>
            </View>

            {result.score.feedbackKo ? (
              <Text style={{ fontSize: 15, color: theme.colors.text, marginTop: 12, textAlign: 'center', lineHeight: 22 }}>
                {result.score.feedbackKo}
              </Text>
            ) : null}

            {/* per-character diff hint */}
            <View style={{ marginTop: 16, alignItems: 'center' }}>
              <Text style={{ fontSize: 12, color: theme.colors.subtext, marginBottom: 6 }}>인식된 발음 (글자별 대조)</Text>
              <DiffText segs={result.diff} size={22} />
              {wrongChars.length ? (
                <Text style={{ fontSize: 13, color: theme.colors.bad, marginTop: 8, textAlign: 'center' }}>
                  다시 짚어볼 글자: {wrongChars.join(' , ')}
                </Text>
              ) : (
                <Text style={{ fontSize: 13, color: theme.colors.good, marginTop: 8 }}>모든 글자가 정확해요!</Text>
              )}
              <Text style={{ fontSize: 11, color: theme.colors.subtext, marginTop: 6 }}>
                글자 일치율 {result.accuracy}%
              </Text>
            </View>

            <View style={{ marginTop: 16 }}>
              <Button icon="speaker" title="다시 듣기" onPress={speak} secondary color={color} />
            </View>
          </Card>
        </Fade>
      ) : null}

      {/* navigation */}
      <Fade delay={140}>
        <Row>
          <View style={{ flex: 1, marginRight: 6 }}>
            <Button title="◀ 이전" onPress={() => advance(-1)} secondary color={color} />
          </View>
          <View style={{ flex: 1, marginLeft: 6 }}>
            <Button title="다음" onPress={() => advance(1)} color={color} />
          </View>
        </Row>
      </Fade>

      <Fade delay={180}>
        <View style={{ marginTop: 6 }}>
          <Button title="홈으로" onPress={() => app.navigate('home')} secondary />
        </View>
      </Fade>
    </View>
  );
}
