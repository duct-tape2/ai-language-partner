import React from 'react';
import { Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { STRINGS } from '../i18n';
import { ALL_BADGES } from '../gamification';
import { BadgeChip, Button, Card, Fade, Muted, ProgressRing, Row, Stat, Title, XPBar } from '../components';
import { Mascot } from '../characters/Mascot';
import { learnerName } from '../labels';
import type { AppController } from '../store';

export function ProgressScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const { progress, settings, gam } = app;
  const goalPct = Math.min(1, progress.spokenSentenceCount / Math.max(1, settings.dailyGoal));
  // Only today has local history; show today's bar filled, prior days await tracking.
  const week = [0, 0, 0, 0, 0, 0, progress.spokenSentenceCount];
  const weekMax = Math.max(1, ...week);
  const dayLabels = ['월', '화', '수', '목', '금', '토', '일'];

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <Mascot personaId={app.selectedPersonaId} size={76} expression={progress.completedMissions > 0 ? 'cheer' : 'idle'} />
          <View style={{ flex: 1, marginLeft: 8 }}>
            <Title>{STRINGS.progress.title}</Title>
            <Muted>{progress.completedMissions > 0 ? '오늘도 잘하고 있어요!' : '오늘의 첫 미션을 시작해볼까요?'}</Muted>
          </View>
        </View>
      </Fade>

      <Fade delay={60}>
        <Card>
          <XPBar level={app.level} pct={app.levelPct} />
        </Card>
      </Fade>

      <Fade delay={100}>
        <Card>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <ProgressRing size={104} pct={goalPct} centerTop={`${progress.spokenSentenceCount}`} centerBottom={`/ ${settings.dailyGoal}`} />
            <View style={{ flex: 1, marginLeft: 16 }}>
              <Text style={{ fontSize: 17, fontWeight: '800', color: theme.colors.text }}>{STRINGS.home.dailyGoal}</Text>
              <Muted>오늘 말한 문장 / 목표</Muted>
            </View>
          </View>
        </Card>
      </Fade>

      <Fade delay={140}>
        <Card>
          <Row>
            <Stat label={STRINGS.progress.streakDays} value={`${progress.streakDays}`} />
            <Stat label={STRINGS.progress.spoken} value={progress.spokenSentenceCount} />
            <Stat label={STRINGS.progress.cards} value={app.srsCards.length} />
            <Stat label={STRINGS.progress.missions} value={progress.completedMissions} />
          </Row>
        </Card>
      </Fade>

      <Fade delay={180}>
        <Card>
          <Muted>{STRINGS.progress.weekly}</Muted>
          <View style={{ flexDirection: 'row', alignItems: 'flex-end', height: 90, marginTop: 8 }}>
            {week.map((v, i) => (
              <View key={i} style={{ flex: 1, alignItems: 'center' }}>
                <View style={{ width: 16, height: Math.max(4, (v / weekMax) * 70), backgroundColor: i === 6 ? theme.colors.accent : theme.colors.track, borderRadius: 6 }} />
                <Text style={{ fontSize: 11, color: theme.colors.subtext, marginTop: 4 }}>{dayLabels[i]}</Text>
              </View>
            ))}
          </View>
          {progress.spokenSentenceCount === 0 && (
            <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 8 }}>오늘 한 문장만 말해도 여기에 기록돼요.</Text>
          )}
        </Card>
      </Fade>

      {app.serverGam && (
        <Fade delay={210}>
          <Card>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
              <Muted>리그 · 주간 랭킹 {app.apiInfo.mode === 'real' ? '(서버)' : ''}</Muted>
              <Text style={{ fontWeight: '800', color: theme.colors.goldText }}>
                {app.serverGam.league.currentTier.name} · {app.serverGam.xp.weekXp} XP
              </Text>
            </View>
            {app.reputation && !app.reputation.leaderboardEligible ? (
              <Text style={{ fontSize: 13, color: theme.colors.bad, marginTop: 2 }}>이번 주 랭킹 참여가 일시 제한됐어요. XP는 계속 기록돼요.</Text>
            ) : app.reputation && app.reputation.reviewRecommended ? (
              <Text style={{ fontSize: 13, color: theme.colors.goldText, marginTop: 2 }}>랭킹 반영이 잠시 검토 중이에요. XP는 기록되고 있어요.</Text>
            ) : null}
            {app.serverGam.weeklyLeaderboard.entries.length === 0 ? (
              <Muted>이번 주 첫 XP를 쌓아 랭킹에 올라보세요.</Muted>
            ) : (
              app.serverGam.weeklyLeaderboard.entries.slice(0, 5).map((e) => (
                <View key={e.learnerId} style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 3 }}>
                  <Text style={{ color: e.isCurrentLearner ? theme.colors.accentDark : theme.colors.text, fontWeight: e.isCurrentLearner ? '800' : '500' }}>
                    {e.rank}. {learnerName(e.learnerId, e.isCurrentLearner)}
                  </Text>
                  <Text style={{ color: theme.colors.subtext }}>{e.xp} XP</Text>
                </View>
              ))
            )}
            <Muted>리그 도전과제 {app.serverGam.achievements.awardedCount}/{app.serverGam.achievements.totalCount} · 아래 배지와는 별개예요</Muted>
            <View style={{ flexDirection: 'row', gap: 10, marginTop: 12 }}>
              <View style={{ flex: 1 }}>
                <Button icon="people" title={`친구${app.friends?.friendCount ? ` ${app.friends.friendCount}` : ''}`} onPress={() => app.navigate('friends')} secondary />
              </View>
              <View style={{ flex: 1 }}>
                <Button
                  icon="gem"
                  title={`${app.serverGam.rewardInventory.balances.find((b) => b.currencyKey === 'gems')?.balance ?? 0} · 상점`}
                  onPress={() => app.navigate('shop')}
                />
              </View>
            </View>
          </Card>
        </Fade>
      )}

      <Fade delay={220}>
        <Card>
          <Muted>{STRINGS.progress.badges} · {gam.badgeIds.length}/{ALL_BADGES.length}</Muted>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 8 }}>
            {ALL_BADGES.map((b) => (
              <BadgeChip key={b.id} emoji={b.emoji} label={b.label} earned={gam.badgeIds.includes(b.id)} />
            ))}
          </View>
          {gam.badgeIds.length === 0 && (
            <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 4 }}>
              첫 따라 말하기와 첫 복습 카드로 배지를 바로 받을 수 있어요.
            </Text>
          )}
        </Card>
      </Fade>

    </View>
  );
}
