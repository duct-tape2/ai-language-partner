import React, { useState } from 'react';
import { Switch, Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { STRINGS } from '../i18n';
import { SHOW_DEV_TOOLS } from '../devConfig';
import { Button, Card, Fade, Muted, Press, Title } from '../components';
import type { AppController } from '../store';

function Toggle({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  const { theme } = useTheme();
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 10 }}>
      <Text style={{ fontSize: 15, color: theme.colors.text }}>{label}</Text>
      <Switch value={value} onValueChange={onChange} trackColor={{ true: theme.colors.accent, false: theme.colors.track }} thumbColor="#fff" />
    </View>
  );
}

function Stepper({ label, value, suffix, onDec, onInc }: { label: string; value: string; suffix?: string; onDec: () => void; onInc: () => void }) {
  const { theme } = useTheme();
  const btn = (t: string, fn: () => void, a11y: string) => (
    <Press onPress={fn} accessibilityLabel={a11y}>
      <View style={{ width: 40, height: 40, borderRadius: 10, borderWidth: 1, borderColor: theme.colors.border, alignItems: 'center', justifyContent: 'center', backgroundColor: theme.colors.surface }}>
        <Text style={{ fontSize: 20, color: theme.colors.accentDark, fontWeight: '800' }}>{t}</Text>
      </View>
    </Press>
  );
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 10 }}>
      <Text style={{ fontSize: 15, color: theme.colors.text }}>{label}</Text>
      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
        {btn('−', onDec, `${label} 줄이기`)}
        <Text style={{ minWidth: 64, textAlign: 'center', fontSize: 15, fontWeight: '700', color: theme.colors.text }}>
          {value}
          {suffix ?? ''}
        </Text>
        {btn('+', onInc, `${label} 늘리기`)}
      </View>
    </View>
  );
}

export function SettingsScreen({ app }: { app: AppController }) {
  const { theme, mode, toggleMode, reducedMotion, setReducedMotion } = useTheme();
  const { entitlement, settings } = app;
  const [confirmReset, setConfirmReset] = useState(false);
  const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
  const s = STRINGS.settings;
  const planLabels: Record<string, string> = {
    master_sandbox: s.planMasterSandbox,
    free: s.planFree,
    basic: s.planBasic,
    plus: s.planPlus,
    pro: s.planPro,
  };
  const planLabel = app.demoMode ? s.planDemo : planLabels[entitlement?.plan ?? 'free'] ?? s.planFree;
  const voiceLine = app.demoMode ? s.demoVoiceLine : entitlement?.premiumVoices ? s.premiumVoices : s.basicVoices;

  return (
    <View>
      <Fade>
        <Title>{s.title}</Title>
      </Fade>

      <Fade delay={40}>
        <Card>
          <Muted>{s.language}</Muted>
          <View style={{ flexDirection: 'row', marginTop: 6 }}>
            <View style={{ flex: 1, marginRight: 6 }}>
              <Button
                title={s.languageKo}
                onPress={() => app.updateSettings({ uiLocale: 'ko' })}
                secondary={settings.uiLocale !== 'ko'}
              />
            </View>
            <View style={{ flex: 1, marginLeft: 6 }}>
              <Button
                title={s.languageZhHant}
                onPress={() => app.updateSettings({ uiLocale: 'zh-Hant' })}
                secondary={settings.uiLocale !== 'zh-Hant'}
              />
            </View>
          </View>
        </Card>
      </Fade>

      <Fade delay={60}>
        <Card>
          <Muted>{s.appearance}</Muted>
          <Toggle label={s.darkMode} value={mode === 'dark'} onChange={toggleMode} />
          <Toggle label={s.reducedMotion} value={reducedMotion} onChange={setReducedMotion} />
        </Card>
      </Fade>

      <Fade delay={100}>
        <Card>
          <Muted>{s.learning}</Muted>
          <Stepper
            label={s.ttsSpeed}
            value={settings.ttsSpeed.toFixed(2)}
            suffix="x"
            onDec={() => app.updateSettings({ ttsSpeed: clamp(+(settings.ttsSpeed - 0.1).toFixed(2), 0.6, 1.3) })}
            onInc={() => app.updateSettings({ ttsSpeed: clamp(+(settings.ttsSpeed + 0.1).toFixed(2), 0.6, 1.3) })}
          />
          <Stepper
            label={s.dailyGoal}
            value={`${settings.dailyGoal}`}
            onDec={() => app.updateSettings({ dailyGoal: clamp(settings.dailyGoal - 1, 1, 50) })}
            onInc={() => app.updateSettings({ dailyGoal: clamp(settings.dailyGoal + 1, 1, 50) })}
          />
          <Stepper
            label={s.reviewCap}
            value={`${settings.reviewCap}`}
            onDec={() => app.updateSettings({ reviewCap: clamp(settings.reviewCap - 5, 5, 100) })}
            onInc={() => app.updateSettings({ reviewCap: clamp(settings.reviewCap + 5, 5, 100) })}
          />
          <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 10 }}>
            <Text style={{ fontSize: 15, color: theme.colors.text }}>{s.reminder}</Text>
            <Text style={{ fontSize: 15, fontWeight: '700', color: theme.colors.accentDark }}>{settings.reminderTime}</Text>
          </View>
        </Card>
      </Fade>

      <Fade delay={140}>
        <Card>
          <Muted>{s.plan}</Muted>
          <Text style={{ fontSize: 20, fontWeight: '800', color: theme.colors.text, marginTop: 2 }}>{planLabel}</Text>
          <Muted>{voiceLine}</Muted>
        </Card>
      </Fade>

      {app.socialSettings && (
        <Fade delay={160}>
          <Card>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
              <Muted>{s.socialPrivacy}</Muted>
              {app.socialSaveState !== 'idle' && (
                <Text style={{ fontSize: 12, fontWeight: '700', color: app.socialSaveState === 'error' ? theme.colors.bad : app.socialSaveState === 'saving' ? theme.colors.subtext : theme.colors.good }}>
                  {app.socialSaveState === 'saving' ? s.saving : app.socialSaveState === 'saved' ? s.saved : s.saveFailed}
                </Text>
              )}
            </View>
            <Toggle
              label={s.discoverable}
              value={app.socialSettings.discoverable}
              onChange={(v) => app.updateSocial({ discoverable: v, allowFriendInvites: app.socialSettings!.allowFriendInvites, showWeeklyXp: app.socialSettings!.showWeeklyXp })}
            />
            <Toggle
              label={s.allowFriendInvites}
              value={app.socialSettings.allowFriendInvites}
              onChange={(v) => app.updateSocial({ discoverable: app.socialSettings!.discoverable, allowFriendInvites: v, showWeeklyXp: app.socialSettings!.showWeeklyXp })}
            />
            <Toggle
              label={s.showWeeklyXp}
              value={app.socialSettings.showWeeklyXp}
              onChange={(v) => app.updateSocial({ discoverable: app.socialSettings!.discoverable, allowFriendInvites: app.socialSettings!.allowFriendInvites, showWeeklyXp: v })}
            />
            {app.reputation && (() => {
              const rep = app.reputation;
              // Non-aggressive account states: 제한됨 / 검토 중 / 양호·보통.
              const restricted = !rep.leaderboardEligible;
              const underReview = rep.reviewRecommended;
              const label = restricted ? s.accountRestricted : underReview ? s.accountReview : rep.riskBand === 'medium' ? s.accountNormal : s.accountGood;
              const tone = restricted ? theme.colors.bad : underReview ? theme.colors.gold : theme.colors.good;
              const note = restricted
                ? s.accountRestrictedNote
                : underReview
                  ? s.accountReviewNote
                  : s.accountGoodNote;
              return (
                <View style={{ marginTop: 6, borderTopWidth: 1, borderTopColor: theme.colors.border, paddingTop: 8 }}>
                  <Text style={{ fontSize: 14, color: theme.colors.text }}>
                    {s.accountStatus}: <Text style={{ fontWeight: '800', color: tone }}>{label}</Text>
                  </Text>
                  <Muted>{note}</Muted>
                  <Text onPress={() => app.navigate('friends')} style={{ color: theme.colors.subtext, fontSize: 13, fontWeight: '700', marginTop: 6, textDecorationLine: 'underline' }}>
                    {s.manageBlocked(app.socialBlocks?.count ?? 0)}
                  </Text>
                </View>
              );
            })()}
          </Card>
        </Fade>
      )}

      <Fade delay={175}>
        <Card>
          <Muted>{s.security}</Muted>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 2 }}>
            <Text style={{ fontSize: 15, fontWeight: '700', color: theme.colors.text }}>{s.deviceTrust}</Text>
            <View style={{ width: 110 }}>
              <Button title={s.open} onPress={() => app.navigate('security')} secondary />
            </View>
          </View>
          <Muted>{s.deviceTrustDesc}</Muted>
        </Card>
      </Fade>

      {/* Developer diagnostics — only in dev builds (__DEV__). Never shipped to users. */}
      {SHOW_DEV_TOOLS && (
        <Fade delay={180}>
          <Card style={{ borderStyle: 'dashed' }}>
            <Muted>개발자 (디버그 전용)</Muted>
            <Text style={{ fontSize: 13, color: theme.colors.subtext }}>API: {app.apiInfo.mode} · {app.apiInfo.base}</Text>
            <Muted>health: {app.healthText}</Muted>
            <Button title="Backend health check" onPress={app.checkHealth} secondary />
            <Button title="로컬 데이터 내보내기(콘솔)" onPress={async () => console.log(await app.exportData())} secondary />
          </Card>
        </Fade>
      )}

      <Fade delay={220}>
        {confirmReset ? (
          <Card style={{ borderColor: theme.colors.bad, borderWidth: 1.5 }}>
            <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.bad }}>{s.resetConfirmTitle}</Text>
            <Muted>{s.resetConfirmBody}</Muted>
            <View style={{ flexDirection: 'row', marginTop: 6 }}>
              <View style={{ flex: 1, marginRight: 6 }}>
                <Button title={s.cancel} onPress={() => setConfirmReset(false)} secondary />
              </View>
              <View style={{ flex: 1, marginLeft: 6 }}>
                <Button title={s.delete} onPress={() => { setConfirmReset(false); void app.resetData(); }} tone="bad" />
              </View>
            </View>
          </Card>
        ) : (
          <Button title={s.reset} onPress={() => setConfirmReset(true)} tone="bad" secondary />
        )}
      </Fade>
    </View>
  );
}
