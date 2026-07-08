import React from 'react';
import { Text, View, Pressable, TextInput } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Card, Button, Title, Muted, Pill, Fade, Row, FuriganaTokens } from '../components';
import { Icon } from '../icons';
import { IDIOMS, IDIOM_TOTAL } from '../idioms/idiomData';
import type { Idiom } from '../idioms/idiomData';
import type { AppController } from '../store';

// 관용구(慣用句)와 사자성어(四字熟語)를 검색하고, 탭하면 상세(직역 vs 실제 뜻,
// 한국어 대응 표현, 예문, 발음 듣기)가 열린다. app.speak(ja-JP)로 발음. 정적 데이터.
const UI = {
  title: '관용구 · 사자성어',
  subtitle: '일본어 관용구와 사자성어예요. 직역과 실제 뜻이 얼마나 다른지 보고, 탭해서 발음까지 들어보세요.',
  count: (n: number) => `${n}개`,
  search: '검색 (일본어 · 뜻 · 한국어 표현)',
  searchLabel: '관용구 검색',
  literal: '직역',
  meaning: '실제 뜻',
  equivalent: '한국어 대응 표현',
  example: '예문',
  listen: '발음 듣기',
  kanyoku: '관용구',
  yoji: '사자성어',
  none: '검색 결과가 없어요. 다른 단어로 찾아보세요.',
  back: '목록으로',
  home: '홈으로',
};

function norm(s: string) {
  return s.toLowerCase().replace(/\s+/g, '');
}

export function IdiomsScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const accent = personaColor(app.selectedPersonaId);
  const [openId, setOpenId] = React.useState<string | null>(null);
  const [query, setQuery] = React.useState('');

  const open = IDIOMS.find((i) => i.id === openId) ?? null;

  const openIdiom = (i: Idiom) => {
    setOpenId(i.id);
    app.track('idiom_opened', { id: i.id });
  };

  const back = () => setOpenId(null);

  const filtered = React.useMemo(() => {
    const q = norm(query);
    if (!q) return IDIOMS;
    return IDIOMS.filter((i) => {
      const hay = norm(i.ja + i.reading + i.meaningKo + i.literalKo + (i.koEquivalent ?? ''));
      return hay.includes(q);
    });
  }, [query]);

  const kindLabel = (k: Idiom['kind']) => (k === 'yoji' ? UI.yoji : UI.kanyoku);

  // ----- detail view -----
  if (open) {
    return (
      <View>
        <Fade>
          <Row>
            <Pill label={kindLabel(open.kind)} color={accent} />
          </Row>
          <View style={{ marginTop: 10 }}>
            <FuriganaTokens tokens={open.tokens} size={30} color={accent} />
          </View>
          <Text style={{ fontSize: 14, color: theme.colors.subtext, marginTop: 8 }}>{open.reading}</Text>
        </Fade>

        <Fade delay={60}>
          <View style={{ height: 12 }} />
          <Pressable
            onPress={() => app.speak(open.ja)}
            accessibilityRole="button"
            accessibilityLabel={`${open.reading}, ${UI.listen}`}
          >
            <View
              style={{
                flexDirection: 'row',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: theme.colors.accentSoft,
                borderRadius: theme.radius.md,
                borderWidth: 1,
                borderColor: accent,
                paddingVertical: 12,
                marginBottom: 4,
              }}
            >
              <Icon name="speaker" size={20} color={accent} />
              <View style={{ width: 8 }} />
              <Text style={{ fontSize: 15, fontWeight: '800', color: accent }}>{UI.listen}</Text>
            </View>
          </Pressable>
        </Fade>

        <Fade delay={120}>
          <Card>
            <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.subtext, letterSpacing: 1, marginBottom: 4 }}>{UI.literal}</Text>
            <Text style={{ fontSize: 16, color: theme.colors.subtext, lineHeight: 24, fontStyle: 'italic' }}>{open.literalKo}</Text>
            <View style={{ height: 1, backgroundColor: theme.colors.border, marginVertical: 12 }} />
            <Text style={{ fontSize: 12, fontWeight: '800', color: accent, letterSpacing: 1, marginBottom: 4 }}>{UI.meaning}</Text>
            <Text style={{ fontSize: 17, fontWeight: '800', color: theme.colors.text, lineHeight: 26 }}>{open.meaningKo}</Text>
            {open.koEquivalent ? (
              <>
                <View style={{ height: 1, backgroundColor: theme.colors.border, marginVertical: 12 }} />
                <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.subtext, letterSpacing: 1, marginBottom: 4 }}>{UI.equivalent}</Text>
                <Text style={{ fontSize: 16, fontWeight: '700', color: theme.colors.good, lineHeight: 24 }}>{open.koEquivalent}</Text>
              </>
            ) : null}
          </Card>
        </Fade>

        {open.exampleJa ? (
          <Fade delay={160}>
            <Card>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.subtext, letterSpacing: 1 }}>{UI.example}</Text>
                <Pressable
                  onPress={() => app.speak(open.exampleJa as string)}
                  accessibilityRole="button"
                  accessibilityLabel={`${UI.example}, ${UI.listen}`}
                >
                  <Icon name="speaker" size={18} color={theme.colors.subtext} />
                </Pressable>
              </View>
              <Text style={{ fontSize: 17, fontWeight: '700', color: theme.colors.text, lineHeight: 26 }}>{open.exampleJa}</Text>
              {open.exampleKo ? (
                <Text style={{ fontSize: 14, color: theme.colors.subtext, marginTop: 6, lineHeight: 21 }}>{open.exampleKo}</Text>
              ) : null}
            </Card>
          </Fade>
        ) : null}

        <Fade delay={200}>
          <Button title={UI.back} onPress={back} secondary color={accent} />
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
          <Pill label={UI.count(IDIOM_TOTAL)} color={accent} />
        </View>
        <Muted>{UI.subtitle}</Muted>
      </Fade>

      <Fade delay={60}>
        <View
          style={{
            backgroundColor: theme.colors.card,
            borderRadius: theme.radius.md,
            borderWidth: 1,
            borderColor: theme.colors.border,
            paddingHorizontal: 14,
            marginTop: 12,
            marginBottom: 4,
            flexDirection: 'row',
            alignItems: 'center',
          }}
        >
          <View style={{ marginRight: 8 }}>
            <Icon name="search" size={16} color={theme.colors.subtext} />
          </View>
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder={UI.search}
            placeholderTextColor={theme.colors.subtext}
            accessibilityLabel={UI.searchLabel}
            autoCapitalize="none"
            style={{ flex: 1, fontSize: 15, color: theme.colors.text, paddingVertical: 12 }}
          />
          {query ? (
            <Pressable onPress={() => setQuery('')} accessibilityRole="button" accessibilityLabel="검색어 지우기">
              <Text style={{ fontSize: 16, color: theme.colors.subtext, paddingHorizontal: 4 }}>✕</Text>
            </Pressable>
          ) : null}
        </View>
      </Fade>

      <Fade delay={120}>
        <View style={{ marginTop: 8 }}>
          {filtered.length === 0 ? (
            <Card>
              <Muted>{UI.none}</Muted>
            </Card>
          ) : (
            filtered.map((i) => (
              <Pressable
                key={i.id}
                onPress={() => openIdiom(i)}
                accessibilityRole="button"
                accessibilityLabel={`${i.ja}, ${i.meaningKo}`}
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
                  <View style={{ flex: 1 }}>
                    <Text style={{ fontSize: 18, fontWeight: '800', color: theme.colors.text }}>{i.ja}</Text>
                    <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 3, lineHeight: 19 }} numberOfLines={2}>
                      {i.meaningKo}
                    </Text>
                    <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 6 }}>
                      <View style={{ backgroundColor: theme.colors.accentSoft, borderRadius: 999, paddingHorizontal: 8, paddingVertical: 2 }}>
                        <Text style={{ fontSize: 11, fontWeight: '700', color: accent }}>
                          {i.kind === 'yoji' ? UI.yoji : UI.kanyoku}
                        </Text>
                      </View>
                      {i.koEquivalent ? (
                        <Text style={{ fontSize: 12, color: theme.colors.good, marginLeft: 8 }} numberOfLines={1}>
                          {i.koEquivalent}
                        </Text>
                      ) : null}
                    </View>
                  </View>
                  <Text style={{ fontSize: 20, color: theme.colors.subtext, marginLeft: 8 }}>›</Text>
                </View>
              </Pressable>
            ))
          )}
        </View>
      </Fade>

      <Fade delay={160}>
        <View style={{ height: 8 }} />
        <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
      </Fade>
    </View>
  );
}
