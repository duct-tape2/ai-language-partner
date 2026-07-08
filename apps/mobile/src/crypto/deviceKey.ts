// RS256 device key for asymmetric device attestation (Codex `public_key_challenge`).
// The PRIVATE key never leaves the device; only the public JWK is sent to the
// server, which verifies the RS256 signature. Unlike the HMAC dev path there is
// NO shared secret, so nothing forgeable ships in the bundle — this is the secure,
// production-shaped attestation path (a step toward WebAuthn / platform attest).
//
// Uses Web Crypto (crypto.subtle), available in the web build and Node test. On
// bare native RN a SubtleCrypto polyfill (or expo-crypto/native keystore) is needed;
// publicKeyAttestationAvailable() reports false there so the UI degrades cleanly.
import AsyncStorage from '@react-native-async-storage/async-storage';

const PRIV_KEY = 'alp.auth.devicePrivateJwk';
const PUB_KEY = 'alp.auth.devicePublicJwk';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function subtle(): any | null {
  const c: any = (globalThis as any).crypto; // eslint-disable-line @typescript-eslint/no-explicit-any
  return c && c.subtle ? c.subtle : null;
}

export function publicKeyAttestationAvailable(): boolean {
  return !!subtle() && typeof (globalThis as any).btoa === 'function'; // eslint-disable-line @typescript-eslint/no-explicit-any
}

const ALGO = { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' } as const;

async function loadOrCreateKeyPair(): Promise<{ publicJwk: Record<string, unknown>; privateKey: unknown } | null> {
  const s = subtle();
  if (!s) return null;
  const [storedPriv, storedPub] = await Promise.all([AsyncStorage.getItem(PRIV_KEY), AsyncStorage.getItem(PUB_KEY)]);
  if (storedPriv && storedPub) {
    const privateKey = await s.importKey('jwk', JSON.parse(storedPriv), ALGO, false, ['sign']);
    return { publicJwk: JSON.parse(storedPub), privateKey };
  }
  const kp = await s.generateKey(
    { name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' },
    true,
    ['sign', 'verify'],
  );
  const privJwk = await s.exportKey('jwk', kp.privateKey);
  const pubJwk = await s.exportKey('jwk', kp.publicKey);
  pubJwk.use = 'sig';
  pubJwk.alg = 'RS256';
  await AsyncStorage.setItem(PRIV_KEY, JSON.stringify(privJwk));
  await AsyncStorage.setItem(PUB_KEY, JSON.stringify(pubJwk));
  const privateKey = await s.importKey('jwk', privJwk, ALGO, false, ['sign']);
  return { publicJwk: pubJwk, privateKey };
}

function b64url(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  let bin = '';
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return (globalThis as any).btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); // eslint-disable-line @typescript-eslint/no-explicit-any
}

export async function getPublicJwk(): Promise<Record<string, unknown> | null> {
  const kp = await loadOrCreateKeyPair();
  return kp ? kp.publicJwk : null;
}

// RS256 sign the canonical challenge message → base64url signature.
export async function signRs256(message: string): Promise<string | null> {
  const s = subtle();
  const kp = await loadOrCreateKeyPair();
  if (!s || !kp) return null;
  const data = new TextEncoder().encode(message);
  const sig: ArrayBuffer = await s.sign({ name: 'RSASSA-PKCS1-v1_5' }, kp.privateKey, data);
  return b64url(sig);
}
