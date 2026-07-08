import React from 'react';
import { Text, View, Pressable, TextInput } from 'react-native';
import { useTheme } from '../ThemeContext';
import { Button, Card, Fade, FuriganaTokens, Muted, Pill, Title } from '../components';
import { Icon } from '../icons';
import type { AppController } from '../store';
import { SITUATIONS, type Situation, type SituationPhrase } from '../situations/situationData';

const UI = {
  title: '상황별 표현집',
  sub: '여행/생활 장면별로 바로 쓰는 정중한 표현을 모았어요.',
  home: '홈으로',
  back: '목록으로',
  search: '표현 검색 (한국어/일본어)',
  count: (n: number) => n + '개 표현',
  noHit: '검색 결과가 없어요.',
  tapHint: '문장을 누르면 소리로 들려줘요.',
};

function matchPhrase(p: SituationPhrase, q: string): boolean {
  const hay = (p.ja + ' ' + p.ko + ' ' + (p.note || '')).toLowerCase();
  return hay.indexOf(q) >= 0;
}

export function SituationsScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const c = theme.colors;
  const [openId, setOpenId] = React.useState<string | null>(null);
  const [query, setQuery] = React.useState('');

  const current = React.useMemo<Situation | null>(
    () => (openId ? SITUATIONS.find((s) => s.id === openId) || null : null),
    [openId],
  );

  const open = (s: Situation) => {
    setOpenId(s.id);
    setQuery('');
    app.track('situation_opened', { id: s.id });
  };

  const filtered = React.useMemo<SituationPhrase[]>(() => {
    if (!current) return [];
    const q = query.trim().toLowerCase();
    if (!q) return current.phrases;
    return current.phrases.filter((p) => matchPhrase(p, q));
  }, [current, query]);

  // ----- list view -----
  if (!current) {
    return (
      <View>
        <Fade>
          <Title>{UI.title}</Title>
          <Muted>{UI.sub}</Muted>
        </Fade>
        <View style={{ height: 12 }} />
        {SITUATIONS.map((s, i) => (
          <Fade key={s.id} delay={i * 30}>
            <Pressable accessibilityRole="button" onPress={() => open(s)}>
              <Card>
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                  <Text style={{ fontSize: 30, marginRight: 14 }}>{s.icon}</Text>
                  <View style={{ flex: 1 }}>
                    <Text style={{ color: c.text, fontSize: 18, fontWeight: '700' }}>{s.titleKo}</Text>
                    <View style={{ height: 4 }} />
                    <Pill label={UI.count(s.phrases.length)} />
                  </View>
                  <Text style={{ color: c.subtext, fontSize: 22, fontWeight: '700' }}>{'>'}</Text>
                </View>
              </Card>
            </Pressable>
          </Fade>
        ))}
        <View style={{ height: 8 }} />
        <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
      </View>
    );
  }

  // ----- detail view -----
  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
          <Text style={{ fontSize: 28, marginRight: 12 }}>{current.icon}</Text>
          <Title>{current.titleKo}</Title>
        </View>
        <Muted>{UI.tapHint}</Muted>
      </Fade>

      <View style={{ height: 12 }} />
      <TextInput
        value={query}
        onChangeText={setQuery}
        placeholder={UI.search}
        placeholderTextColor={c.subtext}
        style={{
          backgroundColor: c.card,
          borderColor: c.border,
          borderWidth: 1,
          borderRadius: theme.radius.md,
          paddingVertical: 12,
          paddingHorizontal: 16,
          color: c.text,
          fontSize: 16,
          marginBottom: 14,
        }}
      />

      {filtered.length === 0 ? (
        <Card>
          <Muted>{UI.noHit}</Muted>
        </Card>
      ) : (
        filtered.map((p, i) => (
          <Fade key={current.id + '_' + i} delay={i * 25}>
            <Pressable accessibilityRole="button" onPress={() => app.speak(p.ja)}>
              <Card>
                <View style={{ flexDirection: 'row', alignItems: 'flex-start' }}>
                  <View style={{ flex: 1 }}>
                    <FuriganaTokens tokens={p.tokens} size={24} />
                    <View style={{ height: 6 }} />
                    <Text style={{ color: c.subtext, fontSize: 15 }}>{p.ko}</Text>
                    {p.note ? (
                      <View
                        style={{
                          marginTop: 10,
                          backgroundColor: c.accentSoft,
                          borderRadius: theme.radius.sm,
                          paddingVertical: 8,
                          paddingHorizontal: 12,
                        }}
                      >
                        <Text style={{ color: c.accentDark, fontSize: 13, lineHeight: 19 }}>{p.note}</Text>
                      </View>
                    ) : null}
                  </View>
                  <View style={{ marginLeft: 10 }}>
                    <Icon name="speaker" size={22} color={c.subtext} />
                  </View>
                </View>
              </Card>
            </Pressable>
          </Fade>
        ))
      )}

      <View style={{ height: 8 }} />
      <Button title={UI.back} onPress={() => setOpenId(null)} secondary />
      <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
    </View>
  );
}
