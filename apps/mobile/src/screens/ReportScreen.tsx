import React from 'react';
import { Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { Button, Card, Fade, Muted, Pill, ProgressRing, Row, Title } from '../components';
import { Icon } from '../icons';
import { buildReport } from '../report/reportUtils';
import type { AppController } from '../store';

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string | number;
  accent?: boolean;
}) {
  const { theme } = useTheme();
  return (
    <View
      style={{
        flexBasis: '48%',
        flexGrow: 1,
        backgroundColor: theme.colors.card,
        borderRadius: theme.radius.md,
        borderWidth: 1,
        borderColor: theme.colors.border,
        padding: 14,
        marginBottom: 10,
      }}
    >
      <Text style={{ fontSize: 26, fontWeight: '900', color: accent ? theme.colors.accentDark : theme.colors.text }}>
        {value}
      </Text>
      <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 2 }}>{label}</Text>
    </View>
  );
}

export function ReportScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const { progress, gam, srsCards, dueCards, settings } = app;

  React.useEffect(() => {
    app.track('report_viewed');
    // track identity is stable in the store; only fire on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const report = React.useMemo(
    () => buildReport(progress, gam, srsCards, dueCards, settings.dailyGoal),
    [progress, gam, srsCards, dueCards, settings.dailyGoal],
  );

  // No per-day history is stored yet, so the 7-day row shows today's value on the
  // final bar and leaves prior days empty. Labeled honestly with a '오늘 기준' note.
  const week = [0, 0, 0, 0, 0, 0, report.spokenToday];
  const weekMax = Math.max(1, ...week);
  const dayLabels = ['월', '화', '수', '목', '금', '토', '일'];

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
          <View style={{ flex: 1 }}>
            <Title>주간 학습 리포트</Title>
            <Muted>내 로컬 기록으로 만든 요약이에요.</Muted>
          </View>
          <View style={{ alignItems: 'flex-end' }}>
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              <Icon name="flame" size={18} color={theme.colors.goldText} />
              <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.goldText, marginLeft: 4 }}>
                {report.streakDays}일
              </Text>
            </View>
            <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 2 }}>{gam.xp} XP</Text>
          </View>
        </View>
      </Fade>

      <Fade delay={60}>
        <Card>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <ProgressRing
              size={104}
              pct={report.goalPct}
              centerTop={`${report.spokenToday}`}
              centerBottom={`/ ${report.dailyGoal}`}
            />
            <View style={{ flex: 1, marginLeft: 16 }}>
              <Text style={{ fontSize: 17, fontWeight: '800', color: theme.colors.text }}>오늘의 목표</Text>
              <Muted>오늘 말한 문장 / 하루 목표</Muted>
              <Row>
                <Pill label={report.levelBand.label} />
              </Row>
              <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 6 }}>{report.levelBand.note}</Text>
            </View>
          </View>
        </Card>
      </Fade>

      <Fade delay={100}>
        <Row>
          <View style={{ width: '100%', flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' }}>
            <StatCard label="연속일" value={`${report.streakDays}일`} accent />
            <StatCard label="오늘 말한 문장" value={report.spokenToday} accent />
            <StatCard label="저장 복습카드" value={report.reviewCardsSaved} />
            <StatCard label="복습 대기" value={report.dueCount} />
          </View>
        </Row>
      </Fade>

      <Fade delay={140}>
        <Card>
          <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
            <Muted>7일 활동</Muted>
            <View style={{ backgroundColor: theme.colors.chip, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4 }}>
              <Text style={{ fontSize: 11, fontWeight: '700', color: theme.colors.chipText }}>오늘 기준</Text>
            </View>
          </View>
          <View style={{ flexDirection: 'row', alignItems: 'flex-end', height: 90, marginTop: 10 }}>
            {week.map((v, i) => (
              <View key={i} style={{ flex: 1, alignItems: 'center' }}>
                <View
                  style={{
                    width: 16,
                    height: Math.max(4, (v / weekMax) * 70),
                    backgroundColor: i === 6 ? theme.colors.accent : theme.colors.track,
                    borderRadius: 6,
                  }}
                />
                <Text style={{ fontSize: 11, color: theme.colors.subtext, marginTop: 4 }}>{dayLabels[i]}</Text>
              </View>
            ))}
          </View>
          <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 8 }}>
            아직 하루별 기록은 저장하지 않아요. 오늘 값만 정확히 보여줘요.
          </Text>
        </Card>
      </Fade>

      <Fade delay={180}>
        <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
          {report.encouragement.map((line, i) => (
            <View key={i} style={{ flexDirection: 'row', marginBottom: i === report.encouragement.length - 1 ? 0 : 6 }}>
              <Text style={{ color: theme.colors.accentDark, fontWeight: '900', marginRight: 8 }}>·</Text>
              <Text style={{ flex: 1, fontSize: 15, fontWeight: '600', color: theme.colors.text, lineHeight: 22 }}>
                {line}
              </Text>
            </View>
          ))}
        </Card>
      </Fade>

      <Fade delay={220}>
        <View>
          <Button title="오늘 학습 계속" onPress={() => app.navigate('hub')} />
          <Button title="복습하기" onPress={() => app.navigate('review')} secondary />
          <Button title="홈으로" onPress={() => app.navigate('home')} tone="neutral" secondary />
        </View>
      </Fade>

      <Fade delay={260}>
        <Text style={{ fontSize: 12, color: theme.colors.subtext, textAlign: 'center', marginTop: 4, marginBottom: 8 }}>
          데모 · 이 리포트는 기기에 저장된 학습 기록만으로 계산돼요.
        </Text>
      </Fade>
    </View>
  );
}
