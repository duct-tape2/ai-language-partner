// F1. Pack manager. The backend serves packs ZIP-ONLY (GET /v1/dialogue/packs/
// {personaId}/{packVersion}.zip — no per-file route), so real mode downloads the zip
// and unzips it in-app with fflate (Expo managed has no native unzip). Mock mode
// loads a bundled fixture and speaks lines via device TTS.
import { Platform } from 'react-native';
import * as FileSystem from 'expo-file-system';
import { unzipSync } from 'fflate';
import { API_BASE, USE_MOCK } from '../api/client';
import { joinApiUrl } from '../api/url';
import { latestPerPersona } from './packVersion';
import fixtureStory from '../../assets/dialogue_fixture/yui/v1/story.json';
import fixtureManifest from '../../assets/dialogue_fixture/yui/v1/manifest.json';
import type { DialogueManifest, DialoguePackSummary, DialogueStory, LineCategory, LoadedPack, ManifestAudioEntry } from './types';

export type PackState = 'idle' | 'downloading' | 'ready' | 'updating' | 'error';

const FIXTURE_SUMMARY: DialoguePackSummary = {
  personaId: 'yui',
  packVersion: 'v1',
  topics: ['greetings_intro'],
  levels: ['N5'],
};

export async function listPacks(): Promise<DialoguePackSummary[]> {
  if (USE_MOCK) return [FIXTURE_SUMMARY];
  const res = await fetch(joinApiUrl(API_BASE, '/v1/dialogue/packs'), { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new Error(`listPacks failed: ${res.status}`);
  const arr = (await res.json()) as DialoguePackSummary[];
  return latestPerPersona(Array.isArray(arr) ? arr : [], {
    onInvalid: (pack, reason) => console.warn(`[dialogue] Ignoring pack ${pack.personaId}/${pack.packVersion}: ${reason}`),
  });
}

function buildAudioIndex(manifest: DialogueManifest): Record<string, ManifestAudioEntry> {
  const idx: Record<string, ManifestAudioEntry> = {};
  for (const arr of [manifest.audio, manifest.filler, manifest.confirm, manifest.fallback]) {
    for (const e of arr ?? []) idx[e.lineId] = e;
  }
  return idx;
}

export async function loadPack(personaId: string, packVersion: string): Promise<LoadedPack> {
  if (USE_MOCK) {
    const manifest = fixtureManifest as unknown as DialogueManifest;
    return {
      personaId: 'yui',
      packVersion: 'v1',
      story: fixtureStory as unknown as DialogueStory,
      manifest,
      audioIndex: buildAudioIndex(manifest),
      audioBytes: null,
      mock: true,
    };
  }

  clearAudioCache(); // release the previous pack's object URLs / cache keys before loading a new one
  const url = joinApiUrl(API_BASE, `/v1/dialogue/packs/${encodeURIComponent(personaId)}/${encodeURIComponent(packVersion)}.zip`);
  const res = await fetch(url, { headers: { Accept: 'application/zip' } });
  if (!res.ok) throw new Error(`pack zip ${personaId}/${packVersion} failed: ${res.status}`);
  const buf = new Uint8Array(await res.arrayBuffer());
  // Synchronous unzip: fflate's async unzip is Web Worker-backed and Workers do NOT
  // exist on React Native (Hermes) — it would crash on native. The pack loads once
  // behind a "준비 중" spinner, so a brief synchronous decompress is acceptable.
  const files = unzipSync(buf);

  const manifestBytes = files['manifest.json'];
  const storyBytes = files['story.json'];
  if (!manifestBytes || !storyBytes) throw new Error('pack zip missing manifest.json/story.json');
  const manifest = JSON.parse(decodeUtf8(manifestBytes)) as DialogueManifest;
  const story = JSON.parse(decodeUtf8(storyBytes)) as DialogueStory;

  const audioBytes: Record<string, Uint8Array> = {};
  for (const name of Object.keys(files)) {
    if (name.startsWith('audio/') && name.endsWith('.wav')) {
      const lineId = name.slice('audio/'.length, -'.wav'.length);
      audioBytes[lineId] = files[name];
    }
  }

  return { personaId, packVersion, story, manifest, audioIndex: buildAudioIndex(manifest), audioBytes, mock: false };
}

// Lazily materialize a playable URI for a line's pre-synthesized audio.
// Returns null when there is no audio (fixture) → caller speaks the text via TTS.
const uriCache = new Map<string, string>();

// Release web object URLs and reset the cache (called when a new pack loads).
export function clearAudioCache(): void {
  if (Platform.OS === 'web' && typeof URL !== 'undefined' && URL.revokeObjectURL) {
    for (const u of uriCache.values()) {
      if (u.startsWith('blob:')) {
        try {
          URL.revokeObjectURL(u);
        } catch {
          // ignore
        }
      }
    }
  }
  uriCache.clear();
}

export async function playableUri(pack: LoadedPack, lineId: string): Promise<string | null> {
  if (!pack.audioBytes) return null;
  const bytes = pack.audioBytes[lineId];
  if (!bytes) return null;
  const key = `${pack.personaId}_${pack.packVersion}_${lineId}`;
  const cached = uriCache.get(key);
  if (cached) return cached;

  if (Platform.OS === 'web') {
    if (typeof URL === 'undefined' || !URL.createObjectURL) return null;
    // Copy into a fresh ArrayBuffer-backed view for Blob.
    const copy = bytes.slice();
    const url = URL.createObjectURL(new Blob([copy], { type: 'audio/wav' }));
    uriCache.set(key, url);
    return url;
  }

  if (!FileSystem.cacheDirectory) return null;
  const dir = `${FileSystem.cacheDirectory}dtaudio/`;
  try {
    await FileSystem.makeDirectoryAsync(dir, { intermediates: true });
  } catch {
    // exists
  }
  const fileUri = `${dir}${key}.wav`;
  await FileSystem.writeAsStringAsync(fileUri, base64FromBytes(bytes), { encoding: FileSystem.EncodingType.Base64 });
  uriCache.set(key, fileUri);
  return fileUri;
}

export function lineEntry(pack: LoadedPack, lineId: string): ManifestAudioEntry | null {
  return pack.audioIndex[lineId] ?? null;
}

export function randomLineOfCategory(pack: LoadedPack, category: LineCategory): ManifestAudioEntry | null {
  const arr =
    category === 'filler' ? pack.manifest.filler : category === 'confirm' ? pack.manifest.confirm : category === 'fallback' ? pack.manifest.fallback : pack.manifest.audio;
  if (!arr || arr.length === 0) return null;
  return arr[Math.floor(Math.random() * arr.length)];
}

function decodeUtf8(bytes: Uint8Array): string {
  if (typeof TextDecoder !== 'undefined') return new TextDecoder('utf-8').decode(bytes);
  let s = '';
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
  return decodeURIComponent(escape(s));
}

const B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
function base64FromBytes(bytes: Uint8Array): string {
  let out = '';
  for (let i = 0; i < bytes.length; i += 3) {
    const b0 = bytes[i];
    const b1 = i + 1 < bytes.length ? bytes[i + 1] : 0;
    const b2 = i + 2 < bytes.length ? bytes[i + 2] : 0;
    out += B64[b0 >> 2];
    out += B64[((b0 & 3) << 4) | (b1 >> 4)];
    out += i + 1 < bytes.length ? B64[((b1 & 15) << 2) | (b2 >> 6)] : '=';
    out += i + 2 < bytes.length ? B64[b2 & 63] : '=';
  }
  return out;
}
