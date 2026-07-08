import React from 'react';
import { Text, View, Pressable } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Card, Button, Title, Muted, Pill, Fade, Row, ProgressRing } from '../components';
import { SKILLS, recommendNext, type MasterySkill } from '../mastery/masterySkills';
import type { AppController } from '../store';

// Learning-status + mastery dashboard. A hub that ties the many learning
// modules together: header stats + today's-goal ring, a weak-area
// recommendation section, and a full tappable skill grid. The "학습함" toggles
// are local UI state only (no persistence, no backend) so the learner can mark
// off what they've covered in this session.

function StatCard({ value, label, color }: { value: string | number; label: string; color: string }) {
  const { theme } = useTheme();
  return (
    <View
      style={{
        flex: 1,
        backgroundColor: theme.colors.card,
        borderColor: theme.colors.border,
        borderWidth: 1,
        borderRadius: theme.radius.md,
        paddingVertical: 14,
        paddingHorizontal: 8,
        marginHorizontal: 4,
        alignItems: 'center',
      }}
    >
      <Text style={{ fontSize: 26, fontWeight: '900', color }}>{value}</Text>
      <Text style={{ fontSize: 12, color: theme.colors.subtext, marginTop: 4, textAlign: 'center' }}>{label}</Text>
    </View>
  );
}

export function MasteryScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const color = personaColor(app.selectedPersonaId);
  const progress = app.progress;
  const goal = Math.max(1, app.settings.dailyGoal);
  const spoken = progress.spokenSentenceCount;
  const pct = Math.min(1, spoken / goal);
  const goalMet = spoken >= goal;

  const recommended = React.useMemo(() => recommendNext(progress), [progress.spokenSentenceCount, progress.reviewCardsCreated, progress.streakDays]);

  // Local-only "studied this session" marks. React state only, by design.
  const [studied, setStudied] = React.useState<Record<string, boolean>>({});
  const studiedCount = Object.values(studied).filter(Boolean).length;
  const toggle = (key: string) => setStudied((s) => ({ ...s, [key]: !s[key] }));

  React.useEffect(() => {
    app.track('mastery_opened', { streakDays: progress.streakDays, spokenSentenceCount: spoken, reviewCardsCreated: progress.reviewCardsCreated });
    // Fire once on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const go = (skill: MasterySkill) => {
    app.track('mastery_skill_opened', { skill: skill.key, navKey: skill.navKey });
    app.navigate(skill.navKey);
  };

  return (
    <View>
      <Fade>
        <Title>학습 현황</Title>
        <Muted>지금까지의 학습을 한눈에 보고, 다음에 무엇을 하면 좋을지 골라요</Muted>
      </Fade>

      {/* Header stats */}
      <Fade delay={60}>
        <View style={{ flexDirection: 'row', marginTop: 14, marginBottom: 4 }}>
          <StatCard value={`${progress.streakDays}일`} label="연속 학습" color={theme.colors.goldText} />
          <StatCard value={spoken} label="오늘 말한 문장" color={color} />
          <StatCard value={progress.reviewCardsCreated} label="복습 카드" color={theme.colors.accentDark} />
        </View>
      </Fade>

      {/* Today's goal ring */}
      <Fade delay={120}>
        <Card>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <ProgressRing
              size={104}
              stroke={12}
              pct={pct}
              color={goalMet ? theme.colors.good : color}
              centerTop={`${spoken}/${goal}`}
              centerBottom="오늘 목표"
            />
            <View style={{ flex: 1, marginLeft: 16 }}>
              <Text style={{ fontSize: 17, fontWeight: '800', color: theme.colors.text }}>
                {goalMet ? '오늘 목표 달성!' : '오늘 목표까지'}
              </Text>
              <Muted>
                {goalMet
                  ? '멋져요. 추천 학습으로 한 걸음 더 나가볼까요?'
                  : `문장 ${Math.max(0, goal - spoken)}개만 더 말하면 오늘 목표를 채워요.`}
              </Muted>
              {studiedCount > 0 ? (
                <Row>
                  <Pill label={`이번 세션 학습함 ${studiedCount}`} color={color} />
                </Row>
              ) : null}
            </View>
          </View>
        </Card>
      </Fade>

      {/* Weak-area recommendation */}
      <Fade delay={180}>
        <Text style={{ fontSize: 18, fontWeight: '800', color: theme.colors.text, marginTop: 10, marginBottom: 6 }}>추천 학습</Text>
        <Muted>지금 상태에 맞춰 고른 다음 단계예요</Muted>
      </Fade>
      {recommended.map((s, i) => (
        <Fade key={s.key} delay={220 + i * 50}>
          <Pressable onPress={() => go(s)} accessibilityRole="button" accessibilityLabel={`${s.labelKo} 학습하기`}>
            <Card style={{ borderColor: color, borderWidth: 1.5 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <View style={{ width: 48, height: 48, borderRadius: 14, backgroundColor: theme.colors.accentSoft, alignItems: 'center', justifyContent: 'center' }}>
                  <Text style={{ fontSize: 24 }}>{s.icon}</Text>
                </View>
                <View style={{ flex: 1, marginLeft: 12 }}>
                  <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text }}>{s.labelKo}</Text>
                  <Muted>{s.blurbKo}</Muted>
                </View>
                <Text style={{ fontSize: 22, color, marginLeft: 6 }}>›</Text>
              </View>
            </Card>
          </Pressable>
        </Fade>
      ))}

      {/* Full skill grid */}
      <Fade delay={260}>
        <Text style={{ fontSize: 18, fontWeight: '800', color: theme.colors.text, marginTop: 10, marginBottom: 6 }}>전체 스킬</Text>
        <Muted>누르면 해당 학습으로 이동해요. 오른쪽 버튼으로 학습 여부를 표시할 수 있어요</Muted>
      </Fade>
      {SKILLS.map((s, i) => {
        const done = !!studied[s.key];
        return (
          <Fade key={s.key} delay={300 + i * 30}>
            <Card style={{ opacity: done ? 0.72 : 1 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <Pressable
                  onPress={() => go(s)}
                  accessibilityRole="button"
                  accessibilityLabel={`${s.labelKo} 학습으로 이동`}
                  style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}
                >
                  <View style={{ width: 46, height: 46, borderRadius: 12, backgroundColor: theme.colors.chip, alignItems: 'center', justifyContent: 'center' }}>
                    <Text style={{ fontSize: 22 }}>{s.icon}</Text>
                  </View>
                  <View style={{ flex: 1, marginLeft: 12 }}>
                    <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.text }}>
                      {s.labelKo} {done ? <Text style={{ fontSize: 12, color: theme.colors.good }}>학습함</Text> : null}
                    </Text>
                    <Muted>{s.blurbKo}</Muted>
                  </View>
                </Pressable>
                <Pressable
                  onPress={() => toggle(s.key)}
                  accessibilityRole="button"
                  accessibilityLabel={done ? `${s.labelKo} 학습함 표시 해제` : `${s.labelKo} 학습함으로 표시`}
                  accessibilityState={{ selected: done }}
                  style={{
                    marginLeft: 8,
                    paddingVertical: 8,
                    paddingHorizontal: 12,
                    borderRadius: theme.radius.md,
                    borderWidth: 1.5,
                    borderColor: done ? theme.colors.good : theme.colors.border,
                    backgroundColor: done ? theme.colors.good : 'transparent',
                  }}
                >
                  <Text style={{ fontSize: 13, fontWeight: '800', color: done ? '#fff' : theme.colors.subtext }}>
                    {done ? '✓ 학습함' : '학습함'}
                  </Text>
                </Pressable>
              </View>
            </Card>
          </Fade>
        );
      })}

      <Fade delay={340}>
        <Button title="홈으로" secondary onPress={() => app.navigate('home')} />
      </Fade>
    </View>
  );
}
