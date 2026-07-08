// Account auth + device-trust client. Separate from the X-Learner-Id `request`
// helper in client.ts: these endpoints require a real account session
// (Authorization: Bearer <accessToken>) and a device-bound session (X-Device-Id).
//
// Mirrors Codex's backend device-attestation flow exactly:
//   register/login(deviceId) -> Bearer + X-Device-Id
//   -> POST /v1/auth/devices/attestation/challenge {attestationProvider, attestationSubject}
//   -> sign HMAC-SHA256(secret, challenge.message)
//   -> POST /v1/auth/devices/trust {confirmation, attestationProvider, attestationSubject, evidence}
//   => attestationVerified:true, verificationMode:'signed_challenge_hmac'
//
// The HMAC `signed_challenge` provider is the backend's DEV/CI attestation path
// (shared secret). Production device trust uses native Apple App Attest / Google
// Play Integrity / WebAuthn — no client-held secret — which is out of scope here.
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE } from './client';
import { hmacSha256Hex } from '../crypto/hmacSha256';
import { getPublicJwk, publicKeyAttestationAvailable, signRs256 } from '../crypto/deviceKey';
import type {
  AuthDevice,
  AuthDeviceAttestationChallengeResponse,
  AuthDevicesResponse,
  AuthTokenResponse,
  AuthTrustDeviceResponse,
} from '../../../../packages/shared/src/types';

declare const __DEV__: boolean;

const ATTESTATION_SUBJECT = 'device-public-key-1';
const DEVICE_KEY = 'alp.auth.deviceId';
const TOKEN_KEY = 'alp.auth.accessToken';

// Dev/CI signed_challenge secret. SECURITY: EXPO_PUBLIC_* values are inlined into
// the JS bundle — a shared HMAC secret in a PRODUCTION build would be extractable
// and signatures forgeable. So this path is HARD-GATED to __DEV__: production
// builds carry no secret (attestationConfigured() === false) and rely on native
// attestation (Apple App Attest / Google Play Integrity / WebAuthn). Operational
// rule: never set EXPO_PUBLIC_DEVICE_ATTESTATION_SECRET for a production export.
const ATT_SECRET = __DEV__ ? (process.env.EXPO_PUBLIC_DEVICE_ATTESTATION_SECRET || '') : '';

let accessToken: string | null = null;
let deviceId: string | null = null;

async function ensureDeviceId(): Promise<string> {
  if (deviceId) return deviceId;
  const stored = await AsyncStorage.getItem(DEVICE_KEY);
  if (stored) return (deviceId = stored);
  const id = 'mobile_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
  await AsyncStorage.setItem(DEVICE_KEY, id);
  return (deviceId = id);
}

async function authFetch<T>(path: string, options?: RequestInit, withAuth = true): Promise<T> {
  const did = await ensureDeviceId();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Device-Id': did,
    ...((options?.headers as Record<string, string>) || {}),
  };
  if (withAuth && accessToken) headers.Authorization = `Bearer ${accessToken}`;
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = new Error(`auth ${path} failed: ${res.status}`);
    (err as Error & { status?: number }).status = res.status;
    throw err;
  }
  return (await res.json()) as T;
}

export const authApi = {
  isAuthed: () => !!accessToken,
  // Attestation is available if we can do asymmetric RS256 (no secret needed) OR
  // the dev HMAC secret is configured. Public-key is preferred + production-shaped.
  attestationAvailable: () => publicKeyAttestationAvailable() || ATT_SECRET.length > 0,
  publicKeyAvailable: () => publicKeyAttestationAvailable(),
  attestationConfigured: () => ATT_SECRET.length > 0,

  async restore(): Promise<boolean> {
    accessToken = await AsyncStorage.getItem(TOKEN_KEY);
    return !!accessToken;
  },

  async register(email: string, password: string): Promise<AuthTokenResponse> {
    const did = await ensureDeviceId();
    const r = await authFetch<AuthTokenResponse>(
      '/v1/auth/register',
      { method: 'POST', body: JSON.stringify({ email, password, deviceId: did, deviceLabel: 'mobile-app' }) },
      false,
    );
    accessToken = r.accessToken;
    await AsyncStorage.setItem(TOKEN_KEY, r.accessToken);
    return r;
  },

  async login(email: string, password: string): Promise<AuthTokenResponse> {
    const did = await ensureDeviceId();
    const r = await authFetch<AuthTokenResponse>(
      '/v1/auth/login',
      { method: 'POST', body: JSON.stringify({ email, password, deviceId: did, deviceLabel: 'mobile-app' }) },
      false,
    );
    accessToken = r.accessToken;
    await AsyncStorage.setItem(TOKEN_KEY, r.accessToken);
    return r;
  },

  async logout(): Promise<void> {
    try { await authFetch('/v1/auth/logout', { method: 'POST' }); } catch { /* ignore */ }
    accessToken = null;
    await AsyncStorage.removeItem(TOKEN_KEY);
  },

  me: () => authFetch<{ account: unknown; session: { deviceTrust?: unknown } }>('/v1/auth/me'),
  devices: () => authFetch<AuthDevicesResponse>('/v1/auth/devices'),

  // Preferred handshake: asymmetric RS256 public-key challenge (no shared secret).
  // Generates/persists a device RSA keypair, signs the server challenge with the
  // PRIVATE key, sends the public JWK; server verifies. Falls back to dev HMAC.
  async attestDevice(): Promise<AuthDevice> {
    if (publicKeyAttestationAvailable()) {
      const publicJwk = await getPublicJwk();
      if (publicJwk) {
        const subject = JSON.stringify(publicJwk);
        const challenge = await authFetch<AuthDeviceAttestationChallengeResponse>('/v1/auth/devices/attestation/challenge', {
          method: 'POST',
          body: JSON.stringify({ attestationProvider: 'public_key_challenge', attestationSubject: subject }),
        });
        const signature = await signRs256(challenge.message);
        if (signature) {
          const res = await authFetch<AuthTrustDeviceResponse>('/v1/auth/devices/trust', {
            method: 'POST',
            body: JSON.stringify({
              confirmation: 'trust-this-device',
              platform: 'mobile',
              deviceLabel: 'mobile-app',
              attestationProvider: 'public_key_challenge',
              attestationSubject: subject,
              evidence: { challengeId: challenge.challengeId, challenge: challenge.challenge, signature, algorithm: 'rs256', publicKeyJwk: publicJwk },
            }),
          });
          return res.device;
        }
      }
    }
    return this.attestThisDevice();
  },

  // Dev/CI HMAC handshake (shared secret). Fallback when public-key is unavailable.
  async attestThisDevice(): Promise<AuthDevice> {
    const challenge = await authFetch<AuthDeviceAttestationChallengeResponse>('/v1/auth/devices/attestation/challenge', {
      method: 'POST',
      body: JSON.stringify({ attestationProvider: 'signed_challenge', attestationSubject: ATTESTATION_SUBJECT }),
    });
    const signature = hmacSha256Hex(ATT_SECRET, challenge.message);
    const res = await authFetch<AuthTrustDeviceResponse>('/v1/auth/devices/trust', {
      method: 'POST',
      body: JSON.stringify({
        confirmation: 'trust-this-device',
        platform: 'mobile',
        deviceLabel: 'mobile-app',
        attestationProvider: 'signed_challenge',
        attestationSubject: ATTESTATION_SUBJECT,
        evidence: { challengeId: challenge.challengeId, challenge: challenge.challenge, signature, algorithm: 'hmac-sha256' },
      }),
    });
    return res.device;
  },
};
