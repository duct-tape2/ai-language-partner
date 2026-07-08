// Local contract types for the '일상대화' (Daily Talk) dialogue-bank feature.
// These mirror the REAL shipped backend format (verified against apps/api source +
// on-disk packs, 2026-07-02): story.json = dialogue_bank_story_v1 (scenario/node
// graph, NOT ink), manifest.json = dialogue_bank_manifest_v1 (category arrays).
import type { FuriToken } from '../i18n';

export type LineCategory = 'dialogue' | 'filler' | 'confirm' | 'fallback';

// One entry in manifest.audio / .filler / .confirm / .fallback arrays.
export type ManifestAudioEntry = {
  lineId: string;
  path: string; // e.g. "audio/yui_greetings_intro_n5_a01.wav" (relative, inside the zip)
  category: LineCategory;
  text: string;
  voiceUsed?: string;
  engine?: string;
};

// manifest.json (dialogue_bank_manifest_v1)
export type DialogueManifest = {
  schemaVersion: string;
  personaId: string;
  packVersion: string;
  ttsProvider?: string;
  voiceUsed?: string;
  topics?: string[];
  levels?: string[];
  scenarioCount?: number;
  lineCount?: number;
  audioCount?: number;
  audio: ManifestAudioEntry[];
  filler: ManifestAudioEntry[];
  confirm: ManifestAudioEntry[];
  fallback: ManifestAudioEntry[];
  engineBaseUrl?: string;
  sourcePackVersion?: string;
};

// story.json (dialogue_bank_story_v1)
export type StoryChoice = { lineId: string; text: string; ko: string; nextNodeId: string | null };
export type StoryNode = {
  nodeId: string;
  assistantLineId: string;
  assistantText: string;
  assistantKo: string;
  choices: StoryChoice[];
};
export type StoryScenario = {
  scenarioId: string;
  personaId: string;
  packVersion: string;
  topicId: string;
  title: string;
  level: string;
  nodes: StoryNode[];
};
export type DialogueStory = {
  schemaVersion: string;
  personaId: string;
  packVersion: string;
  scenarios: StoryScenario[];
};

// GET /v1/dialogue/packs (bare array)
export type DialoguePackSummary = {
  personaId: string;
  packVersion: string;
  sizeBytes?: number;
  topics?: string[];
  levels?: string[];
  scenarioCount?: number;
  lineCount?: number;
  audioCount?: number;
};

// A pack ready for the runner. audioBytes holds unzipped wav bytes keyed by lineId
// (real packs); null in the bundled fixture (→ audioQueue speaks via device TTS).
export type LoadedPack = {
  personaId: string;
  packVersion: string;
  story: DialogueStory;
  manifest: DialogueManifest;
  audioIndex: Record<string, ManifestAudioEntry>; // every lineId → entry (all 4 categories)
  audioBytes: Record<string, Uint8Array> | null;
  mock: boolean;
};

export type MatchTier = 'match' | 'confirm' | 'fallback';
export type GlobalIntent = 'repeat' | 'hint' | 'quit' | 'slow';

// POST /v1/dialogue/match
export type DialogueMatchRequest = {
  personaId: string;
  packVersion: string;
  utterance: string;
  candidateLineIds: string[];
  globalIntents: true;
};

export type DialogueMatchResponse = {
  tier: MatchTier;
  matchedLineId: string | null;
  score: number;
  confirmLineId: string | null;
  globalIntent: GlobalIntent | null;
  latencyMs: number;
};

// GET /v1/voices (bare array; real items carry extra tuning fields — allowed as superset)
export type VoiceCatalogItem = {
  voiceId: string;
  engine: string;
  characterName: string;
  styleName: string;
  sampleUrl: string; // relative, e.g. "/v1/voices/samples/{voiceId}.wav" — resolve vs API_BASE
  personaId: string | null;
  creditText: string;
  [extra: string]: unknown;
};

// POST /v1/tts/synthesize response (subset we read; backend adds voiceUsed + contentType)
export type TtsPreviewResponse = {
  audioUrl: string | null;
  audioBase64: string | null;
  provider: string;
  voiceUsed?: string;
  spokenText: string;
  durationMs?: number;
};

// Runner-facing shapes (node-graph walk).
export type PersonaTurn = { lineId: string; text: string; ko: string };
export type Candidate = { index: number; lineId: string; text: string; ko: string; nextNodeId: string | null };
export type AdvanceResult = { persona: PersonaTurn | null; choices: Candidate[]; ended: boolean; nodeId: string | null };
