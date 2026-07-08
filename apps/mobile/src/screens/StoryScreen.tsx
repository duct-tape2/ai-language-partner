import React from 'react';
import { Pressable, Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Button, Card, Fade, Furigana, Muted, Pill, Title } from '../components';
import { Mascot } from '../characters/Mascot';
import type { AppController } from '../store';

// Mini Story: understand a short dialogue in context, then answer a comprehension
// question. Mirrors Codex's /practice-hub/stories shape (lines/choices/summaryKo).
export function StoryScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const story = app.currentStory;
  const color = personaColor(app.selectedPersonaId);
  const name = app.persona?.displayName ?? '유이';
  if (!story) {
    return (
      <View>
        <Title>미니 스토리</Title>
        <Muted>지금은 볼 수 있는 이야기가 없어요.</Muted>
        <Button title="홈으로" onPress={() => app.navigate('home')} secondary />
      </View>
    );
  }
  const answered = app.storyChoiceId != null;
  const correct = answered && app.storyChoiceId === story.correctChoiceId;
  const isLast = app.storyIndex >= app.storyTotal - 1;

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>미니 스토리</Title>
          <Pill label={`${app.storyIndex + 1}/${app.storyTotal}`} />
        </View>
        <Muted>{story.contextNote}</Muted>
      </Fade>

      {/* dialogue */}
      <Fade delay={60}>
        <Card>
          {story.lines.map((line, i) => {
            const mine = line.speaker === 'Learner';
            return (
              <View
                key={i}
                style={{
                  flexDirection: 'row',
                  justifyContent: mine ? 'flex-end' : 'flex-start',
                  marginVertical: 6,
                }}
              >
                {!mine && <Mascot personaId={app.selectedPersonaId} size={40} expression="idle" />}
                <View
                  style={{
                    maxWidth: '78%',
                    marginLeft: mine ? 0 : 8,
                    backgroundColor: mine ? color : theme.colors.chip,
                    borderRadius: 16,
                    paddingVertical: 8,
                    paddingHorizontal: 12,
                  }}
                >
                  <Text style={{ fontSize: 11, color: mine ? '#fff' : theme.colors.subtext, marginBottom: 2 }}>
                    {mine ? '나' : name}
                  </Text>
                  <Text style={{ fontSize: 18, fontWeight: '700', color: mine ? '#fff' : theme.colors.text }}>{line.text}</Text>
                  <Text style={{ fontSize: 13, color: mine ? '#ffffffcc' : theme.colors.subtext, marginTop: 2 }}>{line.reading}</Text>
                </View>
              </View>
            );
          })}
        </Card>
      </Fade>

      {/* question + choices */}
      <Fade delay={120}>
        <Card>
          <Muted>이해 확인</Muted>
          <Text style={{ fontSize: 17, fontWeight: '800', color: theme.colors.text, marginVertical: 8 }}>{story.promptKo}</Text>
          {story.choices.map((c) => {
            const chosen = app.storyChoiceId === c.id;
            const showCorrect = answered && c.id === story.correctChoiceId;
            const showWrong = answered && chosen && !correct;
            const bg = showCorrect ? theme.colors.good + '22' : showWrong ? theme.colors.bad + '22' : theme.colors.card;
            const bd = showCorrect ? theme.colors.good : showWrong ? theme.colors.bad : theme.colors.border;
            return (
              <Pressable
                key={c.id}
                onPress={() => app.answerStory(c.id)}
                disabled={answered}
                accessibilityRole="button"
                style={{
                  borderWidth: 1.5,
                  borderColor: bd,
                  backgroundColor: bg,
                  borderRadius: 12,
                  paddingVertical: 13,
                  paddingHorizontal: 14,
                  marginTop: 8,
                  flexDirection: 'row',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <Text style={{ fontSize: 16, color: theme.colors.text, fontWeight: chosen || showCorrect ? '800' : '500' }}>{c.label}</Text>
                {showCorrect ? <Text style={{ color: theme.colors.good, fontWeight: '900' }}>✓</Text> : showWrong ? <Text style={{ color: theme.colors.bad, fontWeight: '900' }}>✕</Text> : null}
              </Pressable>
            );
          })}
        </Card>
      </Fade>

      {/* reveal: summary + xp */}
      {answered && (
        <Fade delay={80}>
          <Card style={{ borderColor: correct ? theme.colors.good : color, borderWidth: 1.5 }}>
            <Text style={{ fontSize: 16, fontWeight: '800', color: correct ? theme.colors.good : theme.colors.accentDark }}>
              {correct ? `정답! +${story.xpReward} XP` : '아쉬워요 — 다시 볼까요'}
            </Text>
            <Text style={{ fontSize: 15, color: theme.colors.text, lineHeight: 22, marginTop: 6 }}>{story.summaryKo}</Text>
          </Card>
        </Fade>
      )}

      <Fade delay={140}>
        {answered ? (
          <Button title={isLast ? '학습 마치기 🎉' : '다음 이야기 →'} onPress={app.nextStory} color={color} />
        ) : (
          <Button title="정답 고르기" onPress={() => {}} color={color} disabled />
        )}
        <Button title="홈으로" onPress={() => app.navigate('home')} secondary />
      </Fade>
    </View>
  );
}
