import React from 'react';
import { Text, View, Pressable } from 'react-native';
import { useTheme } from '../ThemeContext';
import { Button, Card, Fade, Muted, Pill, ProgressRing, Row, Title } from '../components';
import { Icon } from '../icons';
import { personaColor } from '../personaStyle';
import { buildInsights } from '../insights/insightsUtils';
import type { InsightStat, InsightSuggestion, SrsMaturity } from '../insights/insightsUtils';
import type { AppController } from '../store';

function StatTile({ stat }: { stat: InsightStat }) {
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
      <Text style={{ fontSize: 24, fontWeight: '900', color: stat.accent ? theme.colors.accentDark : theme.colors.text }}>
        {stat.value}
      </Text>
      <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 2 }}>{stat.label}</Text>
      {stat.hint ? <Text style={{ fontSize: 11, color: theme.colors.subtext, marginTop: 4 }}>{stat.hint}</Text> : null}
    </View>
  );
}

function MaturityBar({ maturity }: { maturity: SrsMaturity }) {
  const { theme } = useTheme();
  const segs: { label: string; value: number; color: string }[] = [
    { label: '새 카드', value: maturity.fresh, color: theme.colors.track },
    { label: '학습중', value: maturity.learning, color: theme.colors.near },
    { label: '자리잡는중', value: maturity.maturing, color: theme.colors.accent },
    { label: '성숙', value: maturity.mature, color: theme.colors.good },
  ];
  const total = Math.max(1, maturity.total);
  return (
    <View>
      <View
        style={{
          flexDirection: 'row',
          height: 16,
          borderRadius: 999,
          overflow: 'hidden',
          backgroundColor: theme.colors.track,
          marginBottom: 12,
        }}
      >
        {segs.map((s) =>
          s.value > 0 ? <View key={s.label} style={{ flex: s.value / total, backgroundColor: s.color }} /> : null,
        )}
      </View>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
        {segs.map((s) => (
          <View key={s.label} style={{ flexDirection: 'row', alignItems: 'center', width: '50%', marginBottom: 6 }}>
            <View style={{ width: 10, height: 10, borderRadius: 3, backgroundColor: s.color, marginRight: 6 }} />
            <Text style={{ fontSize: 13, color: theme.colors.text, fontWeight: '700' }}>{s.value}</Text>
            <Text style={{ fontSize: 12, color: theme.colors.subtext, marginLeft: 4 }}>{s.label}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

function SuggestionCard({ s, onPress }: { s: InsightSuggestion; onPress: () => void }) {
  const { theme } = useTheme();
  const accent =
    s.tone === 'good' ? theme.colors.good : s.tone === 'near' ? theme.colors.near : theme.colors.accent;
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={`${s.title}. ${s.cta}`} onPress={onPress}>
      <View
        style={{
          backgroundColor: theme.colors.card,
          borderRadius: theme.radius.md,
          borderWidth: 1,
          borderColor: theme.colors.border,
          borderLeftWidth: 4,
          borderLeftColor: accent,
          padding: 14,
          marginBottom: 10,
        }}
      >
        <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.text }}>{s.title}</Text>
        <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 4, lineHeight: 20 }}>{s.body}</Text>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 8 }}>
          <Text style={{ fontSize: 14, fontWeight: '800', color: accent }}>{s.cta}</Text>
          <Text style={{ fontSize: 14, fontWeight: '800', color: accent, marginLeft: 4 }}>›</Text>
        </View>
      </View>
    </Pressable>
  );
}

export function InsightsScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const { progress, gam, srsCards, dueCards, settings, level, levelPct } = app;
  const ringColor = personaColor(app.selectedPersonaId);

  React.useEffect(() => {
    app.track('insights_viewed');
    // track identity is stable in the store; fire once on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const insights = React.useMemo(
    () =>
      buildInsights({
        progress,
        gam,
        srsCards,
        dueCards,
        dailyGoal: settings.dailyGoal,
        level,
        levelPct,
      }),
    [progress, gam, srsCards, dueCards, settings.dailyGoal, level, levelPct],
  );

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
          <View style={{ flex: 1 }}>
            <Title>학습 인사이트</Title>
            <Muted>내 학습 데이터로 만든 요약이에요.</Muted>
          </View>
          <View style={{ alignItems: 'flex-end' }}>
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              <Icon name="flame" size={18} color={theme.colors.goldText} />
              <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.goldText, marginLeft: 4 }}>
                {insights.streakDays}일
              </Text>
            </View>
            <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 2 }}>Lv.{insights.level} · {insights.xp} XP</Text>
          </View>
        </View>
      </Fade>

      <Fade delay={60}>
        <Card>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <ProgressRing
              size={104}
              pct={insights.goalPct}
              color={ringColor}
              centerTop={`${Math.round(insights.goalPct * 100)}%`}
              centerBottom="오늘 목표"
            />
            <View style={{ flex: 1, marginLeft: 16 }}>
              <Text style={{ fontSize: 17, fontWeight: '800', color: theme.colors.text }}>오늘 목표 달성률</Text>
              <Muted>오늘 말한 문장 / 하루 목표</Muted>
              <Row>
                <Pill label={`${insights.spokenToday} / ${insights.dailyGoal}문장`} />
                {insights.goalMet ? <Pill label="목표 달성" color={theme.colors.good} /> : null}
              </Row>
            </View>
          </View>
        </Card>
      </Fade>

      <Fade delay={100}>
        <View style={{ width: '100%', flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' }}>
          {insights.stats.map((s) => (
            <StatTile key={s.key} stat={s} />
          ))}
        </View>
      </Fade>

      <Fade delay={140}>
        <Card>
          <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text }}>SRS 상태 요약</Text>
            <View style={{ backgroundColor: theme.colors.chip, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4 }}>
              <Text style={{ fontSize: 11, fontWeight: '700', color: theme.colors.chipText }}>
                전체 {insights.maturity.total}장
              </Text>
            </View>
          </View>
          {insights.maturity.total > 0 ? (
            <>
              <MaturityBar maturity={insights.maturity} />
              <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 8 }}>
                지금 복습 가능한 카드 {insights.maturity.due}장이에요.
              </Text>
            </>
          ) : (
            <Muted>아직 복습 카드가 없어요. 연습에서 카드를 모으면 여기에 나와요.</Muted>
          )}
        </Card>
      </Fade>

      <Fade delay={180}>
        <View>
          <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text, marginBottom: 8 }}>개선 제안</Text>
          {insights.suggestions.map((s) => (
            <SuggestionCard key={s.key} s={s} onPress={() => app.navigate(s.target)} />
          ))}
        </View>
      </Fade>

      <Fade delay={220}>
        <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
          <Text style={{ fontSize: 13, color: theme.colors.text, lineHeight: 20 }}>
            이 지표는 이 기기의 내 학습 기록이에요. 다른 사용자와 비교한 통계가 아니라, 이 앱에서 내가 남긴 기록만으로
            계산했어요.
          </Text>
        </Card>
      </Fade>

      <Fade delay={260}>
        <View>
          <Button title="복습하기" onPress={() => app.navigate('review')} />
          <Button title="연습 계속" onPress={() => app.navigate('hub')} secondary />
          <Button title="홈으로" onPress={() => app.navigate('home')} tone="neutral" secondary />
        </View>
      </Fade>
    </View>
  );
}
