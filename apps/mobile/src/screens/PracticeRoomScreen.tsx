import React from 'react';
import { Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { STRINGS } from '../i18n';
import { personaColor } from '../personaStyle';
import { personaCoaching } from '../coaching';
import { Button, Card, Fade, Furigana, Muted, PitchAccent, Pill, Row, Title } from '../components';
import { Mascot } from '../characters/Mascot';
import type { AppController } from '../store';

export function PracticeRoomScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const { room, persona } = app;
  const color = personaColor(app.selectedPersonaId);
  const phrase = room?.primaryPhraseJa ?? '今日めっちゃ疲れた';
  const opening = personaCoaching(app.selectedPersonaId).opening;

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <Mascot personaId={app.selectedPersonaId} size={78} speaking={app.speaking} />
          <View style={{ flex: 1, marginLeft: 8 }}>
            <Muted>{persona?.displayName ?? '유이'} · {persona?.role ?? '다정한 일본인 친구'}</Muted>
            <Title>{room?.title ?? '오늘 너무 피곤했어'}</Title>
          </View>
        </View>
      </Fade>

      <Fade delay={60}>
        <Card>
          <Muted>{STRINGS.practice.korean}</Muted>
          <Text style={{ fontSize: 24, fontWeight: '700', color: theme.colors.text, marginVertical: 6 }}>{room?.primaryPhraseKo ?? '오늘 너무 피곤했어'}</Text>
          <Muted>{STRINGS.practice.japanese}</Muted>
          <View style={{ marginVertical: 6 }}>
            <Furigana phrase={phrase} size={30} />
          </View>
          <PitchAccent phrase={phrase} />
          <Muted>{STRINGS.practice.alternatives}</Muted>
          <Row>{(room?.alternativePhrasesJa ?? ['今日はすごく疲れた', '今日ちょっとしんどい']).map((a) => <Pill key={a} label={a} />)}</Row>
        </Card>
      </Fade>

      <Fade delay={120}>
        <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
          <Muted>{STRINGS.practice.aWord(persona?.displayName ?? '유이')}</Muted>
          <Text style={{ fontSize: 16, lineHeight: 24, color: theme.colors.text, marginTop: 4 }}>{opening}</Text>
        </Card>
      </Fade>

      <Fade delay={160}>
        <Button title={STRINGS.practice.listen} onPress={() => app.speak(phrase)} secondary color={color} />
        <Button title={app.demoMode ? STRINGS.practice.startDemo : STRINGS.practice.shadow} onPress={app.submitTurn} color={color} />
      </Fade>
    </View>
  );
}
