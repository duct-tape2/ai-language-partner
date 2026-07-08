import React from 'react';
import { Text, View, Pressable } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Card, Button, Title, Muted, Pill, Fade, Row, FuriganaTokens } from '../components';
import {
  KEIGO,
  KEIGO_TOTAL,
  KEIGO_TYPES,
  KEIGO_COLS,
  type KeigoEntry,
  type KeigoColKey,
  type KeigoForm,
} from '../keigo/keigoData';
import type { AppController } from '../store';

// 존댓말/경어 (敬語) 가이드. N4 -> N3 최대 난관: 같은 동사가 정중어/존경어/겸양어
// 세 갈래로 갈라지고, 존경어 겸양어는 아예 다른 단어가 되는 경우가 많음.
// 정적 데이터만, 네트워크 없음. 각 형을 탭하면 페르소나 음성으로 읽어줌.

const UI = {
  title: '존댓말 경어',
  subtitle: '정중어 존경어 겸양어, 세 가지 경어를 한눈에.',
  countLabel: (n: number) => `동사 ${n}개`,
  introHint: '탭하면 음성으로 들려줘요. 각 단어를 눌러 4가지 형태를 펼쳐 보세요.',
  meaning: '뜻',
  usage: '사용 포인트',
  tapToHear: '탭해서 듣기',
  home: '홈으로',
  ruleTip: '규칙형 정리',
  ruleTipBody: '전용 경어가 없는 동사는 규칙형으로: 존경어 「お + ます어간 + になる」, 겸양어 「お + ます어간 + する」.',
};

// One politeness cell: label on top, tappable furigana below, speaks on press.
function FormCell({
  colKey,
  label,
  form,
  color,
  onSpeak,
}: {
  colKey: KeigoColKey;
  label: string;
  form: KeigoForm;
  color: string;
  onSpeak: (f: KeigoForm, colKey: KeigoColKey) => void;
}) {
  const { theme } = useTheme();
  // 존경어/겸양어만 페르소나 색으로 강조, 사전형/정중어는 기본 텍스트색.
  const emphasize = colKey === 'sonkeigo' || colKey === 'kenjougo';
  const tokenColor = emphasize ? color : theme.colors.text;
  return (
    <Pressable
      onPress={() => onSpeak(form, colKey)}
      accessibilityRole="button"
      accessibilityLabel={`${label} ${form.ja}`}
    >
      <View
        style={{
          flexDirection: 'row',
          alignItems: 'center',
          paddingVertical: 10,
          borderBottomWidth: 1,
          borderBottomColor: theme.colors.border,
        }}
      >
        <View style={{ width: 96 }}>
          <Text style={{ fontSize: 11, fontWeight: '800', color: theme.colors.subtext, letterSpacing: 0.5 }}>{label}</Text>
        </View>
        <View style={{ flex: 1 }}>
          <FuriganaTokens tokens={form.tokens} size={22} color={tokenColor} />
        </View>
        <Text style={{ fontSize: 16, color: theme.colors.subtext, marginLeft: 6 }}>{'♪'}</Text>
      </View>
    </Pressable>
  );
}

export function KeigoScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const accent = personaColor(app.selectedPersonaId);
  const [openId, setOpenId] = React.useState<string | null>(KEIGO[0]?.id ?? null);

  React.useEffect(() => {
    app.track('keigo_opened');
  }, [app]);

  const speakForm = (form: KeigoForm, _colKey: KeigoColKey) => {
    app.speak(form.ja);
  };

  const toggle = (entry: KeigoEntry) => {
    const next = openId === entry.id ? null : entry.id;
    setOpenId(next);
    if (next) app.track('keigo_verb_opened', { id: entry.id });
  };

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>{UI.title}</Title>
          <Pill label={UI.countLabel(KEIGO_TOTAL)} color={accent} />
        </View>
        <Muted>{UI.subtitle}</Muted>
      </Fade>

      {/* 세 가지 경어 종류 설명 */}
      <Fade delay={40}>
        <Card style={{ borderLeftWidth: 4, borderLeftColor: accent }}>
          {KEIGO_TYPES.map((t, i) => (
            <View
              key={t.key}
              style={{
                marginBottom: i === KEIGO_TYPES.length - 1 ? 0 : 14,
                paddingBottom: i === KEIGO_TYPES.length - 1 ? 0 : 14,
                borderBottomWidth: i === KEIGO_TYPES.length - 1 ? 0 : 1,
                borderBottomColor: theme.colors.border,
              }}
            >
              <Text style={{ fontSize: 16, fontWeight: '900', color: theme.colors.text, marginBottom: 4 }}>{t.title}</Text>
              <Text style={{ fontSize: 13, color: theme.colors.subtext, lineHeight: 20 }}>{t.descKo}</Text>
              <View style={{ marginTop: 8, alignSelf: 'flex-start', backgroundColor: theme.colors.chip, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6 }}>
                <Text style={{ fontSize: 13, fontWeight: '700', color: theme.colors.chipText }}>{t.exampleKo}</Text>
              </View>
            </View>
          ))}
        </Card>
      </Fade>

      <Fade delay={80}>
        <Text style={{ fontSize: 13, color: theme.colors.subtext, marginBottom: 6, marginTop: 2 }}>{UI.introHint}</Text>
      </Fade>

      {/* 동사별 4형 리스트 (펼침) */}
      {KEIGO.map((entry, i) => {
        const open = openId === entry.id;
        return (
          <Fade key={entry.id} delay={Math.min(100 + i * 30, 320)}>
            <Pressable
              onPress={() => toggle(entry)}
              accessibilityRole="button"
              accessibilityLabel={`${entry.plain.ja} ${entry.meaningKo}`}
              accessibilityState={{ expanded: open }}
            >
              <View
                style={{
                  backgroundColor: theme.colors.card,
                  borderRadius: theme.radius.lg,
                  borderWidth: 1,
                  borderColor: theme.colors.border,
                  padding: 16,
                  marginBottom: 10,
                }}
              >
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', flexShrink: 1 }}>
                    <FuriganaTokens tokens={entry.tokens} size={24} color={theme.colors.text} />
                    <View style={{ marginLeft: 12, flexShrink: 1 }}>
                      <Text style={{ fontSize: 15, fontWeight: '700', color: theme.colors.subtext }}>{entry.meaningKo}</Text>
                    </View>
                  </View>
                  <Text style={{ fontSize: 20, color: theme.colors.subtext, marginLeft: 8 }}>{open ? '−' : '+'}</Text>
                </View>

                {open ? (
                  <Fade>
                    <View style={{ marginTop: 14 }}>
                      {KEIGO_COLS.map((col) => (
                        <FormCell
                          key={col.key}
                          colKey={col.key}
                          label={col.label}
                          form={entry[col.key]}
                          color={accent}
                          onSpeak={speakForm}
                        />
                      ))}

                      {/* 사용 포인트 */}
                      <View style={{ marginTop: 14, backgroundColor: theme.colors.chip, borderRadius: theme.radius.md, padding: 12 }}>
                        <Text style={{ fontSize: 11, fontWeight: '800', color: theme.colors.subtext, letterSpacing: 0.5, marginBottom: 4 }}>{UI.usage}</Text>
                        <Text style={{ fontSize: 13, color: theme.colors.text, lineHeight: 20 }}>{entry.usageKo}</Text>
                      </View>
                    </View>
                  </Fade>
                ) : (
                  <View style={{ marginTop: 8 }}>
                    <Row>
                      {KEIGO_COLS.filter((c) => c.key === 'sonkeigo' || c.key === 'kenjougo').map((c) => (
                        <Pill key={c.key} label={`${c.label}: ${entry[c.key].ja}`} color={accent} />
                      ))}
                    </Row>
                  </View>
                )}
              </View>
            </Pressable>
          </Fade>
        );
      })}

      {/* 규칙형 팁 */}
      <Fade delay={340}>
        <Card style={{ borderLeftWidth: 4, borderLeftColor: theme.colors.near }}>
          <Text style={{ fontSize: 14, fontWeight: '900', color: theme.colors.text, marginBottom: 6 }}>{UI.ruleTip}</Text>
          <Text style={{ fontSize: 13, color: theme.colors.subtext, lineHeight: 20 }}>{UI.ruleTipBody}</Text>
        </Card>
      </Fade>

      <Fade delay={360}>
        <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
      </Fade>
    </View>
  );
}
