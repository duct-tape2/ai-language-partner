import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Animated, Pressable, Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Button, Card, Fade, Furigana, Muted, Pill, Title } from '../components';
import { findFurigana, STRINGS } from '../i18n';
import { shuffledChips } from '../wordBankItems';
import type { AppController } from '../store';

// Word bank (문장 조립): the Korean meaning + TTS play the sentence; the learner
// taps shuffled chips to rebuild it. Wrong order shakes/marks red and stays
// retryable; only the correct order awards XP and advances (store owns that).
export function WordBankScreen({ app }: { app: AppController }) {
  const { theme, reducedMotion } = useTheme();
  const item = app.currentWordBank;
  const color = personaColor(app.selectedPersonaId);
  const [picked, setPicked] = useState<number[]>([]);
  const [wrong, setWrong] = useState(false);
  const shake = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    setPicked([]);
    setWrong(false);
  }, [app.wordBankIndex]);

  const shuffled = useMemo(() => (item ? shuffledChips(item) : []), [item]);

  if (!item) {
    return (
      <View>
        <Title>{STRINGS.wordBank.title}</Title>
        <Muted>{STRINGS.wordBank.empty}</Muted>
        <Button title="연습 허브로" onPress={() => app.navigate('hub')} secondary />
      </View>
    );
  }

  const solved = app.wordBankSolved;
  const isLast = app.wordBankIndex >= app.wordBankTotal - 1;
  const allUsed = picked.length === shuffled.length;
  const furi = findFurigana(item.ja);

  const runShake = () => {
    if (reducedMotion) return;
    shake.setValue(0);
    Animated.sequence([
      Animated.timing(shake, { toValue: 1, duration: 60, useNativeDriver: true }),
      Animated.timing(shake, { toValue: -1, duration: 60, useNativeDriver: true }),
      Animated.timing(shake, { toValue: 1, duration: 60, useNativeDriver: true }),
      Animated.timing(shake, { toValue: 0, duration: 60, useNativeDriver: true }),
    ]).start();
  };
  const translateX = shake.interpolate({ inputRange: [-1, 1], outputRange: [-8, 8] });

  const pick = (i: number) => {
    if (solved || picked.includes(i)) return;
    setWrong(false);
    setPicked((p) => [...p, i]);
  };
  const unpick = (i: number) => {
    if (solved) return;
    setWrong(false);
    setPicked((p) => p.filter((x) => x !== i));
  };
  const check = () => {
    const ok = app.checkWordBank(picked.map((i) => shuffled[i]).join(''));
    if (!ok) {
      setWrong(true);
      runShake();
    }
  };

  const slotBorder = wrong ? theme.colors.bad : solved ? theme.colors.good : theme.colors.border;

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>{STRINGS.wordBank.title}</Title>
          <Pill label={`${app.wordBankIndex + 1}/${app.wordBankTotal}`} />
        </View>
        <Muted>{STRINGS.wordBank.subtitle}</Muted>
      </Fade>

      <Fade delay={60}>
        <Card style={{ alignItems: 'center' }}>
          <Muted>{STRINGS.wordBank.prompt}</Muted>
          <Text style={{ fontSize: 22, fontWeight: '900', color: theme.colors.text, marginTop: 6, textAlign: 'center' }}>{item.ko}</Text>
          <View style={{ marginTop: 6 }}>
            <Button title={STRINGS.wordBank.listen} onPress={() => app.speak(item.ja)} secondary color={color} />
          </View>
        </Card>
      </Fade>

      <Fade delay={120}>
        <Animated.View style={{ transform: [{ translateX }] }}>
          <Card style={{ borderColor: slotBorder, borderWidth: 1.5, minHeight: 76 }}>
            {picked.length === 0 ? (
              <Muted>{STRINGS.wordBank.emptySlot}</Muted>
            ) : (
              <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
                {picked.map((i) => (
                  <Pressable
                    key={i}
                    onPress={() => unpick(i)}
                    disabled={solved}
                    accessibilityRole="button"
                    accessibilityLabel={`${shuffled[i]} 빼기`}
                    style={{
                      borderWidth: 1.5,
                      borderColor: wrong ? theme.colors.bad : solved ? theme.colors.good : color,
                      backgroundColor: theme.colors.card,
                      borderRadius: 12,
                      paddingVertical: 8,
                      paddingHorizontal: 12,
                      marginRight: 6,
                      marginBottom: 6,
                    }}
                  >
                    <Text style={{ fontSize: 20, fontWeight: '800', color: wrong ? theme.colors.bad : theme.colors.text }}>{shuffled[i]}</Text>
                  </Pressable>
                ))}
              </View>
            )}
            {wrong ? <Text style={{ color: theme.colors.bad, fontWeight: '800', marginTop: 6 }}>{STRINGS.wordBank.wrong}</Text> : null}
          </Card>
        </Animated.View>
      </Fade>

      {!solved && (
        <Fade delay={160}>
          <Card>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
              {shuffled.map((chip, i) => {
                const used = picked.includes(i);
                return (
                  <Pressable
                    key={i}
                    onPress={() => pick(i)}
                    disabled={used}
                    accessibilityRole="button"
                    accessibilityLabel={chip}
                    accessibilityState={{ disabled: used }}
                    style={{
                      borderWidth: 1.5,
                      borderColor: theme.colors.border,
                      backgroundColor: theme.colors.chip,
                      borderRadius: 12,
                      paddingVertical: 10,
                      paddingHorizontal: 14,
                      marginRight: 8,
                      marginBottom: 8,
                      opacity: used ? 0.25 : 1,
                    }}
                  >
                    <Text style={{ fontSize: 20, fontWeight: '800', color: theme.colors.text }}>{chip}</Text>
                  </Pressable>
                );
              })}
            </View>
          </Card>
        </Fade>
      )}

      {solved && (
        <Fade delay={80}>
          <Card style={{ borderColor: theme.colors.good, borderWidth: 1.5 }}>
            <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.good }}>{STRINGS.wordBank.correct(item.xpReward)}</Text>
            <View style={{ marginTop: 8 }}>
              {furi ? (
                <Furigana phrase={item.ja} size={24} color={color} />
              ) : (
                <Text style={{ fontSize: 24, fontWeight: '900', color: color }}>{item.ja}</Text>
              )}
            </View>
            {item.reading ? <Muted>{item.reading}</Muted> : null}
          </Card>
        </Fade>
      )}

      <Fade delay={200}>
        {solved ? (
          <Button title={isLast ? STRINGS.wordBank.finish : STRINGS.wordBank.next} onPress={app.nextWordBank} color={color} />
        ) : (
          <>
            <Button title={STRINGS.wordBank.check} onPress={check} color={color} disabled={!allUsed} />
            {picked.length > 0 && <Button title={STRINGS.wordBank.reset} onPress={() => { setPicked([]); setWrong(false); }} secondary color={color} />}
          </>
        )}
        <Button title="연습 허브로" onPress={() => app.navigate('hub')} secondary />
      </Fade>
    </View>
  );
}
