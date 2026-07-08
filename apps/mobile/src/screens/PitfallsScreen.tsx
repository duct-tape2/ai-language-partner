import React from 'react';
import { Text, View, Pressable } from 'react-native';
import type { AppController } from '../store';
import { useTheme } from '../ThemeContext';
import { Card, Button, Title, Muted, Pill, Fade, FuriganaTokens } from '../components';
import { Icon } from '../icons';
import { personaColor } from '../personaStyle';
import { PITFALLS, PITFALL_CATEGORIES, type PitfallCategory, type Pitfall } from '../pitfalls/pitfallData';

const KO = {
  title: '한국인이 자주 틀리는 일본어',
  intro: '한국어를 그대로 직역하면 틀리는 포인트만 모았어요. 카테고리를 고르고 항목을 눌러 확인하세요.',
  all: '전체',
  wrong: '이렇게 쓰면 틀려요',
  right: '이게 맞아요',
  why: '왜 틀릴까',
  tip: '한 줄 팁',
  listen: '발음 듣기',
  back: '닫기',
  home: '홈으로',
  count: (n: number) => `${n}개 함정`,
};

const CAT_ICON: Record<PitfallCategory, string> = {
  조사: '=',
  한자어: '漢',
  경어: '敬',
  어순: '順',
  발음: '音',
  표현: '表',
};

export function PitfallsScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const accent = personaColor(app.selectedPersonaId);
  const [cat, setCat] = React.useState<PitfallCategory | 'all'>('all');
  const [openId, setOpenId] = React.useState<string | null>(null);

  const list = React.useMemo(
    () => (cat === 'all' ? PITFALLS : PITFALLS.filter((p) => p.category === cat)),
    [cat],
  );
  const open = openId ? PITFALLS.find((p) => p.id === openId) ?? null : null;

  const selectCat = (c: PitfallCategory | 'all') => {
    setCat(c);
    setOpenId(null);
  };

  const openItem = (p: Pitfall) => {
    setOpenId(p.id);
    app.track('pitfall_opened', { id: p.id, category: p.category });
  };

  return (
    <View>
      <Fade>
        <Title>{KO.title}</Title>
        <Muted>{KO.intro}</Muted>
      </Fade>

      <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 12, marginBottom: 6 }}>
        <CatChip label={KO.all} active={cat === 'all'} accent={accent} onPress={() => selectCat('all')} />
        {PITFALL_CATEGORIES.map((c) => (
          <CatChip key={c} label={`${CAT_ICON[c]} ${c}`} active={cat === c} accent={accent} onPress={() => selectCat(c)} />
        ))}
      </View>

      <View style={{ marginTop: 4, marginBottom: 8 }}>
        <Muted>{KO.count(list.length)}</Muted>
      </View>

      {open ? (
        <Fade>
          <DetailCard pitfall={open} accent={accent} onClose={() => setOpenId(null)} onSpeak={() => app.speak(open.rightJa)} />
        </Fade>
      ) : null}

      {list.map((p, i) => (
        <Fade key={p.id} delay={Math.min(i, 8) * 24}>
          <Pressable onPress={() => openItem(p)} accessibilityRole="button" accessibilityLabel={p.koTrap}>
            <View
              style={{
                backgroundColor: openId === p.id ? theme.colors.accentSoft : theme.colors.card,
                borderRadius: theme.radius.md,
                borderWidth: 1,
                borderColor: openId === p.id ? accent : theme.colors.border,
                paddingVertical: 14,
                paddingHorizontal: 16,
                marginBottom: 10,
                flexDirection: 'row',
                alignItems: 'center',
              }}
            >
              <View
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: 10,
                  backgroundColor: theme.colors.chip,
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginRight: 12,
                }}
              >
                <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.chipText }}>{CAT_ICON[p.category]}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 12, fontWeight: '700', color: accent, marginBottom: 2 }}>{p.category}</Text>
                <Text style={{ fontSize: 15, fontWeight: '600', color: theme.colors.text, lineHeight: 21 }}>{p.koTrap}</Text>
              </View>
              <Text style={{ fontSize: 20, color: theme.colors.subtext, marginLeft: 8 }}>{openId === p.id ? '-' : '+'}</Text>
            </View>
          </Pressable>
        </Fade>
      ))}

      <View style={{ marginTop: 8, marginBottom: 24 }}>
        <Button title={KO.home} secondary onPress={() => app.navigate('home')} />
      </View>
    </View>
  );
}

function CatChip({ label, active, accent, onPress }: { label: string; active: boolean; accent: string; onPress: () => void }) {
  const { theme } = useTheme();
  return (
    <Pressable onPress={onPress} accessibilityRole="button" accessibilityLabel={label} accessibilityState={{ selected: active }}>
      <View
        style={{
          backgroundColor: active ? accent : theme.colors.chip,
          borderRadius: 999,
          paddingHorizontal: 14,
          paddingVertical: 8,
          marginRight: 8,
          marginTop: 8,
          borderWidth: 1,
          borderColor: active ? accent : theme.colors.border,
        }}
      >
        <Text style={{ color: active ? '#fff' : theme.colors.chipText, fontSize: 13, fontWeight: '700' }}>{label}</Text>
      </View>
    </Pressable>
  );
}

function DetailCard({
  pitfall,
  accent,
  onClose,
  onSpeak,
}: {
  pitfall: Pitfall;
  accent: string;
  onClose: () => void;
  onSpeak: () => void;
}) {
  const { theme } = useTheme();
  return (
    <Card style={{ borderColor: accent, borderWidth: 2 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <Pill label={pitfall.category} color={accent} />
        <Pressable onPress={onClose} accessibilityRole="button" accessibilityLabel={KO.back}>
          <Text style={{ fontSize: 14, fontWeight: '700', color: theme.colors.subtext, paddingHorizontal: 8, paddingVertical: 4 }}>
            {KO.back}
          </Text>
        </Pressable>
      </View>

      <Text style={{ fontSize: 16, fontWeight: '700', color: theme.colors.text, marginBottom: 14, lineHeight: 23 }}>
        {pitfall.koTrap}
      </Text>

      <View
        style={{
          backgroundColor: theme.colors.card,
          borderRadius: theme.radius.md,
          borderWidth: 1,
          borderColor: theme.colors.bad,
          padding: 12,
          marginBottom: 10,
        }}
      >
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
          <Icon name="close" size={14} color={theme.colors.bad} />
          <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.bad, marginLeft: 6 }}>{KO.wrong}</Text>
        </View>
        <FuriganaTokens tokens={pitfall.wrongTokens} size={22} color={theme.colors.bad} />
      </View>

      <View
        style={{
          backgroundColor: theme.colors.card,
          borderRadius: theme.radius.md,
          borderWidth: 1,
          borderColor: theme.colors.good,
          padding: 12,
          marginBottom: 14,
        }}
      >
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
          <Icon name="check" size={14} color={theme.colors.good} />
          <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.good, marginLeft: 6 }}>{KO.right}</Text>
        </View>
        <FuriganaTokens tokens={pitfall.rightTokens} size={22} color={theme.colors.good} />
      </View>

      <Button title={KO.listen} onPress={onSpeak} color={accent} />

      <View style={{ marginTop: 14, marginBottom: 4 }}>
        <Text style={{ fontSize: 13, fontWeight: '800', color: theme.colors.accentDark, marginBottom: 6 }}>{KO.why}</Text>
        <Text style={{ fontSize: 14, color: theme.colors.text, lineHeight: 22 }}>{pitfall.whyKo}</Text>
      </View>

      <View
        style={{
          marginTop: 12,
          backgroundColor: theme.colors.accentSoft,
          borderRadius: theme.radius.md,
          padding: 12,
          borderWidth: 1,
          borderColor: theme.colors.border,
        }}
      >
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 4 }}>
          <Icon name="bulb" size={14} color={theme.colors.accentDark} />
          <Text style={{ fontSize: 13, fontWeight: '800', color: theme.colors.accentDark, marginLeft: 6 }}>{KO.tip}</Text>
        </View>
        <Text style={{ fontSize: 14, fontWeight: '600', color: theme.colors.text, lineHeight: 22 }}>{pitfall.tipKo}</Text>
      </View>
    </Card>
  );
}
