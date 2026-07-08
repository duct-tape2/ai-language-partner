import React from 'react';
import { Text, View, Pressable } from 'react-native';
import type { AppController } from '../store';
import { useTheme } from '../ThemeContext';
import { Card, Button, Title, Muted, Pill, Fade, FuriganaTokens } from '../components';
import { personaColor } from '../personaStyle';
import {
  CULTURE_NOTES,
  CULTURE_CATEGORIES,
  type CultureCategory,
  type CultureNote,
} from '../culture/cultureNotes';

const KO = {
  title: '일본 문화·매너 노트',
  intro: '여행·유학·비즈니스에서 한국과 다른 일본의 매너와 관습을 정리했어요. 카테고리를 고르고 항목을 눌러 확인하세요.',
  all: '전체',
  detail: '이럴 때는',
  phrase: '이 표현도 함께',
  listen: '발음 듣기',
  back: '닫기',
  home: '홈으로',
  count: (n: number) => `${n}개 노트`,
};

const CAT_ICON: Record<CultureCategory, string> = {
  식사: '食',
  인사: '挨',
  선물: '贈',
  대중교통: '駅',
  경조사: '礼',
  직장: '仕',
  생활: '住',
  표현: '言',
};

export function CultureScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const accent = personaColor(app.selectedPersonaId);
  const [cat, setCat] = React.useState<CultureCategory | 'all'>('all');
  const [openId, setOpenId] = React.useState<string | null>(null);

  const list = React.useMemo(
    () => (cat === 'all' ? CULTURE_NOTES : CULTURE_NOTES.filter((n) => n.category === cat)),
    [cat],
  );
  const open = openId ? CULTURE_NOTES.find((n) => n.id === openId) ?? null : null;

  const selectCat = (c: CultureCategory | 'all') => {
    setCat(c);
    setOpenId(null);
  };

  const openItem = (n: CultureNote) => {
    setOpenId(n.id);
    app.track('culture_opened', { id: n.id });
  };

  return (
    <View>
      <Fade>
        <Title>{KO.title}</Title>
        <Muted>{KO.intro}</Muted>
      </Fade>

      <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 12, marginBottom: 6 }}>
        <CatChip label={KO.all} active={cat === 'all'} accent={accent} onPress={() => selectCat('all')} />
        {CULTURE_CATEGORIES.map((c) => (
          <CatChip
            key={c}
            label={`${CAT_ICON[c]} ${c}`}
            active={cat === c}
            accent={accent}
            onPress={() => selectCat(c)}
          />
        ))}
      </View>

      <View style={{ marginTop: 4, marginBottom: 8 }}>
        <Muted>{KO.count(list.length)}</Muted>
      </View>

      {open ? (
        <Fade>
          <DetailCard note={open} accent={accent} onClose={() => setOpenId(null)} onSpeak={() => open.jaPhrase && app.speak(open.jaPhrase)} />
        </Fade>
      ) : null}

      {list.map((n, i) => (
        <Fade key={n.id} delay={Math.min(i, 8) * 24}>
          <Pressable onPress={() => openItem(n)} accessibilityRole="button" accessibilityLabel={n.titleKo}>
            <View
              style={{
                backgroundColor: openId === n.id ? theme.colors.accentSoft : theme.colors.card,
                borderRadius: theme.radius.md,
                borderWidth: 1,
                borderColor: openId === n.id ? accent : theme.colors.border,
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
                <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.chipText }}>{CAT_ICON[n.category]}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 12, fontWeight: '700', color: accent, marginBottom: 2 }}>{n.category}</Text>
                <Text style={{ fontSize: 15, fontWeight: '600', color: theme.colors.text, lineHeight: 21 }}>{n.titleKo}</Text>
              </View>
              <Text style={{ fontSize: 20, color: theme.colors.subtext, marginLeft: 8 }}>{openId === n.id ? '-' : '+'}</Text>
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
  note,
  accent,
  onClose,
  onSpeak,
}: {
  note: CultureNote;
  accent: string;
  onClose: () => void;
  onSpeak: () => void;
}) {
  const { theme } = useTheme();
  return (
    <Card style={{ borderColor: accent, borderWidth: 2 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <Pill label={note.category} color={accent} />
        <Pressable onPress={onClose} accessibilityRole="button" accessibilityLabel={KO.back}>
          <Text style={{ fontSize: 14, fontWeight: '700', color: theme.colors.subtext, paddingHorizontal: 8, paddingVertical: 4 }}>
            {KO.back}
          </Text>
        </Pressable>
      </View>

      <Text style={{ fontSize: 18, fontWeight: '800', color: theme.colors.text, marginBottom: 12, lineHeight: 25 }}>
        {note.titleKo}
      </Text>

      <Text style={{ fontSize: 15, color: theme.colors.text, lineHeight: 24, marginBottom: note.jaTokens ? 16 : 4 }}>
        {note.bodyKo}
      </Text>

      {note.jaTokens ? (
        <View
          style={{
            backgroundColor: theme.colors.accentSoft,
            borderRadius: theme.radius.md,
            borderWidth: 1,
            borderColor: theme.colors.border,
            padding: 12,
            marginBottom: 12,
          }}
        >
          <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.accentDark, marginBottom: 8 }}>{KO.phrase}</Text>
          <FuriganaTokens tokens={note.jaTokens} size={22} color={accent} />
          {note.jaKo ? (
            <Text style={{ fontSize: 14, color: theme.colors.subtext, marginTop: 8, lineHeight: 21 }}>{note.jaKo}</Text>
          ) : null}
        </View>
      ) : null}

      {note.jaPhrase ? <Button title={KO.listen} onPress={onSpeak} color={accent} /> : null}
    </Card>
  );
}
