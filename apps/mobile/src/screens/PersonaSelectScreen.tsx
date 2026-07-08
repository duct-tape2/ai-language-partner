import React from 'react';
import { Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { STRINGS } from '../i18n';
import { personaColor } from '../personaStyle';
import { Button, Card, Fade, Muted, Title } from '../components';
import { Mascot } from '../characters/Mascot';
import type { AppController } from '../store';

export function PersonaSelectScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  return (
    <View>
      <Fade>
        <Title>{STRINGS.persona.title}</Title>
        <Muted>{STRINGS.persona.subtitle}</Muted>
      </Fade>

      {app.personas.map((p, i) => {
        const selected = app.selectedPersonaId === p.id;
        const color = personaColor(p.id);
        return (
          <Fade key={p.id} delay={60 + i * 60}>
            <Card style={{ borderColor: selected ? color : theme.colors.border, borderWidth: selected ? 2 : 1 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <Mascot personaId={p.id} size={92} expression={selected ? 'cheer' : 'idle'} outfit="scarf" />
                <View style={{ marginLeft: 12, flex: 1 }}>
                  <Text style={{ fontSize: 21, fontWeight: '800', color: theme.colors.text }}>
                    {p.displayName} <Text style={{ fontSize: 14, color: theme.colors.subtext }}>{p.japaneseName}</Text>
                  </Text>
                  <Text style={{ fontSize: 13, color, fontWeight: '700' }}>{p.role}</Text>
                </View>
              </View>
              <Muted>{STRINGS.persona.voice} · {p.voiceStyle}</Muted>
              <Muted>{STRINGS.persona.style} · {p.teachingStyle}</Muted>
              <View style={{ flexDirection: 'row', marginTop: 6 }}>
                <View style={{ flex: 1, marginRight: 6 }}>
                  <Button icon="speaker" title="목소리 듣기" onPress={() => { app.selectPersona(p.id); app.speak('はじめまして、' + (p.japaneseName ?? '') + 'だよ'); }} secondary color={color} />
                </View>
                <View style={{ flex: 1, marginLeft: 6 }}>
                  <Button title={selected ? STRINGS.persona.selected : STRINGS.persona.select} onPress={() => app.selectPersona(p.id)} color={color} secondary={selected} />
                </View>
              </View>
            </Card>
          </Fade>
        );
      })}
    </View>
  );
}
