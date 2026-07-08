import React, { useState } from 'react';
import { Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { Button, Card, Fade, Muted, Row, Pill, Title } from '../components';
import { rewardDesc, rewardTitle } from '../labels';
import type { AppController } from '../store';

const CURRENCY_ICON: Record<string, string> = { coin: '🪙', gems: '💎', gem: '💎' };
const ccy = (k: string) => CURRENCY_ICON[k] ?? '🎟';

function remaining(expiresAt: string): string {
  const ms = new Date(expiresAt).getTime() - Date.now();
  if (Number.isNaN(ms) || ms <= 0) return '곧 만료';
  const m = Math.floor(ms / 60000);
  const s = Math.floor((ms % 60000) / 1000);
  return `${m}:${String(s).padStart(2, '0')} 남음`;
}

export function RewardShopScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const { shop } = app;
  const inventory = app.serverGam?.rewardInventory;
  const activeBoosts = app.serverGam?.activeXpBoosts ?? [];
  // Single wallet source: read balance from the gamification summary (same source
  // the Progress screen uses) so the gem count never disagrees across screens.
  const balances = inventory?.balances ?? shop?.balances ?? [{ currencyKey: 'gems', balance: 0 }];
  const totalBalance = balances.reduce((s, b) => s + b.balance, 0);
  const ownedQty = (key: string) => (inventory?.items ?? []).filter((i) => i.rewardKey === key).reduce((s, i) => s + i.quantity, 0);
  const isActive = (key: string) => activeBoosts.some((b) => b.rewardKey === key);

  const [busyKey, setBusyKey] = useState<string | null>(null);
  const guard = async (key: string, fn: () => Promise<void>) => {
    if (busyKey) return;
    setBusyKey(key);
    try {
      await fn();
    } finally {
      setBusyKey(null);
    }
  };

  return (
    <View>
      <Fade>
        <Muted>젬 상점</Muted>
        <Title>아이템 교환소</Title>
        <Row>
          {/* Always show the gem balance (items are priced in gems) so the wallet
              and prices use the same currency; other non-zero currencies after. */}
          <Pill label={`💎 ${balances.find((b) => b.currencyKey === 'gems' || b.currencyKey === 'gem')?.balance ?? 0}`} />
          {balances
            .filter((b) => b.currencyKey !== 'gems' && b.currencyKey !== 'gem' && b.balance > 0)
            .map((b) => (
              <Pill key={b.currencyKey} label={`${ccy(b.currencyKey)} ${b.balance}`} />
            ))}
        </Row>
        <Muted>미션 완료와 복습으로 젬을 모을 수 있어요.</Muted>
      </Fade>

      {app.shopMessage && (
        <Fade delay={20}>
          <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
            <Text style={{ color: theme.colors.accentDark, fontWeight: '700' }}>{app.shopMessage}</Text>
            <View style={{ marginTop: 8 }}>
              <Button title="확인" onPress={() => app.clearShopMessage()} secondary />
            </View>
          </Card>
        </Fade>
      )}

      {/* Active boosts */}
      {activeBoosts.length > 0 && (
        <Fade delay={40}>
          <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
            <Muted>사용 중인 부스트</Muted>
            {activeBoosts.map((b) => (
              <Text key={b.id} style={{ color: theme.colors.accentDark, fontWeight: '800' }}>
                ⚡ {Math.round(b.multiplier)}배 XP 부스트 사용 중 · {remaining(b.expiresAt)}
              </Text>
            ))}
          </Card>
        </Fade>
      )}

      {/* Shop items */}
      {(shop?.items ?? []).map((it, i) => {
        // Backend computes these per-item; fall back to the gamification inventory.
        const owned = it.currentInventoryQuantity || ownedQty(it.rewardKey);
        const isFreeze = it.rewardType === 'streak_freeze';
        // Only consumable boosts are "사용 중". A streak freeze is held/auto-used,
        // so it shows 보유/자동 보호 — never "사용 중".
        // Use the SAME source as the active-boost banner (serverGam.activeXpBoosts)
        // so the button "사용 중" and the banner are always consistent — never one
        // without the other.
        const active = !isFreeze && isActive(it.rewardKey);
        const busy = busyKey === it.rewardKey;
        const buyTitle = busy
          ? '처리 중...'
          : active
            ? '사용 중'
            : !it.available
              ? '준비 중'
              : !it.affordable
                ? '젬 부족'
                : `${it.priceAmount}젬으로 교환`;
        return (
          <Fade key={it.rewardKey} delay={60 + i * 50}>
            <Card>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                <View style={{ flex: 1, paddingRight: 10 }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <Text style={{ fontSize: 17, fontWeight: '800', color: theme.colors.text }}>{rewardTitle(it.rewardKey, it.title)}</Text>
                    {owned > 0 ? <Pill label={`보유 ${owned}`} /> : null}
                  </View>
                  {rewardDesc(it.rewardKey, it.description) ? <Muted>{rewardDesc(it.rewardKey, it.description)}</Muted> : null}
                  {it.rewardType === 'streak_freeze' ? <Muted>스트릭이 끊길 때 자동으로 사용돼요{owned > 0 ? ` · 보유 ${owned}개` : ''}.</Muted> : null}
                  <Text style={{ color: theme.colors.goldText, fontWeight: '800', marginTop: 4 }}>{ccy(it.priceCurrency)} {it.priceAmount}</Text>
                </View>
                <View style={{ width: 116 }}>
                  <Button
                    title={buyTitle}
                    onPress={() => guard(it.rewardKey, () => app.purchaseReward(it.rewardKey))}
                    disabled={busy || active || !it.available || !it.affordable}
                    secondary={active || !it.available || !it.affordable}
                  />
                  {it.rewardType === 'xp_boost' && owned > 0 && !active ? (
                    <View style={{ marginTop: 6 }}>
                      <Button title="사용하기" onPress={() => guard(`act-${it.rewardKey}`, () => app.activateBoost(it.rewardKey))} tone="good" secondary />
                    </View>
                  ) : null}
                </View>
              </View>
            </Card>
          </Fade>
        );
      })}

      {totalBalance === 0 && (
        <Fade delay={200}>
          <Muted>아직 젬이 없어요. 오늘의 미션·복습·발음 연습으로 XP와 젬을 모아 보상을 받아보세요.</Muted>
        </Fade>
      )}

    </View>
  );
}
