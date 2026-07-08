import React from 'react';
import { Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Button, Card, Fade, Furigana, Muted, Pill, Title } from '../components';
import { Icon } from '../icons';
import type { AppController } from '../store';

// Words: active recall. See the Korean meaning, recall the Japanese word, reveal,
// then self-grade (알았어요 / 아직). Reinforces the daily-loop vocabulary.
export function WordScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const w = app.currentWord;
  const color = personaColor(app.selectedPersonaId);
  if (!w) {
    return (
      <View>
        <Title>단어 복습</Title>
        <Muted>복습할 단어가 없어요.</Muted>
        <Button title="연습 허브로" onPress={() => app.navigate('hub')} secondary />
      </View>
    );
  }
  const revealed = app.wordRevealed;

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>단어 복습</Title>
          <Pill label={`${app.wordIndex + 1}/${app.wordTotal}`} />
        </View>
        <Muted>뜻을 보고 일본어를 떠올려보세요</Muted>
      </Fade>

      <Fade delay={60}>
        <Card style={{ alignItems: 'center', paddingVertical: 28 }}>
          <Muted>이 뜻의 일본어는?</Muted>
          <Text style={{ fontSize: 30, fontWeight: '900', color: theme.colors.text, marginTop: 8, textAlign: 'center' }}>{w.ko}</Text>

          {revealed ? (
            <View style={{ alignItems: 'center', marginTop: 18 }}>
              <Furigana phrase={w.ja} size={30} color={color} />
              <Text style={{ fontSize: 15, color: theme.colors.subtext, marginTop: 6 }}>{w.reading}</Text>
              <View style={{ height: 1, backgroundColor: theme.colors.border, alignSelf: 'stretch', marginVertical: 14 }} />
              <View style={{ marginBottom: 2 }}>
                <Furigana phrase={w.example} size={18} color={theme.colors.text} />
              </View>
              <Muted>{w.exampleKo}</Muted>
              <View style={{ marginTop: 6 }}>
                <Button icon="speaker" title="발음 듣기" onPress={() => app.speak(w.example)} secondary color={color} />
              </View>
            </View>
          ) : (
            <View style={{ marginTop: 18 }}>
              <Icon name="bulb" size={40} color={theme.colors.gold} />
            </View>
          )}
        </Card>
      </Fade>

      <Fade delay={120}>
        {revealed ? (
          <>
            <Button title={`알았어요 +${w.xpReward}`} onPress={() => app.gradeWord(true)} color={color} />
            <Button title="아직 (다시)" onPress={() => app.gradeWord(false)} secondary color={color} />
          </>
        ) : (
          <Button title="정답 확인" onPress={app.revealWord} color={color} />
        )}
        <Button title="연습 허브로" onPress={() => app.navigate('hub')} secondary />
      </Fade>
    </View>
  );
}
