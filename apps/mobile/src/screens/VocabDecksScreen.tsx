import React from 'react';
import { Text, View, Pressable } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Card, Button, Title, Muted, Pill, Fade, Row, FuriganaTokens } from '../components';
import { Icon } from '../icons';
import { DECKS, deckById, VOCAB_TOTAL } from '../vocab/vocabDecks';
import type { VocabDeck, VocabWord } from '../vocab/vocabDecks';
import type { AppController } from '../store';

// 테마별 어휘 덱: 주제별(일상/음식/여행/감정/가족/비즈니스) N5~N4 어휘를
// 플래시카드로 학습. 발음을 탭하면 페르소나 목소리로 읽어 주고, 각 단어를
// '아는 단어 / 모르는 단어'로 셀프 체크해 진행을 확인한다. 정적 데이터.
const UI = {
  title: '테마별 어휘',
  subtitle: '주제별로 묶은 N5~N4 단어예요. 덱을 골라 카드를 넘기며 외우고, 발음을 눌러 들어보세요.',
  total: (n: number) => `단어 ${n}개`,
  count: (n: number) => `${n}단어`,
  listen: '발음 듣기',
  know: '아는 단어',
  dontKnow: '모르는 단어',
  next: '다음 카드',
  prev: '이전 카드',
  restart: '처음부터',
  example: '예문',
  progress: (i: number, n: number) => `${i} / ${n}`,
  scoreKnow: (n: number) => `아는 단어 ${n}`,
  scoreDont: (n: number) => `모르는 단어 ${n}`,
  done: '이 덱을 한 바퀴 돌았어요',
  back: '덱 목록으로',
  home: '홈으로',
};

export function VocabDecksScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const accent = personaColor(app.selectedPersonaId);
  const [openId, setOpenId] = React.useState<string | null>(null);
  const [idx, setIdx] = React.useState(0);
  const [known, setKnown] = React.useState<Set<number>>(new Set());
  const [unknown, setUnknown] = React.useState<Set<number>>(new Set());

  const deck = openId ? deckById(openId) : undefined;

  const openDeck = (d: VocabDeck) => {
    setOpenId(d.id);
    setIdx(0);
    setKnown(new Set());
    setUnknown(new Set());
    app.track('vocab_deck_opened', { deck: d.id });
  };

  const backToList = () => {
    setOpenId(null);
    setIdx(0);
    setKnown(new Set());
    setUnknown(new Set());
  };

  // ----- deck flashcard view -----
  if (deck) {
    const total = deck.words.length;
    const word: VocabWord = deck.words[idx];
    const atEnd = idx >= total - 1;

    const mark = (isKnown: boolean) => {
      setKnown((prev) => {
        const next = new Set(prev);
        if (isKnown) next.add(idx);
        else next.delete(idx);
        return next;
      });
      setUnknown((prev) => {
        const next = new Set(prev);
        if (!isKnown) next.add(idx);
        else next.delete(idx);
        return next;
      });
      if (!atEnd) setIdx((i) => i + 1);
    };

    const markedKnown = known.has(idx);
    const markedUnknown = unknown.has(idx);

    return (
      <View>
        <Fade>
          <Row>
            <Title>{deck.emoji} {deck.title}</Title>
            <View style={{ width: 8 }} />
            <Pill label={UI.progress(idx + 1, total)} color={accent} />
          </Row>
          <View style={{ flexDirection: 'row', marginTop: 4 }}>
            <Text style={{ fontSize: 13, fontWeight: '800', color: theme.colors.good, marginRight: 14 }}>{UI.scoreKnow(known.size)}</Text>
            <Text style={{ fontSize: 13, fontWeight: '800', color: theme.colors.bad }}>{UI.scoreDont(unknown.size)}</Text>
          </View>
        </Fade>

        <Fade delay={60}>
          <Card
            style={{
              alignItems: 'center',
              borderWidth: 1.5,
              borderColor: markedKnown ? theme.colors.good : markedUnknown ? theme.colors.bad : theme.colors.border,
            }}
          >
            <View style={{ marginTop: 4, marginBottom: 6 }}>
              <FuriganaTokens tokens={word.tokens} size={34} color={accent} />
            </View>
            <Text style={{ fontSize: 14, color: theme.colors.subtext, marginBottom: 2 }}>{word.reading}</Text>
            <Text style={{ fontSize: 22, fontWeight: '900', color: theme.colors.text, marginTop: 6, textAlign: 'center' }}>{word.meaningKo}</Text>
            <View style={{ marginTop: 12 }}>
              <Button title={UI.listen} onPress={() => app.speak(word.wordJa)} secondary color={accent} />
            </View>
          </Card>
        </Fade>

        {word.exampleJa ? (
          <Fade delay={100}>
            <Card>
              <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.subtext, letterSpacing: 1, marginBottom: 6 }}>{UI.example}</Text>
              <Pressable
                onPress={() => app.speak(word.exampleJa as string)}
                accessibilityRole="button"
                accessibilityLabel={`예문 발음 듣기, ${word.exampleJa}`}
              >
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                  <Text style={{ fontSize: 18, fontWeight: '800', color: theme.colors.text, lineHeight: 27 }}>{word.exampleJa}</Text>
                  <View style={{ width: 8 }} />
                  <Icon name="speaker" size={18} color={theme.colors.text} />
                </View>
              </Pressable>
              {word.exampleKo ? <Text style={{ fontSize: 14, color: theme.colors.subtext, marginTop: 6, lineHeight: 21 }}>{word.exampleKo}</Text> : null}
            </Card>
          </Fade>
        ) : null}

        <Fade delay={140}>
          <View style={{ flexDirection: 'row', marginTop: 2 }}>
            <View style={{ flex: 1, marginRight: 5 }}>
              <Button title={UI.dontKnow} onPress={() => mark(false)} color={theme.colors.bad} secondary />
            </View>
            <View style={{ flex: 1, marginLeft: 5 }}>
              <Button title={UI.know} onPress={() => mark(true)} color={theme.colors.good} />
            </View>
          </View>

          <View style={{ flexDirection: 'row', marginTop: 2 }}>
            <View style={{ flex: 1, marginRight: 5 }}>
              <Button title={UI.prev} onPress={() => setIdx((i) => Math.max(0, i - 1))} secondary disabled={idx === 0} />
            </View>
            <View style={{ flex: 1, marginLeft: 5 }}>
              <Button title={UI.next} onPress={() => setIdx((i) => Math.min(total - 1, i + 1))} secondary color={accent} disabled={atEnd} />
            </View>
          </View>

          {atEnd ? (
            <Card style={{ borderColor: theme.colors.good, borderWidth: 1.5, marginTop: 6 }}>
              <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.good }}>{UI.done}</Text>
              <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 4 }}>{UI.scoreKnow(known.size)} · {UI.scoreDont(unknown.size)}</Text>
            </Card>
          ) : null}

          <Button title={UI.restart} onPress={() => { setIdx(0); setKnown(new Set()); setUnknown(new Set()); }} secondary />
          <Button title={UI.back} onPress={backToList} secondary color={accent} />
          <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
        </Fade>
      </View>
    );
  }

  // ----- deck picker view -----
  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>{UI.title}</Title>
          <Pill label={UI.total(VOCAB_TOTAL)} color={accent} />
        </View>
        <Muted>{UI.subtitle}</Muted>
      </Fade>

      <Fade delay={60}>
        <View style={{ marginTop: 12 }}>
          {DECKS.map((d) => (
            <Pressable
              key={d.id}
              onPress={() => openDeck(d)}
              accessibilityRole="button"
              accessibilityLabel={`${d.title}, ${UI.count(d.words.length)}, ${d.descKo}`}
            >
              <View
                style={{
                  flexDirection: 'row',
                  alignItems: 'center',
                  backgroundColor: theme.colors.card,
                  borderRadius: theme.radius.md,
                  borderWidth: 1,
                  borderColor: theme.colors.border,
                  paddingVertical: 14,
                  paddingHorizontal: 16,
                  marginBottom: 8,
                }}
              >
                <View
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: 12,
                    backgroundColor: theme.colors.accentSoft,
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginRight: 14,
                  }}
                >
                  <Text style={{ fontSize: 24 }}>{d.emoji}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <Text style={{ fontSize: 17, fontWeight: '800', color: theme.colors.text }}>{d.title}</Text>
                    <View style={{ width: 8 }} />
                    <Text style={{ fontSize: 12, fontWeight: '700', color: accent }}>{UI.count(d.words.length)}</Text>
                  </View>
                  <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 2, lineHeight: 19 }}>{d.descKo}</Text>
                </View>
                <Text style={{ fontSize: 20, color: theme.colors.subtext, marginLeft: 8 }}>›</Text>
              </View>
            </Pressable>
          ))}
        </View>
      </Fade>

      <Fade delay={120}>
        <View style={{ height: 8 }} />
        <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
      </Fade>
    </View>
  );
}
