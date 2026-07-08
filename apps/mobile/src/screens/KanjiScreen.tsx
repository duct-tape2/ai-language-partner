import React from 'react';
import { Text, TextInput, View, Pressable } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Card, Button, Title, Muted, Pill, Fade, Row, FuriganaTokens } from '../components';
import { Icon } from '../icons';
import type { AppController } from '../store';
import { kanjiByLevel, type KanjiEntry, type KanjiLevel } from '../kanji/kanjiData';

// First paint stays cheap even for the 646-kanji ALL list by rendering a page at
// a time (PAGE) instead of every tile synchronously; "더 보기" grows the window.
const PAGE = 60;

// Kanji study module: browse N5/N4 kanji, tap one to see a full breakdown
// (on/kun readings, meaning, radical, stroke count, mnemonic, example word).
// Fully offline; data is hand-authored in ../kanji/kanjiData.

type Filter = 'ALL' | KanjiLevel;

const L = {
  title: '한자 학습',
  subtitle: '부수와 니모닉으로 한자를 오래 기억하세요',
  all: '전체',
  onyomi: '음독 (音読)',
  kunyomi: '훈독 (訓読)',
  meaning: '뜻',
  radical: '부수',
  strokes: '획수',
  strokesUnit: '획',
  mnemonic: '기억법',
  example: '예시 단어',
  noReading: '-',
  back: '목록으로',
  home: '홈으로',
  countSuffix: '자',
};

function LevelChip({
  label,
  active,
  color,
  onPress,
}: {
  label: string;
  active: boolean;
  color: string;
  onPress: () => void;
}) {
  const { theme } = useTheme();
  return (
    <Pressable onPress={onPress} accessibilityRole="button" accessibilityLabel={label} accessibilityState={{ selected: active }}>
      <View
        style={{
          backgroundColor: active ? color : theme.colors.chip,
          borderRadius: 999,
          paddingHorizontal: 16,
          paddingVertical: 9,
          marginRight: 8,
          marginTop: 8,
          borderWidth: 1,
          borderColor: active ? color : theme.colors.border,
        }}
      >
        <Text style={{ color: active ? '#fff' : theme.colors.chipText, fontSize: 14, fontWeight: '700' }}>{label}</Text>
      </View>
    </Pressable>
  );
}

function KanjiTile({ entry, color, onPress }: { entry: KanjiEntry; color: string; onPress: () => void }) {
  const { theme } = useTheme();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`${entry.kanji} ${entry.meaningKo}`}
      style={{ width: '31%', marginBottom: 10 }}
    >
      <View
        style={{
          backgroundColor: theme.colors.card,
          borderRadius: theme.radius.md,
          borderWidth: 1,
          borderColor: theme.colors.border,
          paddingVertical: 14,
          alignItems: 'center',
        }}
      >
        <Text style={{ fontSize: 40, fontWeight: '900', color: theme.colors.text }}>{entry.kanji}</Text>
        <Text style={{ fontSize: 12, color: theme.colors.subtext, marginTop: 4 }} numberOfLines={1}>
          {entry.meaningKo}
        </Text>
        <View
          style={{
            position: 'absolute',
            top: 6,
            right: 8,
          }}
        >
          <Text style={{ fontSize: 10, fontWeight: '800', color }}>{entry.level}</Text>
        </View>
      </View>
    </Pressable>
  );
}

function ReadingRow({ label, values, color }: { label: string; values: string[]; color: string }) {
  const { theme } = useTheme();
  return (
    <View style={{ marginTop: 12 }}>
      <Text style={{ fontSize: 13, fontWeight: '700', color: theme.colors.subtext, marginBottom: 6 }}>{label}</Text>
      <Row>
        {values.length === 0 ? (
          <Text style={{ fontSize: 15, color: theme.colors.subtext }}>{L.noReading}</Text>
        ) : (
          values.map((v, i) => (
            <View
              key={i}
              style={{
                backgroundColor: theme.colors.chip,
                borderRadius: 8,
                paddingHorizontal: 10,
                paddingVertical: 6,
                marginRight: 8,
                marginBottom: 8,
              }}
            >
              <Text style={{ fontSize: 16, fontWeight: '700', color }}>{v}</Text>
            </View>
          ))
        )}
      </Row>
    </View>
  );
}

function KanjiDetail({ entry, color, onBack, app }: { entry: KanjiEntry; color: string; onBack: () => void; app: AppController }) {
  const { theme } = useTheme();
  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
          <Pressable onPress={onBack} accessibilityRole="button" accessibilityLabel={L.back}>
            <Text style={{ fontSize: 16, fontWeight: '700', color }}>{'<  ' + L.back}</Text>
          </Pressable>
          <Pill label={entry.level} color={color} />
        </View>
      </Fade>

      <Fade delay={40}>
        <Card style={{ alignItems: 'center', paddingVertical: 26 }}>
          <Text style={{ fontSize: 96, fontWeight: '900', color: theme.colors.text, lineHeight: 108 }}>{entry.kanji}</Text>
          <Text style={{ fontSize: 20, fontWeight: '800', color: theme.colors.text, marginTop: 4 }}>{entry.meaningKo}</Text>
          <Row>
            <Pill label={`${L.strokes} ${entry.strokeCount}${L.strokesUnit}`} />
            <Pill label={`${L.radical} ${entry.radical}`} />
          </Row>
        </Card>
      </Fade>

      <Fade delay={90}>
        <Card>
          <ReadingRow label={L.onyomi} values={entry.onyomi} color={color} />
          <ReadingRow label={L.kunyomi} values={entry.kunyomi} color={theme.colors.text} />
        </Card>
      </Fade>

      <Fade delay={140}>
        <Card>
          <Text style={{ fontSize: 13, fontWeight: '700', color: theme.colors.subtext, marginBottom: 6 }}>{L.radical}</Text>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <View
              style={{
                width: 52,
                height: 52,
                borderRadius: theme.radius.sm,
                backgroundColor: theme.colors.accentSoft,
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: 14,
              }}
            >
              <Text style={{ fontSize: 30, fontWeight: '900', color: theme.colors.accentDark }}>{entry.radical}</Text>
            </View>
            <Text style={{ fontSize: 16, fontWeight: '700', color: theme.colors.text, flex: 1 }}>{entry.radicalMeaningKo}</Text>
          </View>
        </Card>
      </Fade>

      <Fade delay={190}>
        <Card>
          <Text style={{ fontSize: 13, fontWeight: '700', color: theme.colors.subtext, marginBottom: 8 }}>{L.mnemonic}</Text>
          <Text style={{ fontSize: 16, lineHeight: 25, color: theme.colors.text }}>{entry.mnemonicKo}</Text>
        </Card>
      </Fade>

      <Fade delay={240}>
        <Card>
          <Text style={{ fontSize: 13, fontWeight: '700', color: theme.colors.subtext, marginBottom: 10 }}>{L.example}</Text>
          <FuriganaTokens tokens={entry.exampleWordTokens} size={30} color={color} />
          <Text style={{ fontSize: 15, color: theme.colors.subtext, marginTop: 10 }}>{entry.exampleWordKo}</Text>
          <View style={{ marginTop: 8 }}>
            <Button icon="speaker" title="발음 듣기" onPress={() => app.speak(entry.exampleWordJa)} secondary color={color} />
          </View>
        </Card>
      </Fade>

      <Fade delay={290}>
        <Button title={L.back} onPress={onBack} secondary color={color} />
        <Button title={L.home} onPress={() => app.navigate('home')} secondary />
      </Fade>
    </View>
  );
}

export function KanjiScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const color = personaColor(app.selectedPersonaId);
  const [filter, setFilter] = React.useState<Filter>('ALL');
  const [query, setQuery] = React.useState('');
  const [limit, setLimit] = React.useState(PAGE);
  const [selected, setSelected] = React.useState<KanjiEntry | null>(null);

  const openDetail = (entry: KanjiEntry) => {
    app.track('kanji_opened', { kanji: entry.kanji });
    setSelected(entry);
  };

  // Reset the render window whenever the result set changes so we never mount a
  // stale, oversized page.
  React.useEffect(() => setLimit(PAGE), [filter, query]);

  if (selected) {
    return <KanjiDetail entry={selected} color={color} app={app} onBack={() => setSelected(null)} />;
  }

  const q = query.trim().toLowerCase();
  const all = kanjiByLevel(filter);
  const list = q
    ? all.filter(
        (e) =>
          e.kanji.includes(q) ||
          e.meaningKo.toLowerCase().includes(q) ||
          e.onyomi.some((r) => r.toLowerCase().includes(q)) ||
          e.kunyomi.some((r) => r.toLowerCase().includes(q)),
      )
    : all;
  const shown = list.slice(0, limit);

  return (
    <View>
      <Fade>
        <Title>{L.title}</Title>
        <Muted>{L.subtitle}</Muted>
      </Fade>

      <Fade delay={50}>
        <Row>
          <LevelChip label={L.all} active={filter === 'ALL'} color={color} onPress={() => setFilter('ALL')} />
          <LevelChip label="N5" active={filter === 'N5'} color={color} onPress={() => setFilter('N5')} />
          <LevelChip label="N4" active={filter === 'N4'} color={color} onPress={() => setFilter('N4')} />
          <View style={{ marginTop: 8, marginLeft: 4, justifyContent: 'center' }}>
            <Text style={{ fontSize: 13, color: theme.colors.subtext, fontWeight: '600' }}>
              {list.length}
              {L.countSuffix}
            </Text>
          </View>
        </Row>
        <View
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            backgroundColor: theme.colors.chip,
            borderRadius: 12,
            paddingHorizontal: 12,
            marginTop: 12,
          }}
        >
          <Icon name="search" size={18} color={theme.colors.subtext} />
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder="한자·뜻·읽기 검색"
            placeholderTextColor={theme.colors.subtext}
            style={{ flex: 1, marginLeft: 8, paddingVertical: 10, fontSize: 15, color: theme.colors.text }}
          />
          {query ? (
            <Pressable onPress={() => setQuery('')} accessibilityRole="button" accessibilityLabel="검색어 지우기" hitSlop={8}>
              <Icon name="close" size={16} color={theme.colors.subtext} />
            </Pressable>
          ) : null}
        </View>
      </Fade>

      <View style={{ flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', marginTop: 14 }}>
        {shown.map((entry) => (
          <KanjiTile key={`${entry.level}-${entry.kanji}`} entry={entry} color={color} onPress={() => openDetail(entry)} />
        ))}
      </View>

      {list.length === 0 ? <Muted>검색 결과가 없어요</Muted> : null}

      {shown.length < list.length ? (
        <Button title={`더 보기 (${list.length - shown.length}자 남음)`} onPress={() => setLimit((n) => n + PAGE * 2)} secondary color={color} />
      ) : null}

      <Fade delay={160}>
        <Button title={L.home} onPress={() => app.navigate('home')} secondary />
      </Fade>
    </View>
  );
}
