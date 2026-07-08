import React, { useEffect, useState } from 'react';
import { Text, TextInput, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { Button, Card, Fade, Muted, Pill, Row, Title } from '../components';
import { authApi } from '../api/auth';
import type { AppController } from '../store';
import type { AuthDevice } from '../../../../packages/shared/src/types';

const MODE_LABEL: Record<string, string> = {
  public_key_challenge_rs256: '공개키 서명 인증됨',
  signed_challenge_hmac: '암호 서명 인증됨 (개발 검증)',
  platform_verified: '플랫폼 인증됨',
  account_confirmed_not_platform_verified: '계정 확인됨 (기기 미검증)',
  not_verified: '미검증',
};

export function SecurityScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const real = app.apiInfo.mode === 'real';
  const [authed, setAuthed] = useState(authApi.isAuthed());
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [device, setDevice] = useState<AuthDevice | null>(null);
  const [devices, setDevices] = useState<AuthDevice[]>([]);

  const refreshDevices = async () => {
    try {
      const r = await authApi.devices();
      setDevices(r.devices);
      const cur = r.devices.find((d) => d.isCurrent) ?? r.devices[0] ?? null;
      if (cur) setDevice(cur);
    } catch { /* ignore */ }
  };

  useEffect(() => {
    void (async () => {
      const ok = await authApi.restore();
      setAuthed(ok);
      if (ok) await refreshDevices();
    })();
  }, []);

  const inputStyle = {
    backgroundColor: theme.colors.bg,
    borderColor: theme.colors.border,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    color: theme.colors.text,
    marginTop: 8,
  } as const;

  const run = async (fn: () => Promise<void>, okMsg?: string) => {
    if (busy) return;
    setBusy(true); setMsg(null);
    try { await fn(); if (okMsg) setMsg(okMsg); }
    catch (e) {
      const status = (e as { status?: number }).status;
      if (status === 401 && authed) {
        // session expired / device revoked — drop to re-login, never trust stale state
        await authApi.logout().catch(() => undefined);
        setAuthed(false); setDevice(null); setDevices([]);
        setMsg('세션이 만료됐어요. 다시 로그인해 주세요.');
      } else if (status === 401) {
        setMsg('이메일 또는 비밀번호를 확인해 주세요.');
      } else if (status === 409) {
        setMsg('이미 가입된 이메일이에요. 로그인해 주세요.');
      } else if (status === 429) {
        setMsg('시도가 너무 많아요. 잠시 후 다시 시도해 주세요.');
      } else {
        setMsg('네트워크 오류예요. 잠시 후 다시 시도해 주세요.');
      }
    } finally { setBusy(false); }
  };

  if (!real) {
    return (
      <View>
        <Fade><Muted>보안</Muted><Title>기기 신뢰 · 인증</Title></Fade>
        <Fade delay={60}><Card><Muted>기기 신뢰/인증은 실제 백엔드에 연결됐을 때 동작해요. (현재 데모 모드)</Muted></Card></Fade>
        <Fade delay={100}><Button title="설정으로" onPress={() => app.navigate('settings')} secondary /></Fade>
      </View>
    );
  }

  return (
    <View>
      <Fade>
        <Muted>보안</Muted>
        <Title>기기 신뢰 · 인증</Title>
        <Muted>이 기기를 계정에 안전하게 연결하고 암호 서명으로 인증해요.</Muted>
      </Fade>

      {msg && (
        <Fade delay={20}>
          <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
            <Text style={{ color: theme.colors.accentDark, fontWeight: '700' }}>{msg}</Text>
          </Card>
        </Fade>
      )}

      {!authed ? (
        <Fade delay={60}>
          <Card>
            <Muted>계정으로 기기 등록</Muted>
            <TextInput style={inputStyle} placeholder="이메일" placeholderTextColor={theme.colors.subtext} autoCapitalize="none" keyboardType="email-address" value={email} onChangeText={setEmail} />
            <TextInput style={inputStyle} placeholder="비밀번호 (8자 이상)" placeholderTextColor={theme.colors.subtext} secureTextEntry value={password} onChangeText={setPassword} />
            <View style={{ flexDirection: 'row', gap: 10, marginTop: 12 }}>
              <View style={{ flex: 1 }}>
                <Button title="로그인" onPress={() => run(async () => { await authApi.login(email.trim(), password); setAuthed(true); await refreshDevices(); }, '로그인했어요.')} disabled={busy || !email || !password} secondary />
              </View>
              <View style={{ flex: 1 }}>
                <Button title="가입" onPress={() => run(async () => { await authApi.register(email.trim(), password); setAuthed(true); await refreshDevices(); }, '가입하고 이 기기를 연결했어요.')} disabled={busy || !email || !password} />
              </View>
            </View>
            <Muted>가입 시 이 기기가 세션에 바인딩돼요.</Muted>
          </Card>
        </Fade>
      ) : (
        <>
          <Fade delay={60}>
            <Card>
              <Row>
                <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text }}>이 기기</Text>
                <Pill
                  label={device?.trusted ? '신뢰됨' : authApi.attestationAvailable() ? '미신뢰' : '계정 연결됨'}
                  color={device?.trusted ? theme.colors.good : authApi.attestationAvailable() ? undefined : theme.colors.accent}
                />
              </Row>
              <Muted>
                {device?.trusted
                  ? `상태: ${MODE_LABEL[device.verificationMode] ?? device.verificationMode}${device.attestationVerified ? ' · 서명 검증됨 ✓' : ''}`
                  : authApi.attestationAvailable()
                    ? '상태: 미검증 — 아래에서 이 기기를 인증하세요.'
                    : '이 기기가 계정에 연결됐어요. 기기 서명 인증은 이 빌드에서 제공되지 않아요(보안 경고 아님).'}
              </Muted>
              {authApi.attestationAvailable() ? (
                <>
                  <View style={{ marginTop: 12 }}>
                    <Button
                      title="이 기기 인증하기"
                      onPress={() => run(async () => { const d = await authApi.attestDevice(); setDevice(d); await refreshDevices(); }, '기기 인증 완료 — 서명이 검증됐어요.')}
                      disabled={busy}
                    />
                  </View>
                  <Muted>
                    {authApi.publicKeyAvailable()
                      ? '이 기기에서 만든 개인키로 서버 챌린지에 서명해 인증해요(공개키 RS256 — 공유 비밀 없음). 실제 출시에서는 Apple App Attest / Play Integrity / WebAuthn으로 한층 강화돼요.'
                      : '개발 검증(signed_challenge HMAC)으로 서버 챌린지를 서명해 확인해요. 실제 출시에서는 네이티브 기기 인증으로 대체돼요.'}
                  </Muted>
                </>
              ) : (
                <View style={{ marginTop: 10, padding: 12, borderRadius: 12, backgroundColor: theme.colors.bg }}>
                  <Text style={{ color: theme.colors.text, fontWeight: '700' }}>이 빌드에서는 기기 인증이 계정 확인까지만 동작해요.</Text>
                  <Muted>암호 서명 기기 인증은 네이티브 앱(Apple App Attest / Play Integrity / WebAuthn)에서 제공돼요.</Muted>
                </View>
              )}
            </Card>
          </Fade>

          {devices.length > 0 && (
            <Fade delay={100}>
              <Card>
                <Muted>등록된 기기 {devices.length}대</Muted>
                {devices.map((d) => (
                  <View key={d.id} style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 }}>
                    <Text style={{ color: theme.colors.text }}>{d.deviceLabel || d.platform || '기기'}{d.isCurrent ? ' (이 기기)' : ''}</Text>
                    <Text style={{ color: d.attestationVerified ? theme.colors.good : theme.colors.subtext, fontSize: 13 }}>
                      {d.attestationVerified ? '서명 검증' : d.trustStatus === 'trusted' ? '신뢰됨' : authApi.attestationConfigured() ? '미검증' : '계정 연결'}
                    </Text>
                  </View>
                ))}
              </Card>
            </Fade>
          )}

          <Fade delay={140}>
            <Button title="로그아웃" onPress={() => run(async () => { await authApi.logout(); setAuthed(false); setDevice(null); setDevices([]); }, '로그아웃했어요.')} secondary tone="bad" />
          </Fade>
        </>
      )}

      <Fade delay={180}><Button title="설정으로" onPress={() => app.navigate('settings')} secondary /></Fade>
    </View>
  );
}
