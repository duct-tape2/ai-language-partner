import React, { useEffect, useState } from 'react';
import { Pressable, Text, TextInput, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Button, Card, DiffText, Fade, Furigana, Muted, Pill, Segmented, Title } from '../components';
import { Icon } from '../icons';
import { STRINGS } from '../i18n';
import { dictationMatch, diffChars, kataToHira, stripForDictation } from '../text';
import type { AppController } from '../store';

type ListenMode = 'pick' | 'type';

// Listening: hear the sentence (TTS), then either pick the Korean meaning
// (고르기) or type what was heard (받아쓰기). The JP text stays hidden until
// after answering (it's a listening test), then revealed with furigana.
export function ListeningScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const item = app.currentListening;
  const color = personaColor(app.selectedPersonaId);
  const [mode, setMode] = useState<ListenMode>('pick');
  const [typed, setTyped] = useState('');

  useEffect(() => {
    setTyped('');
  }, [app.listeningIndex]);

  if (!item) {
    return (
      <View>
        <Title>듣기 연습</Title>
        <Muted>지금은 들을 문장이 없어요.</Muted>
        <Button title="연습 허브로" onPress={() => app.navigate('hub')} secondary />
      </View>
    );
  }
  const answered = app.listeningChoiceId != null;
  const correct = answered && app.listeningChoiceId === item.correctChoiceId;
  const isLast = app.listeningIndex >= app.listeningTotal - 1;
  const typedDiff = answered && mode === 'type' && !correct && stripForDictation(typed).length > 0
    ? diffChars(item.reading, kataToHira(typed))
    : null;

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>듣기 연습</Title>
          <Pill label={`${app.listeningIndex + 1}/${app.listeningTotal}`} />
        </View>
        <Muted>{mode === 'pick' ? STRINGS.listening.pickHint : STRINGS.listening.dictationHint}</Muted>
        <View style={{ marginTop: 8 }}>
          <Segmented<ListenMode>
            options={[
              { value: 'pick', label: STRINGS.listening.modePick },
              { value: 'type', label: STRINGS.listening.modeDictation },
            ]}
            value={mode}
            onChange={setMode}
          />
        </View>
      </Fade>

      <Fade delay={60}>
        <Card style={{ alignItems: 'center' }}>
          <Pressable
            onPress={() => app.speak(item.ja)}
            accessibilityRole="button"
            style={{ width: 96, height: 96, borderRadius: 48, backgroundColor: color, alignItems: 'center', justifyContent: 'center' }}
          >
            <Icon name="speaker" size={40} color={'#fff'} />
          </Pressable>
          <Text style={{ marginTop: 10, color: theme.colors.subtext }}>탭해서 다시 듣기</Text>
        </Card>
      </Fade>

      {mode === 'pick' ? (
        <Fade delay={120}>
          <Card>
            <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text, marginBottom: 4 }}>{item.promptKo}</Text>
            {item.choices.map((c) => {
              const chosen = app.listeningChoiceId === c.id;
              const showCorrect = answered && c.id === item.correctChoiceId;
              const showWrong = answered && chosen && !correct;
              const bg = showCorrect ? theme.colors.good + '22' : showWrong ? theme.colors.bad + '22' : theme.colors.card;
              const bd = showCorrect ? theme.colors.good : showWrong ? theme.colors.bad : theme.colors.border;
              return (
                <Pressable
                  key={c.id}
                  onPress={() => app.answerListening(c.id)}
                  disabled={answered}
                  accessibilityRole="button"
                  style={{ borderWidth: 1.5, borderColor: bd, backgroundColor: bg, borderRadius: 12, paddingVertical: 13, paddingHorizontal: 14, marginTop: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}
                >
                  <Text style={{ fontSize: 16, color: theme.colors.text, fontWeight: chosen || showCorrect ? '800' : '500' }}>{c.label}</Text>
                  {showCorrect ? <Text style={{ color: theme.colors.good, fontWeight: '900' }}>✓</Text> : showWrong ? <Text style={{ color: theme.colors.bad, fontWeight: '900' }}>✕</Text> : null}
                </Pressable>
              );
            })}
          </Card>
        </Fade>
      ) : (
        <Fade delay={120}>
          <Card>
            <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text, marginBottom: 4 }}>들은 문장을 입력하세요</Text>
            <TextInput
              value={typed}
              onChangeText={setTyped}
              editable={!answered}
              autoCapitalize="none"
              autoCorrect={false}
              placeholder={STRINGS.listening.dictationPlaceholder}
              placeholderTextColor={theme.colors.subtext}
              accessibilityLabel="받아쓰기 입력"
              style={{
                borderWidth: 1.5,
                borderColor: answered ? (correct ? theme.colors.good : theme.colors.bad) : theme.colors.border,
                borderRadius: 12,
                paddingVertical: 12,
                paddingHorizontal: 14,
                fontSize: 18,
                color: theme.colors.text,
                backgroundColor: theme.colors.card,
                marginTop: 4,
              }}
            />
          </Card>
        </Fade>
      )}

      {answered && (
        <Fade delay={80}>
          <Card style={{ borderColor: correct ? theme.colors.good : color, borderWidth: 1.5 }}>
            <Text style={{ fontSize: 16, fontWeight: '800', color: correct ? theme.colors.good : theme.colors.accentDark }}>
              {correct
                ? mode === 'type' ? STRINGS.listening.dictationCorrect(item.xpReward) : `정답! +${item.xpReward} XP`
                : mode === 'type' ? STRINGS.listening.dictationWrong : '아쉬워요 — 뜻을 확인하세요'}
            </Text>
            <View style={{ marginTop: 8 }}>
              <Furigana phrase={item.ja} size={24} color={color} />
            </View>
            <Muted>{item.reading}</Muted>
            {typedDiff && (
              <View style={{ marginTop: 8 }}>
                <Muted>{STRINGS.listening.dictationYours}</Muted>
                <DiffText segs={typedDiff} size={20} />
              </View>
            )}
            <Text style={{ fontSize: 14, color: theme.colors.text, lineHeight: 21, marginTop: 6 }}>{item.noteKo}</Text>
          </Card>
        </Fade>
      )}

      <Fade delay={140}>
        {answered ? (
          <Button title={isLast ? '학습 마치기' : '다음 문제 →'} onPress={app.nextListening} color={color} />
        ) : mode === 'pick' ? (
          <Button title="뜻 고르기" onPress={() => {}} color={color} disabled />
        ) : (
          <Button
            title={STRINGS.listening.dictationCheck}
            onPress={() => app.answerListeningDictation(dictationMatch(typed, item.ja, item.reading))}
            color={color}
            disabled={stripForDictation(typed).length === 0}
          />
        )}
        <Button title="연습 허브로" onPress={() => app.navigate('hub')} secondary />
      </Fade>
    </View>
  );
}
