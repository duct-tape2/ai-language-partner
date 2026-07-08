import React from 'react';
import { Text, View, Pressable } from 'react-native';
import * as Speech from 'expo-speech';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Card, Button, Title, Muted, Pill, Fade, Row, FuriganaTokens } from '../components';
import { Icon } from '../icons';
import { COUNTERS, COUNTER_TOTAL } from '../counters/counterData';
import type { Counter } from '../counters/counterData';
import type { AppController } from '../store';

// 조수사 (Japanese counters): JLPT 최대 난관. 목록에서 조수사를 고르면 용법 +
// 1~10 읽기(불규칙 후리가나)가 열리고, 숫자를 탭하면 expo-speech(ja-JP)로 발음.
// 네트워크 없이 정적 데이터.
const UI = {
  title: '조수사',
  subtitle: '물건을 셀 때 붙이는 일본어 조수사예요. 1~10 불규칙 읽기를 확인하고 탭해서 들어보세요.',
  count: (n: number) => `${n}개 조수사`,
  use: '이럴 때 써요',
  example: '예문',
  hard: '주의할 읽기',
  tapHint: '탭하면 1~10 읽기가 열려요.',
  tapNumberHint: '숫자를 탭하면 발음을 들려줘요.',
  back: '목록으로',
  home: '홈으로',
};

export function CountersScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const accent = personaColor(app.selectedPersonaId);
  const [openId, setOpenId] = React.useState<string | null>(null);
  const [spokenN, setSpokenN] = React.useState<number | null>(null);

  const open = COUNTERS.find((c) => c.id === openId) ?? null;

  const openCounter = (c: Counter) => {
    setOpenId(c.id);
    setSpokenN(null);
    app.track('counter_opened', { counter: c.counter });
  };

  const back = () => {
    setOpenId(null);
    setSpokenN(null);
    Speech.stop();
  };

  const speak = (reading: string, n: number) => {
    Speech.stop();
    setSpokenN(n);
    Speech.speak(reading, { language: 'ja-JP', rate: 0.9 });
  };

  // ----- detail view -----
  if (open) {
    return (
      <View>
        <Fade>
          <Row>
            <Title>{open.counter}</Title>
            <View style={{ width: 8 }} />
            <Pill label={open.reading} color={accent} />
          </Row>
          <Muted>{UI.tapNumberHint}</Muted>
        </Fade>

        <Fade delay={60}>
          <Card>
            <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.subtext, letterSpacing: 1, marginBottom: 4 }}>{UI.use}</Text>
            <Text style={{ fontSize: 17, fontWeight: '800', color: theme.colors.text, lineHeight: 25 }}>{open.useKo}</Text>
            <View style={{ height: 1, backgroundColor: theme.colors.border, marginVertical: 12 }} />
            <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.subtext, letterSpacing: 1, marginBottom: 4 }}>{UI.example}</Text>
            <Text style={{ fontSize: 15, color: theme.colors.text, lineHeight: 23 }}>{open.exampleKo}</Text>
            {open.hardKo ? (
              <>
                <View style={{ height: 1, backgroundColor: theme.colors.border, marginVertical: 12 }} />
                <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.bad, letterSpacing: 1, marginBottom: 4 }}>{UI.hard}</Text>
                <Text style={{ fontSize: 14, color: theme.colors.text, lineHeight: 22 }}>{open.hardKo}</Text>
              </>
            ) : null}
          </Card>
        </Fade>

        <Fade delay={120}>
          {open.forms.map((f) => {
            const active = spokenN === f.n;
            return (
              <Pressable
                key={f.n}
                onPress={() => speak(f.readingJa, f.n)}
                accessibilityRole="button"
                accessibilityLabel={`${f.n}, ${f.readingJa}, 발음 듣기`}
              >
                <View
                  style={{
                    flexDirection: 'row',
                    alignItems: 'center',
                    backgroundColor: theme.colors.card,
                    borderRadius: theme.radius.md,
                    borderWidth: active ? 2 : 1,
                    borderColor: active ? accent : theme.colors.border,
                    paddingVertical: 12,
                    paddingHorizontal: 16,
                    marginBottom: 8,
                  }}
                >
                  <Text style={{ width: 34, fontSize: 20, fontWeight: '900', color: theme.colors.subtext }}>{f.n}</Text>
                  <View style={{ flex: 1 }}>
                    <FuriganaTokens tokens={f.tokens} size={24} color={accent} />
                  </View>
                  <Text style={{ fontSize: 13, color: theme.colors.subtext, marginRight: 8 }}>{f.readingJa}</Text>
                  <Icon name="speaker" size={20} color={theme.colors.subtext} />
                </View>
              </Pressable>
            );
          })}
        </Fade>

        <Fade delay={160}>
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
          <Pill label={UI.count(COUNTER_TOTAL)} color={accent} />
        </View>
        <Muted>{UI.subtitle}</Muted>
      </Fade>

      <Fade delay={60}>
        <View style={{ marginTop: 12 }}>
          {COUNTERS.map((c) => (
            <Pressable
              key={c.id}
              onPress={() => openCounter(c)}
              accessibilityRole="button"
              accessibilityLabel={`${c.counter}, ${c.useKo}`}
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
                  <Text style={{ fontSize: 24, fontWeight: '900', color: accent }}>{c.counter}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text }}>{c.reading}</Text>
                  <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 2, lineHeight: 19 }}>{c.useKo}</Text>
                </View>
                <Text style={{ fontSize: 20, color: theme.colors.subtext, marginLeft: 8 }}>›</Text>
              </View>
            </Pressable>
          ))}
        </View>
      </Fade>

      <Fade delay={120}>
        <Muted>{UI.tapHint}</Muted>
        <View style={{ height: 8 }} />
        <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
      </Fade>
    </View>
  );
}
