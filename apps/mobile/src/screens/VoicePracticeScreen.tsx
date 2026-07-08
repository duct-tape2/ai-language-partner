import React from 'react';
import { Pressable, Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { STRINGS } from '../i18n';
import { personaColor } from '../personaStyle';
import { personaCoaching } from '../coaching';
import { Button, Card, DiffText, Fade, Furigana, Muted, Pill, ProgressRing, Title } from '../components';
import { Icon } from '../icons';
import { correctionLabel } from '../labels';
import { Mascot, type Expression } from '../characters/Mascot';
import type { AppController } from '../store';

export function VoicePracticeScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const { persona, assistantText, spokenText, sttResult, sttStatus, sttWarning, sttNote, coachingNow, diff, accuracy, corrections } = app;
  const name = persona?.displayName ?? '유이';
  const color = personaColor(app.selectedPersonaId);
  const [done, setDone] = React.useState(false);
  const expr: Expression = app.speaking
    ? 'talking'
    : sttStatus === 'perfect'
      ? 'cheer'
      : sttStatus === 'fail'
        ? 'sad'
        : sttStatus === 'partial'
          ? 'correcting'
          : 'listening';
  const hasResult = sttStatus != null;
  const failed = sttStatus === 'fail';
  const isLast = app.phraseIndex >= app.practiceTotal - 1;
  const ringColor = sttStatus === 'perfect' ? theme.colors.good : sttStatus === 'partial' ? theme.colors.near : theme.colors.bad;

  // Completion moment: the payoff for finishing today's set. Mission is completed
  // once here (not on Save, not mid-loop) — then the user chooses to view growth.
  const finishToday = () => {
    app.completeMission();
    setDone(true);
  };

  if (done) {
    return (
      <View>
        <Fade>
          <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft, alignItems: 'center' }}>
            <Mascot personaId={app.selectedPersonaId} size={120} expression="cheer" />
            <Title>오늘 학습 완료!</Title>
            <Text style={{ fontSize: 16, color: theme.colors.text, marginTop: 4, textAlign: 'center' }}>
              {name}와 오늘의 문장 {app.practiceTotal}개를 모두 따라 말했어요.
            </Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 16 }}>
              <ProgressRing size={92} stroke={10} pct={1} color={theme.colors.good} centerTop={`${app.practiceTotal}`} centerBottom={`/${app.practiceTotal}`} />
              {app.gam?.streakDays ? (
                <View style={{ marginLeft: 20 }}>
                  <Icon name="flame" size={30} color={theme.colors.gold} />
                  <Text style={{ fontSize: 18, fontWeight: '800', color: theme.colors.text }}>{app.gam.streakDays}일 연속</Text>
                  <Muted>내일도 이어가요</Muted>
                </View>
              ) : null}
            </View>
          </Card>
        </Fade>
        <Fade delay={120}>
          <Button title="성장 확인하기 →" onPress={() => app.navigate('progress')} color={color} />
          <Button title="홈으로" onPress={() => app.navigate('home')} secondary />
        </Fade>
      </View>
    );
  }

  return (
    <View>
      <Fade>
        <Title>{STRINGS.voice.title(name)}</Title>
        {app.demoMode && (
          <View style={{ alignSelf: 'flex-start' }}>
            <Pill label={STRINGS.voice.demoBadge} />
          </View>
        )}
      </Fade>

      <Fade delay={60}>
        <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Mascot personaId={app.selectedPersonaId} size={96} expression={expr} speaking={app.speaking} />
            <View style={{ flex: 1, marginLeft: 10 }}>
              <Muted>{name}</Muted>
              <Text style={{ fontSize: 15, lineHeight: 23, color: theme.colors.text }}>
                {assistantText || personaCoaching(app.selectedPersonaId).opening}
              </Text>
            </View>
          </View>
        </Card>
      </Fade>

      <Fade delay={120}>
        <Card>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <Muted>{STRINGS.voice.repeatThis}</Muted>
            <Pill label={`오늘의 문장 ${app.phraseIndex + 1}/${app.practiceTotal}`} />
          </View>
          <View style={{ marginVertical: 8 }}>
            <Furigana phrase={spokenText} size={28} color={color} />
          </View>
          {app.currentPhraseKo ? <Muted>{app.currentPhraseKo}</Muted> : null}
          <Button title={app.speaking ? STRINGS.voice.playing : STRINGS.voice.play} onPress={() => app.speak(spokenText)} color={color} />
          <Button icon="mic" title={hasResult ? '다시 말하기' : STRINGS.voice.record} onPress={app.runMockStt} secondary color={color} />

          {failed && (
            <View style={{ marginTop: 12, padding: 12, borderRadius: 12, backgroundColor: theme.colors.bad + '18' }}>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <Icon name="alert" size={16} color={theme.colors.bad} />
                <Text style={{ color: theme.colors.bad, fontWeight: '800', marginLeft: 6 }}>인식 실패</Text>
              </View>
              <Text style={{ color: theme.colors.text, marginTop: 4 }}>{sttNote}</Text>
              <View style={{ marginTop: 10 }}>
                <Button title={personaCoaching(app.selectedPersonaId).retryCta} onPress={app.runMockStt} color={color} />
              </View>
            </View>
          )}

          {hasResult && !failed && (
            <View style={{ marginTop: 14, flexDirection: 'row', alignItems: 'center' }}>
              <ProgressRing size={84} stroke={9} pct={(accuracy ?? 0) / 100} color={ringColor} centerTop={`${accuracy ?? 0}`} centerBottom="%" />
              <View style={{ flex: 1, marginLeft: 14 }}>
                <Muted>{STRINGS.voice.sttResult} {sttStatus === 'perfect' ? '✓ 정확' : '△ 부분 일치'}</Muted>
                <DiffText segs={diff} size={20} />
                <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 4 }}>{sttNote}</Text>
              </View>
            </View>
          )}
        </Card>
      </Fade>

      {hasResult && coachingNow && (
        <Fade delay={150}>
          <Card style={{ borderColor: color, borderWidth: 1.5 }}>
            <Muted>{name}의 코칭</Muted>
            <Text style={{ fontSize: 16, color: theme.colors.text, marginTop: 2 }}>{coachingNow}</Text>
          </Card>
        </Fade>
      )}

      {corrections.length > 0 && !failed && (
        <Fade delay={170}>
          <Card>
            <Muted>{STRINGS.voice.correctionCard}</Muted>
            {corrections.map((c, i) => (
              <View key={i} style={{ marginTop: 8 }}>
                <Text style={{ fontSize: 13, color: theme.colors.subtext }}>{correctionLabel(c.category, c.severity)}</Text>
                <Text style={{ fontSize: 18, color: theme.colors.accentDark, fontWeight: '700', marginTop: 2 }}>{c.corrected}</Text>
                <Text style={{ fontSize: 15, color: theme.colors.text, lineHeight: 22, marginTop: 2 }}>{c.explanationKo}</Text>
              </View>
            ))}
          </Card>
        </Fade>
      )}

      <Fade delay={200}>
        {/* Primary action = keep the loop moving. Save is a small side action. */}
        {hasResult && !failed ? (
          isLast ? (
            <Button title="오늘 학습 완료" onPress={finishToday} color={color} />
          ) : (
            <Button title="다음 문장 →" onPress={app.nextPhrase} color={color} />
          )
        ) : (
          <Button title={STRINGS.voice.backToPractice} onPress={() => app.navigate('practice')} secondary />
        )}
        {hasResult && !failed && (
          <Pressable
            onPress={app.saveReviewCard}
            style={{ marginTop: 8, paddingVertical: 8, alignItems: 'center' }}
            accessibilityRole="button"
          >
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              {!app.lastSaveState ? <Icon name="bookmark" size={14} color={theme.colors.subtext} /> : null}
              <Text style={{ fontSize: 14, color: app.lastSaveState ? theme.colors.good : theme.colors.subtext, fontWeight: '600', marginLeft: app.lastSaveState ? 0 : 6 }}>
                {app.lastSaveState === 'saved'
                  ? '✓ 복습 카드에 저장됨'
                  : app.lastSaveState === 'duplicate'
                    ? '이미 복습 카드에 있어요'
                    : '이 문장 복습 카드에 저장'}
              </Text>
            </View>
          </Pressable>
        )}
      </Fade>
    </View>
  );
}
