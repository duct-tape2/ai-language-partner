import React from 'react';
import { Text, View, Pressable } from 'react-native';
import * as Speech from 'expo-speech';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Button, Card, Fade, Muted, Pill, Title } from '../components';
import type { AppController } from '../store';
import {
  gojuonLayout,
  hiraganaDakuten,
  hiraganaYoon,
  katakanaDakuten,
  katakanaYoon,
  type KanaCell,
  type KanaType,
} from '../kana/kanaData';

// Korean UI strings (inline consts per task rules).
const T = {
  title: '가나 차트',
  subtitle: '글자를 눌러 발음을 듣고 로마자를 확인하세요',
  hira: '히라가나',
  kata: '가타카나',
  gojuon: '기본 (오십음도)',
  dakuten: '탁음 / 반탁음',
  yoon: '요음',
  home: '홈으로',
  tapHint: '글자를 탭하면 소리가 나요',
};

function speakKana(kana: string) {
  Speech.stop();
  Speech.speak(kana, { language: 'ja-JP', rate: 0.85 });
}

function KanaTile({
  cell,
  color,
  selected,
  onPress,
}: {
  cell: KanaCell | null;
  color: string;
  selected: boolean;
  onPress: (c: KanaCell) => void;
}) {
  const { theme } = useTheme();
  // Empty slot in the 5-wide grid: keep the gap so rows stay aligned.
  if (!cell) {
    return <View style={{ flexBasis: '18%', flexGrow: 0, aspectRatio: 1, margin: '1%' }} />;
  }
  const c = cell;
  return (
    <Pressable
      onPress={() => onPress(c)}
      accessibilityRole="button"
      accessibilityLabel={`${c.kana} ${c.romaji}`}
      accessibilityState={{ selected }}
      style={{ flexBasis: '18%', flexGrow: 0, aspectRatio: 1, margin: '1%' }}
    >
      <View
        style={{
          flex: 1,
          borderRadius: 12,
          borderWidth: selected ? 2 : 1,
          borderColor: selected ? color : theme.colors.border,
          backgroundColor: selected ? theme.colors.accentSoft : theme.colors.card,
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Text style={{ fontSize: 22, fontWeight: '800', color: theme.colors.text }}>{c.kana}</Text>
        <Text style={{ fontSize: 10, color: theme.colors.subtext, marginTop: 2 }}>{c.romaji}</Text>
      </View>
    </Pressable>
  );
}

// Wrap-based grid. Basic grid uses fixed 5-wide layout (with blanks); the
// extra sections just wrap naturally at ~5 per row.
function KanaGrid({
  cells,
  color,
  selectedKana,
  onPress,
}: {
  cells: (KanaCell | null)[];
  color: string;
  selectedKana: string | null;
  onPress: (c: KanaCell) => void;
}) {
  return (
    <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
      {cells.map((cell, i) => (
        <KanaTile
          key={cell ? `${cell.type}-${cell.group}-${cell.kana}` : `blank-${i}`}
          cell={cell}
          color={color}
          selected={cell != null && cell.kana === selectedKana}
          onPress={onPress}
        />
      ))}
    </View>
  );
}

export function KanaChartScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const color = personaColor(app.selectedPersonaId);
  const [type, setType] = React.useState<KanaType>('hira');
  const [selected, setSelected] = React.useState<KanaCell | null>(null);

  const gojuon = gojuonLayout(type);
  const dakuten = type === 'hira' ? hiraganaDakuten : katakanaDakuten;
  const yoon = type === 'hira' ? hiraganaYoon : katakanaYoon;

  const onTap = (c: KanaCell) => {
    setSelected(c);
    speakKana(c.kana);
    app.track('kana_tapped', { kana: c.kana });
  };

  const switchType = (next: KanaType) => {
    if (next === type) return;
    setType(next);
    setSelected(null);
  };

  const Toggle = ({ value, label }: { value: KanaType; label: string }) => {
    const active = type === value;
    return (
      <Pressable
        onPress={() => switchType(value)}
        accessibilityRole="button"
        accessibilityLabel={label}
        accessibilityState={{ selected: active }}
        style={{ flex: 1 }}
      >
        <View
          style={{
            paddingVertical: 10,
            borderRadius: 10,
            alignItems: 'center',
            backgroundColor: active ? color : theme.colors.chip,
          }}
        >
          <Text style={{ fontWeight: '800', color: active ? '#fff' : theme.colors.chipText }}>{label}</Text>
        </View>
      </Pressable>
    );
  };

  const Section = ({ label, cells }: { label: string; cells: (KanaCell | null)[] }) => (
    <Fade delay={80}>
      <View style={{ marginTop: 18 }}>
        <Text style={{ fontSize: 14, fontWeight: '800', color: theme.colors.text, marginBottom: 8 }}>{label}</Text>
        <KanaGrid cells={cells} color={color} selectedKana={selected?.kana ?? null} onPress={onTap} />
      </View>
    </Fade>
  );

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>{T.title}</Title>
          <Pill label={type === 'hira' ? T.hira : T.kata} color={color} />
        </View>
        <Muted>{T.subtitle}</Muted>
      </Fade>

      <Fade delay={40}>
        <View style={{ flexDirection: 'row', gap: 10, marginTop: 12 }}>
          <Toggle value="hira" label={T.hira} />
          <Toggle value="kata" label={T.kata} />
        </View>
      </Fade>

      <Fade delay={60}>
        <Card style={{ marginTop: 14, alignItems: 'center', paddingVertical: 20 }}>
          {selected ? (
            <>
              <Text style={{ fontSize: 56, fontWeight: '900', color: theme.colors.text }}>{selected.kana}</Text>
              <Text style={{ fontSize: 20, fontWeight: '700', color, marginTop: 4 }}>{selected.romaji}</Text>
              <View style={{ marginTop: 12 }}>
                <Button icon="speaker" title="다시 듣기" onPress={() => speakKana(selected.kana)} secondary color={color} />
              </View>
            </>
          ) : (
            <Muted>{T.tapHint}</Muted>
          )}
        </Card>
      </Fade>

      <Section label={T.gojuon} cells={gojuon} />
      <Section label={T.dakuten} cells={dakuten} />
      <Section label={T.yoon} cells={yoon} />

      <View style={{ marginTop: 22, marginBottom: 8 }}>
        <Button title={T.home} onPress={() => app.navigate('home')} secondary />
      </View>
    </View>
  );
}
