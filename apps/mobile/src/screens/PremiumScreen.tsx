import React from 'react';
import { Text, View, Pressable } from 'react-native';
import type { AppController } from '../store';
import { useTheme } from '../ThemeContext';
import { Card, Button, Title, Muted, Pill, Fade } from '../components';
import { personaColor } from '../personaStyle';
import { APP_ABOUT, PLAN_FEATURES, PRIVACY_POINTS } from '../premium/premiumData';

const KO = {
  title: '소개·프리미엄·개인정보',
  aboutHeading: '앱 소개',
  diffHeading: '이 앱만의 차별점',
  compareHeading: '무료 vs 프리미엄',
  compareIntro: '지금은 무료 기능만 제공돼요. 프리미엄 항목은 준비 중입니다.',
  colFree: '무료',
  colPremium: '프리미엄',
  privacyHeading: '개인정보·음성 처리',
  soonTitle: '프리미엄은 준비 중이에요',
  soonBody:
    '아직 앱 안에서 결제할 수 없어요. 정직하게 말하면, 아래 버튼은 구매가 아니라 출시 알림 신청일 뿐이에요. 결제 수단이 열리면 이 화면에서 안내할게요.',
  notify: '출시되면 알림 받기',
  notified: '알림 신청 완료 (데모)',
  home: '홈으로',
};

export function PremiumScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const accent = personaColor(app.selectedPersonaId);
  const [notified, setNotified] = React.useState(false);

  React.useEffect(() => {
    app.track('premium_viewed');
  }, [app]);

  const onNotify = () => {
    setNotified(true);
    app.track('premium_interest');
  };

  return (
    <View>
      <Fade>
        <Title>{KO.title}</Title>
      </Fade>

      {/* ---- About + differentiators ---- */}
      <Fade delay={40}>
        <Card style={{ borderColor: accent, borderWidth: 2 }}>
          <Text style={{ fontSize: 12, fontWeight: '800', color: accent, marginBottom: 6 }}>{KO.aboutHeading}</Text>
          <Text style={{ fontSize: 19, fontWeight: '800', color: theme.colors.text, marginBottom: 8, lineHeight: 26 }}>
            {APP_ABOUT.tagline}
          </Text>
          <Muted>{APP_ABOUT.summary}</Muted>

          <Text style={{ fontSize: 13, fontWeight: '800', color: theme.colors.accentDark, marginTop: 16, marginBottom: 4 }}>
            {KO.diffHeading}
          </Text>
          {APP_ABOUT.diffs.map((d) => (
            <View key={d.title} style={{ flexDirection: 'row', alignItems: 'flex-start', marginTop: 12 }}>
              <View
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: 10,
                  backgroundColor: theme.colors.chip,
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginRight: 12,
                }}
              >
                <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.chipText }}>{d.icon}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 15, fontWeight: '700', color: theme.colors.text, marginBottom: 2 }}>{d.title}</Text>
                <Text style={{ fontSize: 13, color: theme.colors.subtext, lineHeight: 20 }}>{d.body}</Text>
              </View>
            </View>
          ))}
        </Card>
      </Fade>

      {/* ---- Free vs Premium comparison table ---- */}
      <Fade delay={80}>
        <Card>
          <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text, marginBottom: 4 }}>{KO.compareHeading}</Text>
          <Muted>{KO.compareIntro}</Muted>

          <View style={{ flexDirection: 'row', marginTop: 14, marginBottom: 8, alignItems: 'center' }}>
            <Text style={{ flex: 1, fontSize: 12, fontWeight: '700', color: theme.colors.subtext }}>{' '}</Text>
            <Text style={{ width: 64, textAlign: 'center', fontSize: 12, fontWeight: '800', color: theme.colors.subtext }}>
              {KO.colFree}
            </Text>
            <Text style={{ width: 72, textAlign: 'center', fontSize: 12, fontWeight: '800', color: accent }}>{KO.colPremium}</Text>
          </View>

          {PLAN_FEATURES.map((f, i) => (
            <View
              key={f.title}
              style={{
                flexDirection: 'row',
                alignItems: 'center',
                paddingVertical: 10,
                borderTopWidth: i === 0 ? 1 : 0,
                borderBottomWidth: 1,
                borderColor: theme.colors.border,
              }}
            >
              <View style={{ flex: 1, paddingRight: 8 }}>
                <Text style={{ fontSize: 14, color: theme.colors.text, lineHeight: 20 }}>{f.title}</Text>
                {f.note ? <Text style={{ fontSize: 11, color: theme.colors.subtext, marginTop: 2 }}>{f.note}</Text> : null}
              </View>
              <View style={{ width: 64, alignItems: 'center' }}>
                <Check on={f.free} onColor={theme.colors.good} offColor={theme.colors.border} />
              </View>
              <View style={{ width: 72, alignItems: 'center' }}>
                <Check on={f.premium} onColor={accent} offColor={theme.colors.border} />
              </View>
            </View>
          ))}
        </Card>
      </Fade>

      {/* ---- Privacy / voice processing ---- */}
      <Fade delay={120}>
        <Card>
          <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text, marginBottom: 10 }}>{KO.privacyHeading}</Text>
          {PRIVACY_POINTS.map((p, i) => (
            <View
              key={p.title}
              style={{
                flexDirection: 'row',
                alignItems: 'flex-start',
                marginTop: i === 0 ? 0 : 14,
              }}
            >
              <View
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: 10,
                  backgroundColor: theme.colors.accentSoft,
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginRight: 12,
                }}
              >
                <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.accentDark }}>{p.icon}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 15, fontWeight: '700', color: theme.colors.text, marginBottom: 2 }}>{p.title}</Text>
                <Text style={{ fontSize: 13, color: theme.colors.subtext, lineHeight: 20 }}>{p.body}</Text>
              </View>
            </View>
          ))}
        </Card>
      </Fade>

      {/* ---- Honest "coming soon" note (no fake purchase) ---- */}
      <Fade delay={160}>
        <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: accent }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
            <Pill label="준비 중" color={accent} />
          </View>
          <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text, marginBottom: 6 }}>{KO.soonTitle}</Text>
          <Text style={{ fontSize: 14, color: theme.colors.text, lineHeight: 22, marginBottom: 12 }}>{KO.soonBody}</Text>
          {notified ? (
            <View
              style={{
                borderRadius: theme.radius.md,
                borderWidth: 1,
                borderColor: theme.colors.good,
                paddingVertical: 12,
                alignItems: 'center',
              }}
            >
              <Text style={{ color: theme.colors.good, fontWeight: '800', fontSize: 15 }}>{KO.notified}</Text>
            </View>
          ) : (
            <Button title={KO.notify} onPress={onNotify} color={accent} />
          )}
        </Card>
      </Fade>

      <View style={{ marginTop: 4, marginBottom: 24 }}>
        <Button title={KO.home} secondary onPress={() => app.navigate('home')} />
      </View>
    </View>
  );
}

function Check({ on, onColor, offColor }: { on: boolean; onColor: string; offColor: string }) {
  return (
    <View
      accessible
      accessibilityLabel={on ? '포함' : '미포함'}
      style={{
        width: 22,
        height: 22,
        borderRadius: 11,
        borderWidth: 1.5,
        borderColor: on ? onColor : offColor,
        backgroundColor: on ? onColor : 'transparent',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Text style={{ fontSize: 13, fontWeight: '900', color: on ? '#fff' : offColor }}>{on ? '○' : '-'}</Text>
    </View>
  );
}
