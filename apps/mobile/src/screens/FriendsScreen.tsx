import React, { useState } from 'react';
import { Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { Button, Card, Fade, Muted, Pill, Row, Title } from '../components';
import { courseLevelLabel, friendReason, learnerName } from '../labels';
import { rewardTitle } from '../labels';
import type { AppController } from '../store';

export function FriendsScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const { friends, friendRecs, friendQuests } = app;
  const [confirmRemove, setConfirmRemove] = useState<string | null>(null);

  const incoming = friends?.incomingInvites ?? [];
  const outgoing = friends?.outgoingInvites ?? [];
  const recs = friendRecs?.recommendations ?? [];
  const quests = friendQuests?.friendQuests ?? [];
  const blocks = app.socialBlocks?.blocks ?? [];

  return (
    <View>
      <Fade>
        <Muted>소셜</Muted>
        <Title>함께 배우는 친구</Title>
        <Muted>친구와 함께 주간 목표에 도전하고 서로의 학습을 응원해요.</Muted>
      </Fade>

      {app.socialSettings && (!app.socialSettings.discoverable || !app.socialSettings.allowFriendInvites || !app.socialSettings.showWeeklyXp) && (
        <Fade delay={30}>
          <Card style={{ backgroundColor: theme.colors.bg }}>
            {!app.socialSettings.discoverable && <Muted>· 내 프로필은 추천에 노출되지 않아요.</Muted>}
            {!app.socialSettings.allowFriendInvites && <Muted>· 친구 초대 받기를 꺼두었어요.</Muted>}
            {!app.socialSettings.showWeeklyXp && <Muted>· 내 주간 XP는 친구에게 비공개예요.</Muted>}
            <Text onPress={() => app.navigate('settings')} style={{ color: theme.colors.accentDark, fontSize: 13, fontWeight: '700', marginTop: 4 }}>설정에서 변경</Text>
          </Card>
        </Fade>
      )}

      {/* Friend quests — co-op weekly goal (Duolingo-style) */}
      {quests.length > 0 && (
        <Fade delay={40}>
          <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
            <Muted>주간 파트너 도전</Muted>
            {quests.map((q) => {
              const pct = Math.max(0, Math.min(1, q.progressRatio));
              const reached = q.combinedXp >= q.targetXp;
              return (
                <View key={q.id} style={{ paddingVertical: 8 }}>
                  <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text }}>주간 파트너 XP 도전</Text>
                  <Muted>{`${learnerName(q.partnerLearnerId)}님과 함께 · ${reached ? '목표 달성! ' : ''}합산 ${q.combinedXp}/${q.targetXp} XP`}</Muted>
                  <View style={{ height: 10, borderRadius: 5, backgroundColor: theme.colors.border, marginTop: 6, overflow: 'hidden' }}>
                    <View style={{ width: `${Math.round(pct * 100)}%`, height: '100%', backgroundColor: theme.colors.accent }} />
                  </View>
                  {q.completed && !q.claimed ? (
                    <View style={{ marginTop: 8 }}>
                      <Button title={`${rewardTitle(q.reward.key, q.reward.title || '보상')} 받기`} onPress={() => app.claimQuest(q.id)} tone="good" />
                    </View>
                  ) : (
                    <Muted>{q.claimed ? '보상을 받았어요 🎉' : `목표까지 ${Math.max(0, q.targetXp - q.combinedXp)} XP`}</Muted>
                  )}
                </View>
              );
            })}
          </Card>
        </Fade>
      )}

      {/* My friends */}
      <Fade delay={80}>
        <Card>
          <Text style={{ fontSize: 18, fontWeight: '800', color: theme.colors.text }}>내 친구 {friends?.friendCount ?? 0}명</Text>
          {(friends?.friends ?? []).length === 0 ? (
            <Muted>아직 친구가 없어요. 아래 추천에서 함께 배울 친구를 초대해보세요.</Muted>
          ) : (
            (friends?.friends ?? []).map((f) => (
              <View key={f.id} style={{ paddingVertical: 6, borderTopWidth: 1, borderTopColor: theme.colors.border }}>
                <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Text style={{ color: theme.colors.text, fontWeight: '600' }}>{learnerName(f.friendLearnerId)}</Text>
                  <View style={{ width: 96 }}>
                    <Button title="삭제" onPress={() => setConfirmRemove(f.friendLearnerId)} tone="bad" secondary />
                  </View>
                </View>
                {confirmRemove === f.friendLearnerId && (
                  <View style={{ marginTop: 8, padding: 12, borderRadius: 12, backgroundColor: theme.colors.bg }}>
                    <Text style={{ color: theme.colors.bad, fontWeight: '800' }}>{learnerName(f.friendLearnerId)}님을 친구에서 삭제할까요?</Text>
                    <Muted>상대방에게 알림은 가지 않아요. 다시 친구가 되려면 초대가 필요해요.</Muted>
                    <View style={{ flexDirection: 'row', gap: 10, marginTop: 8 }}>
                      <View style={{ flex: 1 }}><Button title="취소" onPress={() => setConfirmRemove(null)} secondary /></View>
                      <View style={{ flex: 1 }}><Button title="삭제" onPress={() => { setConfirmRemove(null); app.unfriend(f.friendLearnerId); }} tone="bad" /></View>
                    </View>
                  </View>
                )}
              </View>
            ))
          )}
        </Card>
      </Fade>

      {/* Invites: incoming + outgoing (always show section so users know invites exist) */}
      <Fade delay={120}>
        <Card>
          <Muted>받은 초대 {incoming.length > 0 ? `${incoming.length}건` : ''}</Muted>
          {incoming.length === 0 ? (
            <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 2 }}>받은 초대가 없어요.</Text>
          ) : (
            incoming.map((inv) => (
              <View key={inv.id} style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 6 }}>
                <Text style={{ color: theme.colors.text, fontWeight: '600' }}>{learnerName(inv.requesterLearnerId)}</Text>
                <View style={{ width: 110 }}>
                  <Button title="수락" onPress={() => app.acceptInvite(inv.id)} tone="good" />
                </View>
              </View>
            ))
          )}
          {outgoing.length > 0 && (
            <View style={{ marginTop: 10, borderTopWidth: 1, borderTopColor: theme.colors.border, paddingTop: 8 }}>
              <Muted>보낸 초대 {outgoing.length}건</Muted>
              {outgoing.map((inv) => (
                <View key={inv.id} style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 6 }}>
                  <Text style={{ color: theme.colors.text, fontWeight: '600' }}>{learnerName(inv.addresseeLearnerId)}</Text>
                  <Pill label={inv.status === 'pending' ? '대기 중' : inv.status === 'accepted' ? '수락됨' : '거절됨'} />
                </View>
              ))}
            </View>
          )}
        </Card>
      </Fade>

      {/* Recommendations */}
      <Fade delay={160}>
        <Card>
          <Muted>나와 비슷한 학습자 {friendRecs ? `(${friendRecs.count})` : ''}</Muted>
          {recs.length === 0 ? (
            <View>
              <Muted>아직 추천할 친구가 없어요.</Muted>
              <Text style={{ color: theme.colors.subtext, fontSize: 13, marginTop: 2 }}>
                오늘 미션을 1개 완료하면 비슷한 레벨의 학습자를 추천해드려요.
              </Text>
              <View style={{ marginTop: 10 }}>
                <Button title="오늘의 미션 하러 가기" onPress={() => app.navigate('home')} />
              </View>
            </View>
          ) : (
            recs.slice(0, 6).map((r) => (
              <View key={r.learnerId} style={{ paddingVertical: 8, borderTopWidth: 1, borderTopColor: theme.colors.border }}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text style={{ color: theme.colors.text, fontWeight: '700' }}>{learnerName(r.learnerId)}</Text>
                  <View style={{ width: 110 }}>
                    <Button
                      title={r.alreadyFriend ? '친구' : r.pendingInvite ? '초대됨' : '친구 초대'}
                      onPress={() => app.inviteFriend(r.learnerId)}
                      disabled={r.alreadyFriend || r.pendingInvite}
                      secondary={r.alreadyFriend || r.pendingInvite}
                    />
                  </View>
                </View>
                <Muted>{friendReason(r.reasonCodes, r.sharedSources)}</Muted>
                <Row>
                  <Pill label={`레벨 ${courseLevelLabel(r.profile.level)}`} />
                  <Pill label={`이번 주 ${r.weekXp} XP`} />
                  {r.lastActiveAt ? <Pill label="최근 학습" /> : null}
                </Row>
                {!r.alreadyFriend && (
                  <Text onPress={() => app.blockLearner(r.learnerId)} style={{ color: theme.colors.subtext, fontSize: 12, marginTop: 6 }}>
                    이 학습자 차단 · 추천 숨기기
                  </Text>
                )}
              </View>
            ))
          )}
        </Card>
      </Fade>

      {/* Blocked learners */}
      {(blocks.length > 0) && (
        <Fade delay={180}>
          <Card>
            <Muted>차단한 학습자 {blocks.length}명</Muted>
            {blocks.map((b) => (
              <View key={b.id} style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 6 }}>
                <Text style={{ color: theme.colors.text, fontWeight: '600' }}>{learnerName(b.blockedLearnerId)}</Text>
                <View style={{ width: 110 }}>
                  <Button title="차단 해제" onPress={() => app.unblockLearner(b.blockedLearnerId)} secondary />
                </View>
              </View>
            ))}
          </Card>
        </Fade>
      )}

    </View>
  );
}
