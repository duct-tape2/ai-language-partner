import React from 'react';
import { Text, View, Pressable } from 'react-native';
import { useTheme } from '../ThemeContext';
import { Card, Button, Title, Muted, Pill, Fade, Row, ProgressRing } from '../components';
import { Icon, EMOJI_TO_ICON } from '../icons';
import { personaColor } from '../personaStyle';
import { buildQuests, STREAK_REPAIR_INFO, RETURN_BONUS_INFO } from '../quests/questData';
import type { BuiltQuest } from '../quests/questData';
import type { AppController } from '../store';

// Daily Quest & Streak - retention economy screen.
// Uses LOCAL gam/progress data. If app.serverGam.dailyQuests exists it renders
// those (server-verified); otherwise it derives a local quest set from today's
// on-device progress. Honest: no real reward transactions here, only goals and
// encouragement.

type UiQuest = {
  key: string;
  icon: string;
  label: string;
  tip: string;
  current: number;
  target: number;
  done: boolean;
  navTarget?: BuiltQuest['navTarget'];
  rewardXp?: number; // only present for server quests, shown as a stated reward
};

function ProgressBar({ pct, color }: { pct: number; color: string }) {
  const { theme } = useTheme();
  const w = Math.min(1, Math.max(0, pct));
  return (
    <View style={{ height: 8, borderRadius: 999, backgroundColor: theme.colors.track, overflow: 'hidden', marginTop: 8 }}>
      <View style={{ width: `${w * 100}%`, height: 8, backgroundColor: color, borderRadius: 999 }} />
    </View>
  );
}

function QuestRow({ q, accent, onPress }: { q: UiQuest; accent: string; onPress?: () => void }) {
  const { theme } = useTheme();
  const pct = q.target > 0 ? q.current / q.target : 0;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${q.label}, ${q.current}/${q.target}${q.done ? ', 완료' : ''}`}
      onPress={onPress}
      disabled={!onPress}
      style={{ marginBottom: 14 }}
    >
      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
        <View style={{ width: 28, marginRight: 10, alignItems: 'center' }}>
          {EMOJI_TO_ICON[q.icon] ? (
            <Icon name={EMOJI_TO_ICON[q.icon]} size={22} color={theme.colors.accentDark} />
          ) : (
            <Text style={{ fontSize: 22 }}>{q.icon}</Text>
          )}
        </View>
        <View style={{ flex: 1 }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.text }}>{q.label}</Text>
            <Text style={{ fontSize: 13, fontWeight: '800', color: q.done ? theme.colors.good : theme.colors.subtext }}>
              {q.done ? '완료 ✓' : `${q.current} / ${q.target}`}
            </Text>
          </View>
          <ProgressBar pct={pct} color={q.done ? theme.colors.good : accent} />
          <Text style={{ fontSize: 12, color: theme.colors.subtext, marginTop: 6 }}>{q.tip}</Text>
        </View>
      </View>
    </Pressable>
  );
}

export function DailyQuestScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const accent = personaColor(app.selectedPersonaId);

  React.useEffect(() => {
    app.track('quests_viewed', { source: app.serverGam?.dailyQuests?.length ? 'server' : 'local' });
    // Track once on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const serverQuests = app.serverGam?.dailyQuests ?? [];
  const usingServer = serverQuests.length > 0;

  const quests: UiQuest[] = React.useMemo(() => {
    if (usingServer) {
      return serverQuests.map((sq) => ({
        key: sq.key,
        icon: '🎯',
        label: sq.title,
        tip: sq.rewardXp > 0 ? `완료 시 +${sq.rewardXp} XP` : '오늘 안에 완료해보세요.',
        current: sq.progress,
        target: sq.target,
        done: sq.completed,
        rewardXp: sq.rewardXp,
      }));
    }
    return buildQuests(app.progress).map((bq) => ({
      key: bq.key,
      icon: bq.icon,
      label: bq.labelKo,
      tip: bq.tip,
      current: bq.current,
      target: bq.target,
      done: bq.done,
      navTarget: bq.navTarget,
    }));
  }, [usingServer, serverQuests, app.progress]);

  const doneCount = quests.filter((q) => q.done).length;
  const allDone = quests.length > 0 && doneCount === quests.length;

  // Streak: prefer server streak summary, fall back to local gam/progress.
  const streakDays = app.serverGam?.streak?.currentStreak ?? app.gam.streakDays ?? app.progress.streakDays;
  const longestStreak = app.serverGam?.streak?.longestStreak;

  const navTargets: Record<NonNullable<BuiltQuest['navTarget']>, () => void> = {
    dailytalk: () => app.navigate('dailytalk'),
    review: () => app.navigate('review'),
    hub: () => app.navigate('hub'),
    choukai: () => app.navigate('choukai'),
  };

  return (
    <View>
      <Fade>
        <Title>데일리 퀘스트</Title>
        <Muted>
          {usingServer
            ? '오늘의 목표를 채우면 XP가 쌓여요. 서버에 기록된 퀘스트예요.'
            : '오늘의 목표예요. 기기에 저장된 오늘 학습량으로 계산돼요.'}
        </Muted>
      </Fade>

      <Fade delay={60}>
        <Card>
          <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 6 }}>
            <ProgressRing
              size={92}
              pct={quests.length ? doneCount / quests.length : 0}
              color={accent}
              centerTop={`${doneCount}/${quests.length}`}
              centerBottom="완료"
            />
            <View style={{ flex: 1, marginLeft: 16 }}>
              <Text style={{ fontSize: 17, fontWeight: '800', color: theme.colors.text }}>
                {allDone ? '오늘 목표 모두 달성!' : '오늘의 퀘스트'}
              </Text>
              <Muted>
                {allDone
                  ? '멋져요. 내일도 이 흐름을 이어가요.'
                  : `${quests.length - doneCount}개 남았어요. 하나씩 채워볼까요?`}
              </Muted>
              {!usingServer && (
                <Row>
                  <Pill label="로컬 목표" color={theme.colors.subtext} />
                  <Pill label="실제 보상 없음" color={theme.colors.subtext} />
                </Row>
              )}
            </View>
          </View>
        </Card>
      </Fade>

      <Fade delay={100}>
        <Card>
          {quests.length === 0 ? (
            <Muted>오늘의 퀘스트가 아직 없어요. 홈에서 학습을 시작하면 목표가 생겨요.</Muted>
          ) : (
            quests.map((q) => (
              <QuestRow
                key={q.key}
                q={q}
                accent={accent}
                onPress={q.navTarget ? navTargets[q.navTarget] : undefined}
              />
            ))
          )}
          {usingServer && (
            <Text style={{ fontSize: 12, color: theme.colors.subtext, marginTop: 2 }}>
              XP 보상은 퀘스트 완료 시 서버에서 지급돼요.
            </Text>
          )}
        </Card>
      </Fade>

      <Fade delay={140}>
        <Card>
          <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              <View style={{ marginRight: 8 }}>
                <Icon name="flame" size={26} color={theme.colors.text} />
              </View>
              <View>
                <Text style={{ fontSize: 22, fontWeight: '900', color: theme.colors.text }}>{streakDays}일 연속</Text>
                {longestStreak != null && (
                  <Text style={{ fontSize: 12, color: theme.colors.subtext }}>최고 기록 {longestStreak}일</Text>
                )}
              </View>
            </View>
            <View
              style={{
                backgroundColor: theme.colors.chip,
                borderRadius: 999,
                paddingHorizontal: 12,
                paddingVertical: 6,
              }}
            >
              <Text style={{ color: theme.colors.chipText, fontSize: 12, fontWeight: '700' }}>
                {app.progress.spokenSentenceCount > 0 ? '오늘 유지 중' : '오늘 아직'}
              </Text>
            </View>
          </View>

          <View style={{ height: 1, backgroundColor: theme.colors.border, marginVertical: 12 }} />

          <Text style={{ fontSize: 14, fontWeight: '800', color: theme.colors.text, marginBottom: 4 }}>
            스트릭 프리즈 / 리페어
          </Text>
          <Text style={{ fontSize: 13, color: theme.colors.subtext, lineHeight: 20 }}>{STREAK_REPAIR_INFO}</Text>
          <Row>
            <Pill label="준비 중" color={theme.colors.subtext} />
          </Row>
        </Card>
      </Fade>

      <Fade delay={180}>
        <Card>
          <Text style={{ fontSize: 14, fontWeight: '800', color: theme.colors.text, marginBottom: 4 }}>복귀 보너스</Text>
          <Text style={{ fontSize: 13, color: theme.colors.subtext, lineHeight: 20 }}>{RETURN_BONUS_INFO}</Text>
          <Row>
            <Pill label="준비 중" color={theme.colors.subtext} />
          </Row>
        </Card>
      </Fade>

      <Fade delay={220}>
        <Card>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
            <Text style={{ fontWeight: '800', color: theme.colors.text }}>레벨 {app.level}</Text>
            <Text style={{ color: theme.colors.subtext, fontSize: 12 }}>{Math.round(app.levelPct * 100)}%</Text>
          </View>
          <ProgressBar pct={app.levelPct} color={accent} />
          <Text style={{ fontSize: 12, color: theme.colors.subtext, marginTop: 8 }}>
            현재 {app.gam.xp} XP · 말하기와 복습으로 XP가 쌓여요.
          </Text>
        </Card>
      </Fade>

      <Fade delay={260}>
        <Button title="오늘의 대화 하러 가기" onPress={() => app.navigate('dailytalk')} color={accent} />
        <Button title="복습하기" onPress={() => app.navigate('review')} secondary color={accent} />
        <Button title="연습 허브 열기" onPress={() => app.navigate('hub')} secondary color={accent} />
        <Button title="홈으로" onPress={() => app.navigate('home')} tone="neutral" secondary />
      </Fade>
    </View>
  );
}
