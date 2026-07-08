import React from 'react';
import { ScrollView, Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { Mascot, type Expression, type Outfit } from './Mascot';

// Web-only visual test harness (reached via ?pose=1). Renders the real Mascot
// component in every expression/outfit so the rig can be screenshot-verified.
const CELLS: { label: string; personaId: string; expression?: Expression; outfit?: Outfit; speaking?: boolean }[] = [
  { label: '유이 idle', personaId: 'yui' },
  { label: '유이 listening', personaId: 'yui', expression: 'listening' },
  { label: '유이 correcting', personaId: 'yui', expression: 'correcting' },
  { label: '유이 cheer', personaId: 'yui', expression: 'cheer' },
  { label: '유이 thinking', personaId: 'yui', expression: 'thinking' },
  { label: '유이 scarf', personaId: 'yui', outfit: 'scarf' },
  { label: '하루카 listening', personaId: 'haruka', expression: 'listening' },
  { label: '하루카 correcting', personaId: 'haruka', expression: 'correcting' },
  { label: '하루카 cheer', personaId: 'haruka', expression: 'cheer' },
  { label: '렌 wink', personaId: 'ren', expression: 'wink' },
  { label: '렌 cheer', personaId: 'ren', expression: 'cheer' },
  { label: '렌 beanie', personaId: 'ren', outfit: 'beanie' },
];

export function PoseSheet() {
  const { theme } = useTheme();
  return (
    <ScrollView contentContainerStyle={{ padding: 16, backgroundColor: theme.colors.bg }}>
      <Text style={{ fontSize: 20, fontWeight: '800', color: theme.colors.text, marginBottom: 12 }}>표정 / 포즈 / 의상 시트</Text>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' }}>
        {CELLS.map((c) => (
          <View key={c.label} style={{ width: '32%', alignItems: 'center', backgroundColor: theme.colors.card, borderRadius: 16, paddingVertical: 8, marginBottom: 10, borderWidth: 1, borderColor: theme.colors.border }}>
            <Mascot personaId={c.personaId} size={96} expression={c.expression} outfit={c.outfit} speaking={c.speaking} />
            <Text style={{ fontSize: 12, color: theme.colors.subtext }}>{c.label}</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}
