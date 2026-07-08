import React from 'react';
import { Text, View, Pressable, TextInput } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Card, Button, Title, Muted, Pill, Fade, Row, FuriganaTokens } from '../components';
import { GRAMMAR, grammarByLevel } from '../grammar/grammarData';
import { GrammarDepthNote } from '../grammar/GrammarDepthNote';
import type { GrammarPoint, GrammarLevel } from '../grammar/grammarData';
import type { AppController } from '../store';

// 문법 설명 (Grammar): 우리 앱은 고정 예문만 있었는데, 여기서 N5/N4 핵심 문형을
// 레벨 필터 + 검색 + 상세(의미/접속/예문/주의)로 설명한다. 네트워크 없이 정적 데이터.
type LevelFilter = 'ALL' | GrammarLevel;

// Render a page at a time so the 180-point ALL list paints instantly instead of
// mounting 180 animated cards up front.
const PAGE = 60;

const UI = {
  title: '문법 설명',
  subtitle: 'N5 / N4 핵심 문형을 뜻과 접속, 예문으로 정리했어요.',
  searchPlaceholder: '문형이나 뜻으로 검색 (예: たら, 이유, 가능)',
  all: '전체',
  empty: '검색 결과가 없어요. 다른 말로 찾아보세요.',
  count: (n: number) => `${n}개 문형`,
  meaning: '의미',
  connection: '접속',
  example: '예문',
  note: '주의',
  back: '목록으로',
  home: '홈으로',
  detailHint: '탭하면 자세한 설명이 열려요.',
};

function levelColor(level: GrammarLevel, theme: ReturnType<typeof useTheme>['theme']): string {
  return level === 'N5' ? theme.colors.good : level === 'N3' ? theme.colors.near : theme.colors.accent;
}

export function GrammarScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const accent = personaColor(app.selectedPersonaId);
  const [level, setLevel] = React.useState<LevelFilter>('ALL');
  const [query, setQuery] = React.useState('');
  const [limit, setLimit] = React.useState(PAGE);
  const [openId, setOpenId] = React.useState<string | null>(null);

  const base = level === 'ALL' ? GRAMMAR : grammarByLevel(level);
  const q = query.trim().toLowerCase();
  const list = q
    ? base.filter(
        (g) =>
          g.pattern.toLowerCase().includes(q) ||
          g.meaningKo.toLowerCase().includes(q) ||
          g.connectionKo.toLowerCase().includes(q) ||
          (g.noteKo ?? '').toLowerCase().includes(q),
      )
    : base;

  React.useEffect(() => setLimit(PAGE), [level, query]);
  const shown = list.slice(0, limit);

  const open = list.find((g) => g.id === openId) ?? null;

  const filters: { value: LevelFilter; label: string }[] = [
    { value: 'ALL', label: UI.all },
    { value: 'N5', label: 'N5' },
    { value: 'N4', label: 'N4' },
    { value: 'N3', label: 'N3' },
  ];

  const selectLevel = (v: LevelFilter) => {
    setLevel(v);
    setOpenId(null);
  };

  const openGrammar = (g: GrammarPoint) => {
    setOpenId(g.id);
    app.track('grammar_opened', { id: g.id });
  };

  // ----- detail view -----
  if (open) {
    const lc = levelColor(open.level, theme);
    return (
      <View>
        <Fade>
          <Row>
            <Title>{open.pattern}</Title>
          </Row>
          <Row>
            <Pill label={open.level} color={lc} />
          </Row>
        </Fade>

        <Fade delay={60}>
          <Card>
            <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.subtext, letterSpacing: 1, marginBottom: 4 }}>{UI.meaning}</Text>
            <Text style={{ fontSize: 18, fontWeight: '800', color: theme.colors.text, lineHeight: 26 }}>{open.meaningKo}</Text>
          </Card>
        </Fade>

        <Fade delay={100}>
          <Card>
            <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.subtext, letterSpacing: 1, marginBottom: 4 }}>{UI.connection}</Text>
            <Text style={{ fontSize: 16, fontWeight: '700', color: theme.colors.accentDark, lineHeight: 24 }}>{open.connectionKo}</Text>
          </Card>
        </Fade>

        <Fade delay={140}>
          <Card>
            <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.subtext, letterSpacing: 1, marginBottom: 8 }}>{UI.example}</Text>
            <FuriganaTokens tokens={open.exampleTokens} size={24} color={accent} />
            <Text style={{ fontSize: 15, color: theme.colors.text, marginTop: 10, lineHeight: 22 }}>{open.exampleKo}</Text>
            <View style={{ marginTop: 10 }}>
              <Button title="음성으로 듣기" onPress={() => app.speak(open.exampleJa)} secondary color={accent} />
            </View>
          </Card>
        </Fade>

        {open.noteKo ? (
          <Fade delay={180}>
            <Card style={{ borderColor: theme.colors.near, borderLeftWidth: 4 }}>
              <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.near, letterSpacing: 1, marginBottom: 4 }}>{UI.note}</Text>
              <Text style={{ fontSize: 14, color: theme.colors.text, lineHeight: 22 }}>{open.noteKo}</Text>
            </Card>
          </Fade>
        ) : null}

        <Fade delay={200}>
          <GrammarDepthNote koPitfall={open.koPitfall} similar={open.similarKo} extraExamples={open.extraExamples} />
        </Fade>

        <Fade delay={220}>
          <Button title={UI.back} onPress={() => setOpenId(null)} secondary color={accent} />
          <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
        </Fade>
      </View>
    );
  }

  // ----- list view -----
  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>{UI.title}</Title>
          <Pill label={UI.count(list.length)} color={accent} />
        </View>
        <Muted>{UI.subtitle}</Muted>
      </Fade>

      <Fade delay={60}>
        <View style={{ flexDirection: 'row', backgroundColor: theme.colors.track, borderRadius: 999, padding: 4, marginTop: 12, marginBottom: 8 }}>
          {filters.map((f) => {
            const active = f.value === level;
            return (
              <Pressable
                key={f.value}
                onPress={() => selectLevel(f.value)}
                style={{ flex: 1 }}
                accessibilityRole="button"
                accessibilityLabel={`${f.label} 문법`}
                accessibilityState={{ selected: active }}
              >
                <View style={{ paddingVertical: 8, alignItems: 'center', borderRadius: 999, backgroundColor: active ? theme.colors.card : 'transparent' }}>
                  <Text style={{ fontWeight: active ? '800' : '500', color: active ? theme.colors.accentDark : theme.colors.subtext, fontSize: 14 }}>{f.label}</Text>
                </View>
              </Pressable>
            );
          })}
        </View>
      </Fade>

      <Fade delay={100}>
        <View
          style={{
            backgroundColor: theme.colors.card,
            borderRadius: theme.radius.md,
            borderWidth: 1,
            borderColor: theme.colors.border,
            paddingHorizontal: 12,
            paddingVertical: 4,
            marginBottom: 12,
          }}
        >
          <TextInputRow value={query} onChange={setQuery} placeholder={UI.searchPlaceholder} />
        </View>
      </Fade>

      {list.length === 0 ? (
        <Card>
          <Muted>{UI.empty}</Muted>
        </Card>
      ) : (
        shown.map((g) => {
          const lc = levelColor(g.level, theme);
          return (
            <Pressable
              key={g.id}
              onPress={() => openGrammar(g)}
              accessibilityRole="button"
              accessibilityLabel={`${g.pattern}, ${g.meaningKo}`}
            >
              <View
                style={{
                  backgroundColor: theme.colors.card,
                  borderRadius: theme.radius.lg,
                  borderWidth: 1,
                  borderColor: theme.colors.border,
                  borderLeftWidth: 4,
                  borderLeftColor: lc,
                  padding: 16,
                  marginBottom: 10,
                }}
              >
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text style={{ fontSize: 20, fontWeight: '900', color: theme.colors.text, flexShrink: 1, paddingRight: 8 }}>{g.pattern}</Text>
                  <View style={{ backgroundColor: theme.colors.chip, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4 }}>
                    <Text style={{ color: lc, fontSize: 12, fontWeight: '800' }}>{g.level}</Text>
                  </View>
                </View>
                <Text style={{ fontSize: 14, color: theme.colors.subtext, marginTop: 6, lineHeight: 20 }}>{g.meaningKo}</Text>
              </View>
            </Pressable>
          );
        })
      )}

      {shown.length < list.length ? (
        <Button title={`더 보기 (${list.length - shown.length}개 남음)`} onPress={() => setLimit((n) => n + PAGE * 2)} secondary color={accent} />
      ) : null}

      <Fade delay={200}>
        <Text style={{ fontSize: 12, color: theme.colors.subtext, textAlign: 'center', marginTop: 4, marginBottom: 8 }}>{UI.detailHint}</Text>
        <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
      </Fade>
    </View>
  );
}

// Small controlled text input styled to match cards. Kept local so we don't touch
// shared components. TextInput comes from react-native.
function TextInputRow({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder: string }) {
  const { theme } = useTheme();
  const { TextInput } = require('react-native') as typeof import('react-native');
  return (
    <TextInput
      value={value}
      onChangeText={onChange}
      placeholder={placeholder}
      placeholderTextColor={theme.colors.subtext}
      accessibilityLabel="문법 검색"
      style={{ fontSize: 15, color: theme.colors.text, paddingVertical: 10 }}
    />
  );
}
