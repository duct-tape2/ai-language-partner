import React from 'react';
import { Pressable, Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { STRINGS } from '../i18n';
import { personaColor } from '../personaStyle';
import { Button, Card, EmptyState, Fade, Muted, Pill, Title } from '../components';
import type { AppController } from '../store';
import { api, resolveApiUrl, synthesizePersona, USE_MOCK } from '../api/client';
import { AudioQueue } from '../dialogue/audioQueue';
import type { VoiceCatalogItem } from '../dialogue/types';

const PREVIEW_LINE = 'こんにちは。今日も一緒に話しましょう。';

export function VoiceGalleryScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const [voices, setVoices] = React.useState<VoiceCatalogItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [filter, setFilter] = React.useState<string>('all');
  const [playingId, setPlayingId] = React.useState<string | null>(null);
  const queueRef = React.useRef<AudioQueue | null>(null);

  const queue = () => {
    if (!queueRef.current) queueRef.current = new AudioQueue();
    return queueRef.current;
  };

  React.useEffect(() => {
    api
      .listVoices()
      .then((v) => setVoices(Array.isArray(v) ? v : []))
      .catch(() => setVoices([]))
      .finally(() => setLoading(false));
    return () => queue().cancel();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const personaIds = Array.from(new Set(voices.map((v) => v.personaId).filter((p): p is string => !!p)));
  const shown = filter === 'all' ? voices : voices.filter((v) => v.personaId === filter);
  const personaName = (id: string) =>
    app.personas.find((p) => p.id === id)?.displayName ?? (id.charAt(0).toUpperCase() + id.slice(1));

  const playSample = async (v: VoiceCatalogItem) => {
    queue().cancel();
    setPlayingId(v.voiceId);
    app.track('voice_gallery_previewed', { voiceId: v.voiceId, personaId: v.personaId ?? null });
    await queue().play([{ uri: resolveApiUrl(v.sampleUrl), text: v.characterName, personaId: v.personaId ?? 'yui' }]);
    setPlayingId((id) => (id === v.voiceId ? null : id));
  };

  const previewPersona = async (personaId: string) => {
    queue().cancel();
    setPlayingId(`persona:${personaId}`);
    try {
      const res = await synthesizePersona(PREVIEW_LINE, personaId);
      if (res.audioUrl) {
        await queue().play([{ uri: resolveApiUrl(res.audioUrl), text: PREVIEW_LINE, personaId }]);
      } else {
        await queue().play([{ uri: null, text: PREVIEW_LINE, personaId }]);
      }
    } catch {
      // ignore
    }
    setPlayingId((id) => (id === `persona:${personaId}` ? null : id));
  };

  return (
    <View>
      <Fade>
        <Title>{STRINGS.voiceGallery.title}</Title>
        <Muted>{STRINGS.voiceGallery.subtitle}</Muted>
        {!loading && voices.length > 0 && (
          <View style={{ alignSelf: 'flex-start' }}>
            <Pill label={STRINGS.voiceGallery.countLabel(voices.length)} />
          </View>
        )}
      </Fade>

      {loading ? (
        <Fade delay={60}>
          <Muted>불러오는 중…</Muted>
        </Fade>
      ) : voices.length === 0 ? (
        <Fade delay={60}>
          <Card>
            <EmptyState
              icon="soundwave"
              title="목소리 갤러리 (데모)"
              desc={STRINGS.voiceGallery.empty}
              cta={{ label: STRINGS.common.back, onPress: () => app.navigate('settings') }}
            />
          </Card>
        </Fade>
      ) : (
        <>
          {personaIds.length > 0 && (
            <Fade delay={40}>
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginBottom: 6 }}>
                <FilterChip label={STRINGS.voiceGallery.all} active={filter === 'all'} onPress={() => setFilter('all')} />
                {personaIds.map((pid) => (
                  <FilterChip key={pid} label={personaName(pid)} active={filter === pid} color={personaColor(pid)} onPress={() => setFilter(pid)} />
                ))}
              </View>
            </Fade>
          )}

          {filter !== 'all' && (
            <Fade delay={60}>
              <Button title={STRINGS.voiceGallery.previewPersona(filter)} onPress={() => previewPersona(filter)} color={personaColor(filter)} />
            </Fade>
          )}

          {shown.map((v, i) => {
            const active = playingId === v.voiceId;
            const accessibilityLabel = [
              active ? STRINGS.voiceGallery.playing : STRINGS.voiceGallery.play,
              v.characterName,
              v.styleName,
            ].join(', ');
            return (
              <Fade key={v.voiceId} delay={Math.min(200, 60 + i * 10)}>
                <Pressable onPress={() => playSample(v)} accessibilityRole="button" accessibilityLabel={accessibilityLabel}>
                  <Card style={active ? { borderColor: theme.colors.accent, borderWidth: 1.5 } : undefined}>
                    <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                      <View style={{ flex: 1 }}>
                        <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text }}>
                          {v.characterName} · {v.styleName}
                        </Text>
                        <Muted>{v.creditText}</Muted>
                      </View>
                      <Text style={{ fontSize: 15, color: theme.colors.accentDark, fontWeight: '700' }}>
                        {active ? STRINGS.voiceGallery.playing : STRINGS.voiceGallery.play}
                      </Text>
                    </View>
                  </Card>
                </Pressable>
              </Fade>
            );
          })}
        </>
      )}

      <Fade delay={80}>
        <Button title={STRINGS.common.back} onPress={() => app.navigate('settings')} secondary />
      </Fade>
    </View>
  );
}

function FilterChip({ label, active, color, onPress }: { label: string; active: boolean; color?: string; onPress: () => void }) {
  const { theme } = useTheme();
  const c = color ?? theme.colors.accent;
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
      style={{ backgroundColor: active ? c : theme.colors.chip, borderRadius: 999, paddingHorizontal: 14, paddingVertical: 8, marginRight: 8, marginBottom: 8 }}
    >
      <Text style={{ color: active ? '#fff' : theme.colors.chipText, fontWeight: '700', fontSize: 14 }}>{label}</Text>
    </Pressable>
  );
}
