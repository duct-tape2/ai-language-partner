import React, { useState } from 'react';
import { Image, Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { STRINGS } from '../i18n';
import { personaColor } from '../personaStyle';
import { Button, Card, Fade, Muted, Title } from '../components';
import { Mascot } from '../characters/Mascot';
import type { AppController } from '../store';

export function OnboardingScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const [step, setStep] = useState(0);
  const [personaId, setPersonaId] = useState(app.selectedPersonaId);
  const [level, setLevel] = useState(0);
  const [goal, setGoal] = useState(5);

  const next = () => setStep((s) => s + 1);
  const dot = (i: number) => (
    <View
      key={i}
      style={{ width: 8, height: 8, borderRadius: 999, marginHorizontal: 4, backgroundColor: i === step ? theme.colors.accent : theme.colors.track }}
    />
  );

  return (
    <View style={{ flex: 1, justifyContent: 'center' }}>
      <View style={{ flexDirection: 'row', justifyContent: 'center', marginBottom: 18 }}>{[0, 1, 2, 3].map(dot)}</View>

      {step === 0 && (
        <Fade>
          <View style={{ alignItems: 'center', marginBottom: 8 }}>
            <Image source={require('../../assets/shirokuma_hero.png')} style={{ width: 300, height: 300, resizeMode: 'contain' }} />
          </View>
          <Title>{STRINGS.onboarding.welcome}</Title>
          <Muted>{STRINGS.onboarding.welcomeSub}</Muted>
          {app.demoMode && (
            <View style={{ marginTop: 12, padding: 12, borderRadius: 12, backgroundColor: theme.colors.chip }}>
              <Text style={{ fontSize: 13, color: theme.colors.subtext, lineHeight: 19 }}>ℹ️ {STRINGS.onboarding.demoNotice}</Text>
            </View>
          )}
          <View style={{ height: 16 }} />
          <Button title={STRINGS.onboarding.next} onPress={next} />
        </Fade>
      )}

      {step === 1 && (
        <Fade>
          <Title>{STRINGS.onboarding.pickPartner}</Title>
          {app.personas.map((p) => {
            const sel = personaId === p.id;
            const color = personaColor(p.id);
            return (
              <Card key={p.id} style={{ borderColor: sel ? color : theme.colors.border, borderWidth: sel ? 2 : 1 }}>
                <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <Mascot personaId={p.id} size={58} expression={sel ? 'happy' : 'idle'} />
                    <View style={{ marginLeft: 6 }}>
                      <Text style={{ fontSize: 18, fontWeight: '800', color: theme.colors.text }}>{p.displayName}</Text>
                      <Text style={{ fontSize: 13, color }}>{p.role}</Text>
                    </View>
                  </View>
                  <Button title={sel ? '선택됨' : '선택'} onPress={() => setPersonaId(p.id)} color={color} secondary={sel} />
                </View>
              </Card>
            );
          })}
          <Button title={STRINGS.onboarding.next} onPress={next} />
        </Fade>
      )}

      {step === 2 && (
        <Fade>
          <Title>{STRINGS.onboarding.levelTitle}</Title>
          {STRINGS.onboarding.levels.map((l, i) => (
            <Card key={i} style={{ borderColor: level === i ? theme.colors.accent : theme.colors.border, borderWidth: level === i ? 2 : 1 }}>
              <Button title={l} onPress={() => setLevel(i)} secondary={level !== i} />
            </Card>
          ))}
          <Button title={STRINGS.onboarding.next} onPress={next} />
        </Fade>
      )}

      {step === 3 && (
        <Fade>
          <Title>{STRINGS.onboarding.goalTitle}</Title>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            {[3, 5, 10].map((g) => (
              <View key={g} style={{ flex: 1, marginHorizontal: 4 }}>
                <Button title={`${g}문장`} onPress={() => setGoal(g)} secondary={goal !== g} />
              </View>
            ))}
          </View>
          <View style={{ height: 16 }} />
          {app.demoMode && (
            <Text style={{ fontSize: 12, color: theme.colors.subtext, textAlign: 'center', marginBottom: 10, lineHeight: 18 }}>
              현재 데모 모드에서는 음성 인식·교정 결과가 예시로 제공됩니다.
            </Text>
          )}
          <Button title={STRINGS.onboarding.start} onPress={() => app.completeOnboarding({ personaId, level, dailyGoal: goal })} color={personaColor(personaId)} />
        </Fade>
      )}
    </View>
  );
}
