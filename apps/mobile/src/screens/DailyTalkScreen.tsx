import React from 'react';
import { Platform, Pressable, Text, View } from 'react-native';
import { Audio } from 'expo-av';
import { useTheme } from '../ThemeContext';
import { STRINGS } from '../i18n';
import { personaColor } from '../personaStyle';
import { Button, Card, Fade, FuriganaTokens, Muted, Pill, Title } from '../components';
import type { AppController } from '../store';
import { api, transcribeAudioFile, USE_MOCK } from '../api/client';
import { DialogueRunner } from '../dialogue/runner';
import { AudioQueue, type PlayItem } from '../dialogue/audioQueue';
import { matchMock } from '../dialogue/matchMock';
import { clearAudioCache, listPacks, loadPack, playableUri, randomLineOfCategory, type PackState } from '../dialogue/packManager';
import type { AdvanceResult, Candidate, DialoguePackSummary, DialogueMatchResponse, LoadedPack, PersonaTurn } from '../dialogue/types';

type Phase = 'setup' | 'active' | 'summary';
type Status = 'idle' | 'listening' | 'recognizing' | 'speaking' | 'userTurn';

const TOPICS = [
  { label: '인사', id: 'greetings_intro' },
  { label: '오늘', id: 'today' },
  { label: '음식 주문', id: 'food_order' },
  { label: '취미', id: 'hobbies' },
  { label: '날씨', id: 'weather_seasons' },
];
const LEVELS = ['N5', 'N4'];

// 16kHz mono recording — iOS default preset is 44.1kHz, so override (contract §6.1).
function recordingOptions(): Audio.RecordingOptions {
  const base = Audio.RecordingOptionsPresets.HIGH_QUALITY;
  return {
    ...base,
    android: { ...base.android, sampleRate: 16000, numberOfChannels: 1 },
    ios: { ...base.ios, sampleRate: 16000, numberOfChannels: 1 },
  };
}

export function DailyTalkScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const [phase, setPhase] = React.useState<Phase>('setup');
  const [packs, setPacks] = React.useState<DialoguePackSummary[]>([]);
  const [personaId, setPersonaId] = React.useState<string>(app.selectedPersonaId || 'yui');
  const [topicId, setTopicId] = React.useState(TOPICS[0].id);
  const [level, setLevel] = React.useState(LEVELS[0]);
  const [packState, setPackState] = React.useState<PackState>('idle');

  const [status, setStatus] = React.useState<Status>('idle');
  const [persona, setPersona] = React.useState<PersonaTurn | null>(null);
  const [choices, setChoices] = React.useState<Candidate[]>([]);
  const [recognized, setRecognized] = React.useState<string | null>(null);
  const [pendingConfirm, setPendingConfirm] = React.useState<Candidate | null>(null);
  const [emphasizeChips, setEmphasizeChips] = React.useState(false);
  const [showKo, setShowKo] = React.useState(false);
  const [turns, setTurns] = React.useState(0);
  const [micDenied, setMicDenied] = React.useState(false);
  const [saved, setSaved] = React.useState(false);

  const runnerRef = React.useRef<DialogueRunner | null>(null);
  const packRef = React.useRef<LoadedPack | null>(null);
  const queueRef = React.useRef<AudioQueue | null>(null);
  const recRef = React.useRef<Audio.Recording | null>(null);
  const color = personaColor(personaId);

  // Show the human display name ("유이"), never the raw pack id ("yui"). Pack ids
  // not in the persona catalog fall back to a capitalized id.
  const personaName = (id: string) =>
    app.personas.find((p) => p.id === id)?.displayName ?? (id.charAt(0).toUpperCase() + id.slice(1));

  const queue = () => {
    if (!queueRef.current) queueRef.current = new AudioQueue();
    return queueRef.current;
  };

  React.useEffect(() => {
    listPacks()
      .then((p) => {
        setPacks(p);
        if (p.length && !p.some((x) => x.personaId === personaId)) setPersonaId(p[0].personaId);
      })
      .catch(() => setPacks([]));
    return () => {
      queue().cancel();
      clearAudioCache();
      void recRef.current?.stopAndUnloadAsync().catch(() => undefined);
      recRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const packVersion = () => packs.find((p) => p.personaId === personaId)?.packVersion ?? 'v1';

  const playLines = async (ids: string[]): Promise<void> => {
    const pack = packRef.current;
    if (!pack) return;
    const items: PlayItem[] = [];
    for (const id of ids) {
      const entry = pack.audioIndex[id];
      const uri = await playableUri(pack, id);
      items.push({ uri, text: entry?.text ?? '', personaId });
    }
    await queue().play(items);
  };

  const applyAdvance = (res: AdvanceResult, turnsNow?: number) => {
    setShowKo(false);
    if (res.ended) {
      setChoices([]);
      app.completeMission();
      app.track('daily_talk_turn_completed', { ended: true, turns: turnsNow ?? turns });
      if (res.persona) {
        setPersona(res.persona);
        setStatus('speaking');
        void playLines([res.persona.lineId]).then(() => setPhase('summary'));
      } else {
        setTimeout(() => setPhase('summary'), 300);
      }
      return;
    }
    setChoices(res.choices);
    if (res.persona) {
      setPersona(res.persona);
      setStatus('speaking');
      // Transition to userTurn only when the persona audio actually finishes, so the
      // barge-in guard (queue().isPlaying()) can interrupt mid-line.
      void playLines([res.persona.lineId]).then(() => setStatus((s) => (s === 'speaking' ? 'userTurn' : s)));
    } else {
      setStatus('userTurn');
    }
  };

  const start = async () => {
    setPackState('downloading');
    try {
      const pack = await loadPack(personaId, packVersion());
      packRef.current = pack;
      runnerRef.current = new DialogueRunner(pack.story, { topicId, level });
      setPackState('ready');
      app.track('pack_downloaded', { personaId, packVersion: pack.packVersion });
      app.track('daily_talk_started', { personaId, topicId, level });
      setPhase('active');
      applyAdvance(runnerRef.current.current());
    } catch {
      setPackState('error');
    }
  };

  const chooseCandidate = (c: Candidate) => {
    const runner = runnerRef.current;
    if (!runner) return;
    setRecognized(c.text);
    setEmphasizeChips(false);
    setPendingConfirm(null);
    const nextTurns = turns + 1;
    setTurns(nextTurns);
    app.track('daily_talk_turn_completed', { tier: 'match', lineId: c.lineId });
    applyAdvance(runner.choose(c), nextTurns);
  };

  const runMatch = async (utterance: string) => {
    const pack = packRef.current;
    if (!pack || !runnerRef.current) return;
    setRecognized(utterance);
    setStatus('recognizing');
    const filler = randomLineOfCategory(pack, 'filler');
    if (filler) void playLines([filler.lineId]);

    const confirmFallback = randomLineOfCategory(pack, 'confirm');
    let resp: DialogueMatchResponse;
    if (USE_MOCK) {
      resp = matchMock(utterance, choices, confirmFallback?.lineId ?? null);
    } else {
      resp = await api.dialogueMatch({
        personaId,
        packVersion: pack.packVersion,
        utterance,
        candidateLineIds: choices.map((c) => c.lineId),
        globalIntents: true,
      });
    }

    if (resp.globalIntent === 'repeat' || resp.globalIntent === 'slow') {
      if (persona) void playLines([persona.lineId]);
      setStatus('userTurn');
      return;
    }
    if (resp.globalIntent === 'hint') {
      setEmphasizeChips(true);
      setStatus('userTurn');
      return;
    }
    if (resp.globalIntent === 'quit') {
      app.track('daily_talk_turn_completed', { quit: true });
      setPhase('summary');
      return;
    }

    if (resp.tier === 'match' && resp.matchedLineId) {
      const c = choices.find((x) => x.lineId === resp.matchedLineId);
      if (c) return chooseCandidate(c);
    }
    if (resp.tier === 'confirm') {
      const c = choices.find((x) => x.lineId === resp.matchedLineId) ?? null;
      setPendingConfirm(c);
      const cid = resp.confirmLineId ?? confirmFallback?.lineId ?? null;
      if (cid) {
        setStatus('speaking');
        void playLines([cid]);
      }
      app.track('daily_talk_confirm_shown', { lineId: resp.matchedLineId, score: resp.score });
      setStatus('userTurn');
      return;
    }
    // fallback
    const fb = randomLineOfCategory(pack, 'fallback');
    if (fb) {
      setStatus('speaking');
      void playLines([fb.lineId]);
    }
    setEmphasizeChips(true);
    const nodeId = runnerRef.current.snapshot().nodeId ?? 'unknown';
    void api.logUnmatched(personaId, pack.packVersion, nodeId, utterance, USE_MOCK ? 0.5 : 1);
    app.track('daily_talk_fallback_shown', { utterance });
    setStatus('userTurn');
  };

  const onMic = async () => {
    // Barge-in: interrupt whatever the queue is actually playing (status alone is
    // unreliable — persona lines flip to userTurn while audio is still playing).
    if (queue().isPlaying()) {
      queue().cancel();
      app.track('daily_talk_barge_in', {});
    }
    if (USE_MOCK) {
      const guess = choices.length ? choices[Math.floor(Math.random() * choices.length)].text : '';
      await runMatch(guess);
      return;
    }
    if (recRef.current) {
      try {
        const rec = recRef.current;
        recRef.current = null;
        await rec.stopAndUnloadAsync();
        const uri = rec.getURI();
        setStatus('recognizing');
        if (!uri) return;
        const type = Platform.OS === 'ios' ? 'audio/wav' : Platform.OS === 'web' ? 'audio/webm' : 'audio/m4a';
        const stt = await transcribeAudioFile({ uri, type }, choices.map((c) => c.lineId));
        await runMatch(stt.text);
      } catch {
        setMicDenied(true);
        app.track('stt_failed', { reason: 'transcribe_error' });
        setStatus('userTurn');
      }
      return;
    }
    const perm = await Audio.requestPermissionsAsync();
    if (!perm.granted) {
      setMicDenied(true);
      app.track('stt_failed', { reason: 'permission_denied' });
      return;
    }
    await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
    let rec: Audio.Recording | null = null;
    try {
      rec = new Audio.Recording();
      await rec.prepareToRecordAsync(recordingOptions());
      await rec.startAsync();
      recRef.current = rec;
      rec = null; // ownership transferred to recRef
      setStatus('listening');
    } catch {
      if (rec) {
        try {
          await rec.stopAndUnloadAsync();
        } catch {
          // already unloaded
        }
      }
      setMicDenied(true);
      app.track('stt_failed', { reason: 'record_error' });
      setStatus('userTurn');
    }
  };

  const confirmYes = () => {
    if (pendingConfirm) return chooseCandidate(pendingConfirm);
    setPendingConfirm(null);
  };
  const confirmNo = () => {
    setPendingConfirm(null);
    setEmphasizeChips(true);
    setStatus('userTurn');
  };

  const saveCard = async () => {
    if (!persona) return;
    try {
      await api.createReviewCard({ id: `dt_${persona.lineId}_${Date.now()}`, front: persona.ko, back: persona.text, tags: ['일상대화'] });
      setSaved(true);
    } catch {
      // best-effort
    }
  };

  // ----- render -----
  if (phase === 'setup') {
    const personaIds = packs.length ? Array.from(new Set(packs.map((p) => p.personaId))) : ['yui'];
    return (
      <View>
        <Fade>
          <Title>{STRINGS.dailyTalk.title}</Title>
          <Muted>{STRINGS.dailyTalk.subtitle}</Muted>
          <View style={{ alignSelf: 'flex-start' }}>
            <Pill label={USE_MOCK ? STRINGS.dailyTalk.demoBadge : STRINGS.dailyTalk.liveBadge} />
          </View>
        </Fade>
        <Fade delay={60}>
          <Card>
            <Muted>{STRINGS.dailyTalk.pickPersona}</Muted>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 6 }}>
              {personaIds.map((pid) => (
                <Chip key={pid} label={personaName(pid)} active={pid === personaId} color={personaColor(pid)} onPress={() => setPersonaId(pid)} />
              ))}
            </View>
            <Muted>{STRINGS.dailyTalk.pickTopic}</Muted>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 6 }}>
              {TOPICS.map((t) => (
                <Chip key={t.id} label={t.label} active={t.id === topicId} color={color} onPress={() => setTopicId(t.id)} />
              ))}
            </View>
            <Muted>{STRINGS.dailyTalk.pickLevel}</Muted>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 6 }}>
              {LEVELS.map((l) => (
                <Chip key={l} label={l} active={l === level} color={color} onPress={() => setLevel(l)} />
              ))}
            </View>
          </Card>
          <Button
            title={packState === 'downloading' ? STRINGS.dailyTalk.loading : STRINGS.dailyTalk.start}
            onPress={start}
            color={color}
            disabled={packState === 'downloading'}
          />
          {packState === 'error' && <Muted>대화 팩을 불러오지 못했어요. 다시 시도해주세요.</Muted>}
        </Fade>
      </View>
    );
  }

  if (phase === 'summary') {
    return (
      <View>
        <Fade>
          <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft, alignItems: 'center' }}>
            <Title>{STRINGS.dailyTalk.endTitle}</Title>
            <Text style={{ fontSize: 16, color: theme.colors.text, marginTop: 4 }}>{STRINGS.dailyTalk.endTurns(turns)}</Text>
          </Card>
        </Fade>
        <Fade delay={80}>
          <Pressable onPress={saveCard} style={{ paddingVertical: 10, alignItems: 'center' }} accessibilityRole="button">
            <Text style={{ fontSize: 15, color: saved ? theme.colors.good : theme.colors.subtext, fontWeight: '700' }}>
              {saved ? STRINGS.dailyTalk.saved : STRINGS.dailyTalk.saveCard}
            </Text>
          </Pressable>
          <Button title={STRINGS.dailyTalk.toHome} onPress={() => app.navigate('home')} color={color} />
        </Fade>
      </View>
    );
  }

  // active
  const statusLabel =
    status === 'listening'
      ? STRINGS.dailyTalk.listening
      : status === 'recognizing'
        ? STRINGS.dailyTalk.recognizing
        : status === 'speaking'
          ? STRINGS.dailyTalk.speaking
          : STRINGS.dailyTalk.yourTurn;

  return (
    <View>
      <Fade>
        <Title>{STRINGS.dailyTalk.title}</Title>
        <View style={{ alignSelf: 'flex-start' }}>
          <Pill label={USE_MOCK ? STRINGS.dailyTalk.demoBadge : STRINGS.dailyTalk.liveBadge} />
        </View>
      </Fade>

      <Fade delay={60}>
        <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
          <Muted>{personaName(personaId)}</Muted>
          {persona ? (
            <View style={{ marginTop: 6 }}>
              <FuriganaTokens tokens={[{ b: persona.text }]} size={24} color={color} />
              {showKo ? (
                <Text style={{ fontSize: 15, color: theme.colors.subtext, marginTop: 6 }}>{persona.ko}</Text>
              ) : (
                <Pressable onPress={() => setShowKo(true)} accessibilityRole="button">
                  <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 6 }}>{STRINGS.dailyTalk.showKo}</Text>
                </Pressable>
              )}
            </View>
          ) : null}
          <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 10 }}>{statusLabel}</Text>
        </Card>
      </Fade>

      {recognized ? (
        <Fade delay={100}>
          <Card>
            <Muted>{STRINGS.dailyTalk.recognized}</Muted>
            <Text style={{ fontSize: 18, color: theme.colors.text, fontWeight: '700', marginTop: 2 }}>{recognized}</Text>
          </Card>
        </Fade>
      ) : null}

      {pendingConfirm ? (
        <Fade delay={120}>
          <Card style={{ borderColor: color, borderWidth: 1.5 }}>
            <Text style={{ fontSize: 16, color: theme.colors.text }}>{STRINGS.dailyTalk.confirmQ}</Text>
            <View style={{ flexDirection: 'row', marginTop: 8 }}>
              <View style={{ flex: 1, marginRight: 6 }}>
                <Button title={STRINGS.dailyTalk.yes} onPress={confirmYes} color={color} />
              </View>
              <View style={{ flex: 1, marginLeft: 6 }}>
                <Button title={STRINGS.dailyTalk.no} onPress={confirmNo} secondary color={color} />
              </View>
            </View>
          </Card>
        </Fade>
      ) : null}

      <Fade delay={140}>
        <Card style={emphasizeChips ? { borderColor: color, borderWidth: 1.5 } : undefined}>
          <Muted>{STRINGS.dailyTalk.suggestChips}</Muted>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 6 }}>
            {choices.map((c) => (
              <ChipJa key={c.lineId} candidate={c} color={color} onPress={() => chooseCandidate(c)} />
            ))}
          </View>
          <Button title={status === 'listening' ? STRINGS.dailyTalk.micStop : STRINGS.dailyTalk.mic} onPress={onMic} color={color} />
          {micDenied && <Muted>{STRINGS.dailyTalk.micDenied}</Muted>}
        </Card>
      </Fade>
    </View>
  );
}

function Chip({ label, active, color, onPress }: { label: string; active: boolean; color: string; onPress: () => void }) {
  const { theme } = useTheme();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
      style={{ backgroundColor: active ? color : theme.colors.chip, borderRadius: 999, paddingHorizontal: 14, paddingVertical: 8, marginRight: 8, marginBottom: 8 }}
    >
      <Text style={{ color: active ? '#fff' : theme.colors.chipText, fontWeight: '700', fontSize: 14 }}>{label}</Text>
    </Pressable>
  );
}

function ChipJa({ candidate, color, onPress }: { candidate: Candidate; color: string; onPress: () => void }) {
  const { theme } = useTheme();
  const [ko, setKo] = React.useState(false);
  return (
    <Pressable
      onPress={onPress}
      onLongPress={() => setKo((v) => !v)}
      accessibilityRole="button"
      style={{ backgroundColor: theme.colors.chip, borderColor: color, borderWidth: 1, borderRadius: 14, paddingHorizontal: 12, paddingVertical: 8, marginRight: 8, marginBottom: 8 }}
    >
      <FuriganaTokens tokens={[{ b: candidate.text }]} size={17} color={theme.colors.text} />
      {ko && candidate.ko ? <Text style={{ fontSize: 12, color: theme.colors.subtext, marginTop: 2 }}>{candidate.ko}</Text> : null}
    </Pressable>
  );
}
