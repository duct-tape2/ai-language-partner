import React from 'react';
import { Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Button, Card, Fade, Furigana, Muted, Pill, Title } from '../components';
import { Icon } from '../icons';
import { Mascot } from '../characters/Mascot';
import type { AppController } from '../store';

// Roleplay: a situation + the partner's line. The learner plans a reply, reveals a
// natural one, and practices saying it. Speaking-in-context, guided.
export function RoleplayScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const item = app.currentRoleplay;
  const color = personaColor(app.selectedPersonaId);
  const name = app.persona?.displayName ?? '유이';
  if (!item) {
    return (
      <View>
        <Title>롤플레이</Title>
        <Muted>지금은 상황이 없어요.</Muted>
        <Button title="연습 허브로" onPress={() => app.navigate('hub')} secondary />
      </View>
    );
  }
  const revealed = app.roleplayRevealed;
  const isLast = app.roleplayIndex >= app.roleplayTotal - 1;

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>롤플레이</Title>
          <Pill label={`${app.roleplayIndex + 1}/${app.roleplayTotal}`} />
        </View>
        <Muted>{item.title}</Muted>
      </Fade>

      <Fade delay={60}>
        <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
          <Text style={{ fontSize: 15, color: theme.colors.text, marginBottom: 10 }}>🎬 {item.situationKo}</Text>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Mascot personaId={app.selectedPersonaId} size={56} expression="talking" />
            <View style={{ flex: 1, marginLeft: 8, backgroundColor: theme.colors.chip, borderRadius: 14, padding: 12 }}>
              <Text style={{ fontSize: 12, color: theme.colors.subtext, marginBottom: 2 }}>{name}</Text>
              <Furigana phrase={item.partnerJa} size={22} color={theme.colors.text} />
            </View>
          </View>
          <View style={{ marginTop: 8, alignSelf: 'flex-start' }}>
            <Button icon="speaker" title="다시 듣기" onPress={() => app.speak(item.partnerJa)} secondary color={color} />
          </View>
        </Card>
      </Fade>

      <Fade delay={120}>
        <Card style={{ borderColor: color, borderWidth: 1.5 }}>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Icon name="target" size={14} color={theme.colors.subtext} />
            <View style={{ marginLeft: 6 }}><Muted>목표</Muted></View>
          </View>
          <Text style={{ fontSize: 16, fontWeight: '700', color: theme.colors.text, marginTop: 2 }}>{item.goalKo}</Text>
          {revealed && (
            <View style={{ marginTop: 14 }}>
              <Muted>이렇게 답해보세요</Muted>
              <View style={{ marginTop: 6 }}>
                <Furigana phrase={item.replyJa} size={26} color={color} />
              </View>
              <Text style={{ fontSize: 14, color: theme.colors.subtext, marginTop: 4 }}>{item.replyReading}</Text>
              <Text style={{ fontSize: 15, color: theme.colors.text, marginTop: 2 }}>{item.replyKo}</Text>
              <View style={{ marginTop: 8, alignSelf: 'flex-start' }}>
                <Button icon="speaker" title="따라 말하기" onPress={() => app.speak(item.replyJa)} secondary color={color} />
              </View>
            </View>
          )}
        </Card>
      </Fade>

      <Fade delay={160}>
        {revealed ? (
          <Button title={isLast ? `학습 마치기 +${item.xpReward}` : `다음 상황 → +${item.xpReward}`} onPress={app.nextRoleplay} color={color} />
        ) : (
          <Button title="답 보기" onPress={app.revealRoleplay} color={color} />
        )}
        <Button title="연습 허브로" onPress={() => app.navigate('hub')} secondary />
      </Fade>
    </View>
  );
}
