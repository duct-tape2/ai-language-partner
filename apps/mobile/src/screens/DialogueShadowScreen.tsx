import React from 'react';
import { Text, View, Pressable } from 'react-native';
import * as Speech from 'expo-speech';
import { useTheme } from '../ThemeContext';
import { personaColor, personaVoice } from '../personaStyle';
import { Button, Card, Fade, FuriganaTokens, Muted, Pill, Row, Title } from '../components';
import { Icon } from '../icons';
import type { AppController } from '../store';
import { DIALOGUES, DIALOGUE_TOTAL, type Dialogue, type ShadowLine } from '../shadowing/shadowingData';

// 회화 섀도잉: 짧은 일상 대화를 듣고 따라 말하는 스피킹 반복 연습.
// 목록에서 대화를 열면 A/B 말풍선으로 대사를 보여주고, 각 줄을 탭하면 발음,
// '전체 재생'으로 순차 재생, 한국어 표시를 켜고 끌 수 있다.

const UI = {
  title: '회화 섀도잉',
  intro: '짧은 일상 대화를 듣고 따라 말해 보세요.',
  pickHint: '대화를 골라 시작하세요',
  playAll: '전체 재생',
  stop: '정지',
  showKo: '한국어 표시',
  hideKo: '한국어 숨기기',
  back: '목록으로',
  home: '홈으로',
  tapHint: '말풍선을 탭하면 한 줄씩 들을 수 있어요.',
};

function LineBubble({
  line,
  showKo,
  active,
  onPress,
}: {
  line: ShadowLine;
  showKo: boolean;
  active: boolean;
  onPress: () => void;
}) {
  const { theme } = useTheme();
  const isA = line.speaker === 'A';
  const bubbleBg = isA ? theme.colors.card : theme.colors.accentSoft;
  const borderCol = active ? theme.colors.accent : theme.colors.border;
  return (
    <Pressable onPress={onPress} accessibilityRole="button" accessibilityLabel={line.ja}>
      <View
        style={{
          flexDirection: 'row',
          justifyContent: isA ? 'flex-start' : 'flex-end',
          marginBottom: 10,
        }}
      >
        <View
          style={{
            maxWidth: '86%',
            backgroundColor: bubbleBg,
            borderColor: borderCol,
            borderWidth: active ? 2 : 1,
            borderRadius: 16,
            borderTopLeftRadius: isA ? 4 : 16,
            borderTopRightRadius: isA ? 16 : 4,
            paddingVertical: 12,
            paddingHorizontal: 14,
          }}
        >
          <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 6 }}>
            <View
              style={{
                width: 22,
                height: 22,
                borderRadius: 11,
                backgroundColor: isA ? theme.colors.accentDark : theme.colors.accent,
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: 6,
              }}
            >
              <Text style={{ color: '#fff', fontSize: 12, fontWeight: '900' }}>{line.speaker}</Text>
            </View>
            <Icon name="speaker" size={12} color={theme.colors.subtext} />
            <Text style={{ fontSize: 12, color: theme.colors.subtext, marginLeft: 4 }}>탭</Text>
          </View>
          <FuriganaTokens tokens={line.tokens} size={20} color={theme.colors.text} />
          {showKo ? (
            <Text style={{ fontSize: 14, color: theme.colors.subtext, marginTop: 8, lineHeight: 20 }}>
              {line.ko}
            </Text>
          ) : null}
        </View>
      </View>
    </Pressable>
  );
}

function DialogueDetail({
  app,
  dialogue,
  onBack,
}: {
  app: AppController;
  dialogue: Dialogue;
  onBack: () => void;
}) {
  const { theme } = useTheme();
  const color = personaColor(app.selectedPersonaId);
  const [showKo, setShowKo] = React.useState(true);
  const [playing, setPlaying] = React.useState(false);
  const [activeIdx, setActiveIdx] = React.useState(-1);
  const runId = React.useRef(0);

  React.useEffect(() => {
    return () => {
      runId.current++;
      Speech.stop();
    };
  }, []);

  const stopAll = () => {
    runId.current++;
    Speech.stop();
    setPlaying(false);
    setActiveIdx(-1);
  };

  const speakLine = (ja: string) => {
    runId.current++; // cancel any sequential run
    setPlaying(false);
    Speech.stop();
    app.speak(ja);
  };

  const playAll = () => {
    if (playing) {
      stopAll();
      return;
    }
    const v = personaVoice(app.selectedPersonaId);
    const myRun = ++runId.current;
    setPlaying(true);
    const speakAt = (i: number) => {
      if (myRun !== runId.current) return;
      if (i >= dialogue.lines.length) {
        setPlaying(false);
        setActiveIdx(-1);
        return;
      }
      setActiveIdx(i);
      Speech.speak(dialogue.lines[i].ja, {
        language: 'ja-JP',
        rate: v.rate,
        pitch: v.pitch,
        onDone: () => {
          if (myRun !== runId.current) return;
          speakAt(i + 1);
        },
        onStopped: () => {},
        onError: () => {
          if (myRun !== runId.current) return;
          speakAt(i + 1);
        },
      });
    };
    Speech.stop();
    speakAt(0);
  };

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>{dialogue.titleKo}</Title>
        </View>
        <Muted>🎬 {dialogue.situationKo}</Muted>
      </Fade>

      <Fade delay={40}>
        <Row>
          <Button title={playing ? UI.stop : UI.playAll} onPress={playAll} color={color} />
          <View style={{ width: 10 }} />
          <Button
            title={showKo ? UI.hideKo : UI.showKo}
            onPress={() => setShowKo((s) => !s)}
            secondary
            color={color}
          />
        </Row>
        <Text style={{ fontSize: 12, color: theme.colors.subtext, marginTop: 4, marginBottom: 10 }}>
          {UI.tapHint}
        </Text>
      </Fade>

      <Fade delay={80}>
        <View>
          {dialogue.lines.map((line, i) => (
            <LineBubble
              key={i}
              line={line}
              showKo={showKo}
              active={activeIdx === i}
              onPress={() => speakLine(line.ja)}
            />
          ))}
        </View>
      </Fade>

      <Fade delay={120}>
        <Button title={UI.back} onPress={onBack} secondary />
        <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
      </Fade>
    </View>
  );
}

export function DialogueShadowScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const color = personaColor(app.selectedPersonaId);
  const [openId, setOpenId] = React.useState<string | null>(null);

  const open = (d: Dialogue) => {
    setOpenId(d.id);
    app.track('shadowing_opened', { id: d.id });
  };

  const current = openId ? DIALOGUES.find((d) => d.id === openId) ?? null : null;

  if (current) {
    return <DialogueDetail app={app} dialogue={current} onBack={() => setOpenId(null)} />;
  }

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>{UI.title}</Title>
          <Pill label={`${DIALOGUE_TOTAL}개`} />
        </View>
        <Muted>{UI.intro}</Muted>
      </Fade>

      <View style={{ marginTop: 12 }}>
        {DIALOGUES.map((d, i) => (
          <Fade key={d.id} delay={40 + i * 24}>
            <Pressable onPress={() => open(d)} accessibilityRole="button" accessibilityLabel={d.titleKo}>
              <Card style={{ borderColor: theme.colors.border }}>
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                  <View
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: 12,
                      backgroundColor: theme.colors.accentSoft,
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginRight: 12,
                    }}
                  >
                    <Text style={{ fontSize: 18, fontWeight: '900', color }}>{i + 1}</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={{ fontSize: 17, fontWeight: '800', color: theme.colors.text }}>
                      {d.titleKo}
                    </Text>
                    <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 2 }}>
                      {d.situationKo}
                    </Text>
                  </View>
                  <Text style={{ fontSize: 13, color: theme.colors.subtext, marginLeft: 8 }}>
                    {d.lines.length}줄 ›
                  </Text>
                </View>
              </Card>
            </Pressable>
          </Fade>
        ))}
      </View>

      <Fade delay={40 + DIALOGUES.length * 24}>
        <Button title={UI.home} onPress={() => app.navigate('home')} secondary />
      </Fade>
    </View>
  );
}
