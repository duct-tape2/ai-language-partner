import React from 'react';
import { Text, View, Pressable } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Card, Button, Title, Muted, Pill, Fade, FuriganaTokens } from '../components';
import { Icon } from '../icons';
import type { AppController } from '../store';
import {
  NUMBERS,
  HOURS,
  MINUTES,
  DAYS,
  WEEKDAYS,
  type NumbersTab,
  type ReadingEntry,
} from '../numbers/numbersData';

// Numbers / time / date reference + tap-to-speak. Four tabs (숫자 / 시간 / 날짜 /
// 요일). Each row shows the surface label, furigana reading, and Korean gloss;
// tapping speaks the kana reading through the persona voice (ja-JP). Irregular
// readings (4時 よじ, 7時 しちじ, 9時 くじ, 1日 ついたち, 20日 はつか ...) are
// visually flagged so learners know exactly what to memorize.

const T = {
  title: '숫자 · 시간 · 날짜',
  subtitle: '눌러서 발음을 들어보세요. 주황색 표시는 불규칙 읽기예요.',
  home: '홈으로',
  irregular: '불규칙',
  tapHint: '탭하면 일본어 발음이 재생됩니다',
  tabs: {
    numbers: '숫자',
    time: '시간',
    date: '날짜',
    weekday: '요일',
  },
  sections: {
    hours: '시 (〜時)',
    minutes: '분 (〜分)',
  },
};

const TAB_ORDER: NumbersTab[] = ['numbers', 'time', 'date', 'weekday'];

export function NumbersTimeScreen({ app }: { app: AppController }) {
  const color = personaColor(app.selectedPersonaId);
  const [tab, setTab] = React.useState<NumbersTab>('numbers');

  const selectTab = (t: NumbersTab) => {
    if (t === tab) return;
    setTab(t);
    app.track('numbers_tab', { tab: t });
  };

  return (
    <View>
      <Fade>
        <Title>{T.title}</Title>
        <Muted>{T.subtitle}</Muted>
      </Fade>

      <Fade delay={40}>
        <Tabs value={tab} onChange={selectTab} accent={color} />
      </Fade>

      {tab === 'numbers' && (
        <Fade delay={80}>
          <ReadingGrid entries={NUMBERS} accent={color} onSpeak={app.speak} />
        </Fade>
      )}

      {tab === 'time' && (
        <Fade delay={80}>
          <SectionLabel text={T.sections.hours} />
          <ReadingGrid entries={HOURS} accent={color} onSpeak={app.speak} />
          <SectionLabel text={T.sections.minutes} />
          <ReadingGrid entries={MINUTES} accent={color} onSpeak={app.speak} />
        </Fade>
      )}

      {tab === 'date' && (
        <Fade delay={80}>
          <ReadingGrid entries={DAYS} accent={color} onSpeak={app.speak} />
        </Fade>
      )}

      {tab === 'weekday' && (
        <Fade delay={80}>
          <ReadingGrid entries={WEEKDAYS} accent={color} onSpeak={app.speak} />
        </Fade>
      )}

      <Fade delay={120}>
        <Button title={T.home} onPress={() => app.navigate('home')} secondary />
      </Fade>
    </View>
  );
}

function Tabs({
  value,
  onChange,
  accent,
}: {
  value: NumbersTab;
  onChange: (t: NumbersTab) => void;
  accent: string;
}) {
  const { theme } = useTheme();
  return (
    <View style={{ flexDirection: 'row', backgroundColor: theme.colors.track, borderRadius: 999, padding: 4, marginBottom: 14 }}>
      {TAB_ORDER.map((t) => {
        const active = t === value;
        return (
          <Pressable
            key={t}
            onPress={() => onChange(t)}
            style={{ flex: 1 }}
            accessibilityRole="button"
            accessibilityLabel={T.tabs[t]}
            accessibilityState={{ selected: active }}
          >
            <View
              style={{
                paddingVertical: 9,
                alignItems: 'center',
                borderRadius: 999,
                backgroundColor: active ? theme.colors.card : 'transparent',
              }}
            >
              <Text style={{ fontWeight: active ? '800' : '600', color: active ? accent : theme.colors.subtext, fontSize: 14 }}>
                {T.tabs[t]}
              </Text>
            </View>
          </Pressable>
        );
      })}
    </View>
  );
}

function SectionLabel({ text }: { text: string }) {
  const { theme } = useTheme();
  return (
    <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.subtext, marginTop: 4, marginBottom: 8 }}>{text}</Text>
  );
}

function ReadingGrid({
  entries,
  accent,
  onSpeak,
}: {
  entries: ReadingEntry[];
  accent: string;
  onSpeak: (text?: string) => void;
}) {
  return (
    <Card style={{ paddingVertical: 8, paddingHorizontal: 10 }}>
      {entries.map((e, i) => (
        <ReadingRow key={e.label} entry={e} accent={accent} onSpeak={onSpeak} last={i === entries.length - 1} />
      ))}
    </Card>
  );
}

function ReadingRow({
  entry,
  accent,
  onSpeak,
  last,
}: {
  entry: ReadingEntry;
  accent: string;
  onSpeak: (text?: string) => void;
  last: boolean;
}) {
  const { theme } = useTheme();
  const tint = entry.irregular ? theme.colors.accent : theme.colors.text;
  return (
    <Pressable
      onPress={() => onSpeak(entry.readingJa)}
      accessibilityRole="button"
      accessibilityLabel={`${entry.label}, ${entry.readingJa}, ${entry.ko}. ${T.tapHint}`}
      style={{
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: 10,
        paddingHorizontal: 6,
        borderBottomWidth: last ? 0 : 1,
        borderBottomColor: theme.colors.border,
        backgroundColor: entry.irregular ? theme.colors.accentSoft : 'transparent',
        borderRadius: entry.irregular ? 10 : 0,
        marginBottom: entry.irregular ? 2 : 0,
      }}
    >
      <View style={{ flex: 1 }}>
        <FuriganaTokens tokens={entry.tokens} size={24} color={tint} />
        <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 4 }}>{entry.ko}</Text>
      </View>

      <View style={{ alignItems: 'flex-end', marginLeft: 8 }}>
        {entry.irregular ? <Pill label={T.irregular} color={theme.colors.accentDark} /> : null}
        <View
          style={{
            marginTop: entry.irregular ? 6 : 0,
            width: 40,
            height: 40,
            borderRadius: 20,
            borderWidth: 1.5,
            borderColor: accent,
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: theme.colors.card,
          }}
        >
          <Icon name="play" size={16} color={accent} />
        </View>
      </View>
    </Pressable>
  );
}
