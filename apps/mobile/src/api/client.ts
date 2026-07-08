import {
  PERSONAS,
  PRACTICE_ROOMS,
  INITIAL_REVIEW_CARD,
  TODAY_PROGRESS,
  MASTER_ENTITLEMENT,
} from '../../../../packages/shared/src/fixtures';
import type {
  AchievementsSummary,
  Course,
  CreateConversationResponse,
  CreateTurnResponse,
  ActivateXpBoostResponse,
  Entitlement,
  LearnerReputationProfile,
  SocialBlockResponse,
  SocialBlocksResponse,
  SocialDiscoveryResponse,
  SocialSettings,
  SocialUnblockResponse,
  FriendInviteAcceptResponse,
  FriendInviteResponse,
  FriendQuestClaimResponse,
  FriendQuestsResponse,
  FriendRecommendationsResponse,
  FriendsSummary,
  GamificationSummary,
  LeagueStatus,
  LearnerProfile,
  MemorySummary,
  Persona,
  PracticeRoom,
  PronunciationScore,
  RecommendationsResponse,
  RemoveFriendResponse,
  RewardPurchaseResponse,
  RewardShopResponse,
  ReviewCard,
  SttResponse,
  TodayProgress,
  TtsResponse,
  UsageSummary,
  WeeklyLeaderboard,
} from '../../../../packages/shared/src/types';
import type { DialogueMatchRequest, DialogueMatchResponse, TtsPreviewResponse, VoiceCatalogItem } from '../dialogue/types';
import { joinApiUrl, normalizeApiBase } from './url';

// '' means same-origin relative paths (web demo served by the API itself).
// Trim trailing slashes so `${API_BASE}/v1/...` stays stable for env values like
// "https://example.com/" while preserving the same-origin empty string.
export const API_BASE = normalizeApiBase(process.env.EXPO_PUBLIC_API_BASE_URL);
export const USE_MOCK = process.env.EXPO_PUBLIC_USE_MOCK_API !== 'false';
export const apiMode = USE_MOCK ? 'mock' : 'real';
// Dev learner scope (backend uses X-Learner-Id in dev auth mode).
export const LEARNER_ID = process.env.EXPO_PUBLIC_LEARNER_ID || 'local-dev';

const MOCK_SPOKEN = '今日めっちゃ疲れた。';
const MOCK_STT = '今日めっちゃ疲れた';

/**
 * One request helper for the whole app.
 * - mock mode: returns the fixture-backed fallback immediately.
 * - real mode: hits API_BASE with X-Learner-Id scoping; on network/HTTP failure
 *   falls back to the fixture so the UX never dead-ends.
 */
async function request<T>(
  path: string,
  options?: RequestInit,
  fallback?: T,
  reqOpts?: { noFallbackInReal?: boolean },
): Promise<T> {
  if (USE_MOCK && fallback !== undefined) return fallback;
  try {
    const res = await fetch(joinApiUrl(API_BASE, path), {
      headers: { 'Content-Type': 'application/json', 'X-Learner-Id': LEARNER_ID, ...(options?.headers || {}) },
      ...options,
    });
    if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
    return (await res.json()) as T;
  } catch (error) {
    // In real mode, mutations / personal data must NOT silently fall back to a
    // fixture — that would fake success. Re-throw so the caller can surface it.
    if (!USE_MOCK && reqOpts?.noFallbackInReal) throw error;
    if (fallback !== undefined) return fallback;
    throw error;
  }
}

const post = (body: unknown): RequestInit => ({ method: 'POST', body: JSON.stringify(body) });

// Voice sample URLs from GET /v1/voices are relative (e.g. "/v1/voices/samples/x.wav").
export function resolveApiUrl(pathOrUrl: string): string {
  return /^https?:|^blob:|^data:/.test(pathOrUrl) ? pathOrUrl : joinApiUrl(API_BASE, pathOrUrl);
}

// Persona voice preview via the real Aivis-backed engine. Reads the extra `voiceUsed`
// field the backend returns (not part of the shared TtsResponse type).
export async function synthesizePersona(text: string, personaId: string): Promise<TtsPreviewResponse> {
  if (USE_MOCK) return { audioUrl: null, audioBase64: null, provider: 'mock', voiceUsed: 'mock', spokenText: text };
  const res = await fetch(joinApiUrl(API_BASE, '/v1/tts/synthesize'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Learner-Id': LEARNER_ID },
    body: JSON.stringify({ text, personaId, language: 'ja' }),
  });
  if (!res.ok) throw new Error(`TTS /v1/tts/synthesize failed: ${res.status}`);
  return (await res.json()) as TtsPreviewResponse;
}

// Multipart STT upload. The shared request() helper forces JSON content-type and
// JSON.stringify, so file upload needs its own path: build FormData and DO NOT set
// Content-Type (fetch adds the multipart boundary itself).
export type SttUploadFile = { uri: string; name?: string; type?: string } | Blob;

export async function transcribeAudioFile(
  file: SttUploadFile,
  hintLineIds: string[] = [],
  language = 'ja',
): Promise<SttResponse> {
  if (USE_MOCK) return { text: MOCK_STT, provider: 'mock', confidence: 0.82 };
  const form = new FormData();
  if (typeof Blob !== 'undefined' && file instanceof Blob) {
    form.append('file', file, 'audio.webm');
  } else {
    const f = file as { uri: string; name?: string; type?: string };
    if (/^(blob:|data:|https?:)/.test(f.uri)) {
      // Web: browser FormData stringifies a plain {uri} object to "[object Object]".
      // Fetch the blob: URI into a real Blob so the audio bytes are actually sent.
      const blob = await fetch(f.uri).then((r) => r.blob());
      form.append('file', blob, f.name ?? 'audio.webm');
    } else {
      // React Native: FormData accepts a {uri,name,type} part; cast through unknown for TS.
      form.append('file', { uri: f.uri, name: f.name ?? 'audio.m4a', type: f.type ?? 'audio/m4a' } as unknown as Blob);
    }
  }
  form.append('language', language);
  for (const id of hintLineIds) form.append('hintLineIds', id);
  const res = await fetch(joinApiUrl(API_BASE, '/v1/stt/transcribe'), {
    method: 'POST',
    headers: { 'X-Learner-Id': LEARNER_ID },
    body: form,
  });
  if (!res.ok) throw new Error(`STT /v1/stt/transcribe failed: ${res.status}`);
  return (await res.json()) as SttResponse;
}

// ---- mock fallbacks for the evolved (backend-only) surface ----
const mockCourse: Course = {
  id: 'jp_beginner_speaking_ko',
  title: '한국인을 위한 일본어 말하기 입문',
  targetLanguage: 'ja',
  nativeLanguage: 'ko',
  level: 'beginner',
  descriptionKo: '매일 3분, 감정·일상 표현부터 말하기.',
  units: [
    {
      id: 'unit_emotions',
      title: '감정 표현',
      order: 1,
      skillTags: ['감정표현', '친구말투'],
      lessons: [
        { id: 'lesson_tired', title: '피곤·지침', order: 1, practiceRoomIds: ['tired_today', 'mental_tired'] },
      ],
    },
  ],
};

const mockGamification: GamificationSummary = {
  xp: { learnerId: LEARNER_ID, todayXp: 0, weekXp: 0, totalXp: 0, eventCount: 0, weekStart: TODAY_PROGRESS.date },
  streak: { learnerId: LEARNER_ID, currentStreak: 1, longestStreak: 1, activeDays: 1, lastActiveDate: TODAY_PROGRESS.date, isActiveToday: true },
  dailyQuests: [],
  friends: { learnerId: LEARNER_ID, friends: [], incomingInvites: [], outgoingInvites: [], friendCount: 0 },
  friendQuests: [],
  rewardInventory: { items: [], activeXpBoosts: [], catalog: [], balances: [{ currencyKey: 'coin', balance: 0 }] },
  activeXpBoosts: [],
  weeklyLeaderboard: { weekStart: TODAY_PROGRESS.date, weekEnd: TODAY_PROGRESS.date, entries: [], currentLearnerRank: null, excludedLearnerCount: 0 },
  league: { currentTier: { key: 'bronze', name: 'Bronze', minWeeklyXp: 0 }, nextTier: { key: 'silver', name: 'Silver', minWeeklyXp: 200 }, weekXp: 0, progressToNextTier: 0, currentRank: null, weekStart: TODAY_PROGRESS.date },
  achievements: { awardedCount: 0, totalCount: 0, achievements: [], trackCount: 0, completedTrackCount: 0 },
  xpAbuseFlags: [],
};

export const api = {
  health: () => request('/health', undefined, { ok: true, projectId: 'mock' }),

  listPersonas: () => request<{ personas: Persona[] }>('/v1/personas', undefined, { personas: PERSONAS }),

  listPracticeRooms: () =>
    request<{ practiceRooms: PracticeRoom[] }>('/v1/practice-rooms', undefined, { practiceRooms: PRACTICE_ROOMS }),

  getPracticeRoom: (id: string) =>
    request<{ practiceRoom: PracticeRoom }>(`/v1/practice-rooms/${id}`, undefined, {
      practiceRoom: PRACTICE_ROOMS.find((r) => r.id === id) || PRACTICE_ROOMS[0],
    }),

  // ---- course catalog (new) ----
  listCourses: () => request<{ courses: Course[] }>('/v1/courses', undefined, { courses: [mockCourse] }),
  getCourse: (id: string) => request<{ course: Course }>(`/v1/courses/${id}`, undefined, { course: mockCourse }),

  createConversation: (personaId: string, practiceRoomId: string) =>
    request<CreateConversationResponse>('/v1/conversations', post({ personaId, practiceRoomId, mode: 'practice' }), {
      conversationId: `mock_conversation_${personaId}_${practiceRoomId}`,
      persona: PERSONAS.find((p) => p.id === personaId) || PERSONAS[0],
      practiceRoom: PRACTICE_ROOMS.find((r) => r.id === practiceRoomId) || PRACTICE_ROOMS[0],
    }),

  createTurn: (conversationId: string, text: string) =>
    request<CreateTurnResponse>(`/v1/conversations/${conversationId}/turns`, post({ inputType: 'text', text, requestTts: true }), {
      conversationId,
      userText: text,
      assistantText:
        '친구한테 자연스럽게 말하면 「今日めっちゃ疲れた」라고 하면 좋아. 조금 더 부드럽게는 「今日はすごく疲れた」. 먼저 내가 말해볼게. 잘 들어봐.',
      spokenText: MOCK_SPOKEN,
      suggestedUserReply: MOCK_SPOKEN,
      audioUrl: null,
      corrections: [
        { category: 'naturalness', original: text, corrected: MOCK_SPOKEN, explanationKo: '친구 사이에서 자연스러운 일상 표현이에요. 「めっちゃ」가 회화체 강조예요.', severity: 'minor', isKoreanLiteral: false },
      ],
      reviewCards: [INITIAL_REVIEW_CARD],
      usage: { llmInputTokens: 100, llmOutputTokens: 80, ttsCharacters: 12, ttsSeconds: 2.1, cacheHit: false },
    }),

  synthesizeTts: (text: string, personaId: string) =>
    request<TtsResponse>('/v1/tts/synthesize', post({ text, personaId, language: 'ja' }), {
      audioUrl: null, audioBase64: null, provider: 'device_speech', cacheHit: false, spokenText: text, durationMs: 2100,
    }),

  transcribeAudio: (mockText = MOCK_STT) =>
    request<SttResponse>('/v1/stt/transcribe', post({ language: 'ja', mockText }), { text: mockText, provider: 'mock', confidence: 0.82 }),

  // ---- daily talk / dialogue bank (new) ----
  // NOTE: in mock mode the client-side matcher (src/dialogue/matchMock.ts) is used
  // instead of this stub, since it has the candidate texts locally.
  dialogueMatch: (req: DialogueMatchRequest) =>
    request<DialogueMatchResponse>('/v1/dialogue/match', post(req), {
      tier: 'fallback', matchedLineId: null, score: 0, confirmLineId: null, globalIntent: null, latencyMs: 0,
    }),
  logUnmatched: (personaId: string, packVersion: string, nodeId: string, utterance: string, sttConfidence: number) =>
    request<{ accepted: boolean; id?: string }>('/v1/dialogue/unmatched', post({ personaId, packVersion, nodeId, utterance, sttConfidence }), { accepted: true }),
  listVoices: () => request<VoiceCatalogItem[]>('/v1/voices', undefined, []),

  // ---- pronunciation scoring (new) ----
  scorePronunciation: (expectedText: string, actualText: string) =>
    request<PronunciationScore>('/v1/pronunciation/score', post({ expectedText, actualText }), {
      provider: 'mock', expectedText, actualText, score: 89, rating: 'good', scoringMode: 'text_similarity_mock', acousticEvidencePresent: false, feedbackKo: '거의 정확해요. 「れ」를 또렷하게.',
    }),

  listReviewCards: () => request<{ reviewCards: ReviewCard[] }>('/v1/review-cards', undefined, { reviewCards: [INITIAL_REVIEW_CARD] }),

  createReviewCard: (card: ReviewCard) => request<{ reviewCard: ReviewCard }>('/v1/review-cards', post(card), { reviewCard: card }),

  // ---- server SRS (new) ----
  dueReviewCards: () => request<{ reviewCards: ReviewCard[] }>('/v1/review-cards/due', undefined, { reviewCards: [INITIAL_REVIEW_CARD] }),
  gradeReviewCard: (id: string, grade: 'again' | 'hard' | 'good' | 'easy') =>
    request<{ reviewCard: ReviewCard }>(`/v1/review-cards/${id}/grade`, post({ grade }), { reviewCard: INITIAL_REVIEW_CARD }),

  getTodayProgress: () => request<TodayProgress>('/v1/progress/today', undefined, TODAY_PROGRESS),
  getEntitlements: () => request<Entitlement>('/v1/entitlements/me', undefined, MASTER_ENTITLEMENT),

  // ---- server gamification (new) ----
  gamificationMe: () => request<GamificationSummary>('/v1/gamification/me', undefined, mockGamification),
  leaderboardWeekly: () => request<WeeklyLeaderboard>('/v1/leaderboards/weekly', undefined, mockGamification.weeklyLeaderboard),
  achievementsMe: () => request<AchievementsSummary>('/v1/achievements/me', undefined, mockGamification.achievements),
  leagueMe: () => request<LeagueStatus>('/v1/leagues/me', undefined, mockGamification.league),

  // ---- profile / recommendations / insights (new) ----
  profileMe: () => request<LearnerProfile>('/v1/profile/me', undefined, {
    learnerId: LEARNER_ID, nativeLanguage: 'ko', targetLanguage: 'ja', level: 'beginner', jlptLevel: 'N5',
    goals: ['daily_speaking', 'japanese_friend_conversation'], weakTags: ['감정표현'], preferredPersonaId: 'yui',
  }),
  recommendationsToday: () => request<RecommendationsResponse>('/v1/recommendations/today', undefined, {
    profile: { learnerId: LEARNER_ID, nativeLanguage: 'ko', targetLanguage: 'ja', level: 'beginner', jlptLevel: 'N5', goals: ['daily_speaking'], weakTags: ['감정표현'], preferredPersonaId: 'yui' },
    progress: TODAY_PROGRESS,
    dueReviewCards: [INITIAL_REVIEW_CARD],
    recommendedPracticeRooms: PRACTICE_ROOMS.slice(0, 2).map((r, i) => ({ score: 1 - i * 0.2, practiceRoom: r, reason: i === 0 ? '오늘의 추천' : '약점 보강' })),
    nextBestAction: '오늘의 3분 미션을 시작하세요',
  }),
  memorySummary: () => request<MemorySummary>('/v1/memory/summary', undefined, {
    cardCount: 1, reviewedCardCount: 0, newCardCount: 1, averageRecallProbability: null, atRiskCards: [], tagMastery: [], pressureTags: [], model: 'mock',
  }),
  usageSummary: () => request<UsageSummary>('/v1/usage/summary', undefined, {
    llmInputTokens: 0, llmOutputTokens: 0, sttSeconds: 0, ttsCharacters: 0, ttsSeconds: 0, ttsCacheHits: 0, usageRecords: 0, ttsCacheEntries: 0, estimatedMode: 'mock',
  }),
  providersStatus: () => request<Record<string, unknown>>('/v1/providers/status', undefined, { llmProvider: 'mock', ttsProvider: 'mock', sttProvider: 'mock' }),

  // ---- friends / social (new) ----
  friends: () =>
    request<FriendsSummary>('/v1/friends', undefined, {
      learnerId: LEARNER_ID, friends: [], incomingInvites: [], outgoingInvites: [], friendCount: 0,
    }),
  friendRecommendations: () =>
    request<FriendRecommendationsResponse>('/v1/friends/recommendations', undefined, {
      learnerId: LEARNER_ID, weekStart: TODAY_PROGRESS.date, weekEnd: TODAY_PROGRESS.date, recommendations: [], count: 0, excludedFriendCount: 0, excludedPendingInviteCount: 0, excludedBlockedCount: 0, excludedPrivateCount: 0,
    }),
  createFriendInvite: (friendLearnerId: string, message?: string) =>
    request<FriendInviteResponse>('/v1/friends/invites', post({ friendLearnerId, message }), { invite: null, relationship: null, created: false, reason: 'mock' }),
  acceptFriendInvite: (inviteId: string) =>
    request<FriendInviteAcceptResponse>(`/v1/friends/invites/${inviteId}/accept`, post({}), {
      invite: { id: inviteId, requesterLearnerId: 'mock', addresseeLearnerId: LEARNER_ID, status: 'accepted', createdAt: '', updatedAt: '' }, relationship: null, accepted: false, alreadyResponded: true,
    }),
  removeFriend: (friendLearnerId: string) =>
    request<RemoveFriendResponse>(`/v1/friends/${friendLearnerId}`, { method: 'DELETE' }, {
      relationship: { id: 'mock', learnerId: LEARNER_ID, friendLearnerId, status: 'removed', createdAt: '', updatedAt: '' }, removed: false,
    }),

  // ---- reward shop (new) ----
  rewardShop: () =>
    request<RewardShopResponse>('/v1/rewards/shop', undefined, {
      items: [
        { rewardKey: 'xp_boost_2x_15m', rewardType: 'xp_boost', title: '2배 XP 부스트 (15분)', description: '15분 동안 XP 2배', priceCurrency: 'gems', priceAmount: 2, available: true, affordable: false, active: false, sortOrder: 0, purchasedToday: 0, currentInventoryQuantity: 0 },
        { rewardKey: 'streak_freeze_1', rewardType: 'streak_freeze', title: '스트릭 프리즈', description: '하루 빠져도 스트릭 유지', priceCurrency: 'gems', priceAmount: 3, available: true, affordable: false, active: false, sortOrder: 1, purchasedToday: 0, currentInventoryQuantity: 0 },
      ],
      balances: [{ currencyKey: 'gems', balance: 0 }],
    }),
  purchaseReward: (rewardKey: string) =>
    request<RewardPurchaseResponse>(`/v1/rewards/shop/${rewardKey}/purchase`, post({}), {
      purchased: false, reason: 'mock', inventoryItem: null,
      shop: { items: [], balances: [{ currencyKey: 'gems', balance: 0 }] },
    }, { noFallbackInReal: true }),
  activateBoost: (rewardKey: string) =>
    request<ActivateXpBoostResponse>(`/v1/rewards/boosts/${rewardKey}/activate`, post({}), {
      activeBoost: null, activated: false,
      inventory: { items: [], activeXpBoosts: [], catalog: [], balances: [{ currencyKey: 'gems', balance: 0 }] },
    }, { noFallbackInReal: true }),
  friendQuests: () =>
    request<FriendQuestsResponse>('/v1/friends/quests', undefined, {
      friendQuests: [], suggestedPartnerLearnerId: '', weekStart: TODAY_PROGRESS.date, weekEnd: TODAY_PROGRESS.date,
    }),
  claimFriendQuest: (questId: string) =>
    request<FriendQuestClaimResponse>(`/v1/friends/quests/${questId}/claim`, post({}), {
      quest: {
        id: questId, key: 'mock', title: '', learnerId: LEARNER_ID, partnerLearnerId: '', weekKey: '', weekStart: '', weekEnd: '',
        targetXp: 0, learnerXp: 0, partnerXp: 0, combinedXp: 0, progress: 0, progressRatio: 0, completed: false, claimed: false,
        reward: { key: 'mock', type: 'currency', title: '' }, createdAt: '', updatedAt: '',
      },
      rewardItem: null, claimed: false, alreadyClaimed: true,
    }),

  // ---- social settings / blocks / discovery / reputation (iter3) ----
  socialSettings: () =>
    request<SocialSettings>('/v1/social/settings', undefined, {
      learnerId: LEARNER_ID, discoverable: true, allowFriendInvites: true, showWeeklyXp: true, createdAt: '', updatedAt: '',
    }),
  updateSocialSettings: (body: { discoverable: boolean; allowFriendInvites: boolean; showWeeklyXp: boolean }) =>
    request<SocialSettings>('/v1/social/settings', { method: 'PUT', body: JSON.stringify(body) }, {
      learnerId: LEARNER_ID, ...body, createdAt: '', updatedAt: '',
    }, { noFallbackInReal: true }),
  socialBlocks: () =>
    request<SocialBlocksResponse>('/v1/social/blocks', undefined, { learnerId: LEARNER_ID, blocks: [], count: 0 }),
  blockLearner: (blockedLearnerId: string) =>
    request<SocialBlockResponse>(`/v1/social/blocks/${blockedLearnerId}`, post({}), { block: null, blocked: false, reason: 'mock' }, { noFallbackInReal: true }),
  unblockLearner: (blockedLearnerId: string) =>
    request<SocialUnblockResponse>(`/v1/social/blocks/${blockedLearnerId}`, { method: 'DELETE' }, { unblocked: false, learnerId: LEARNER_ID, blockedLearnerId }, { noFallbackInReal: true }),
  socialDiscovery: () =>
    request<SocialDiscoveryResponse>('/v1/social/discovery', undefined, {
      learnerId: LEARNER_ID, weekStart: TODAY_PROGRESS.date, weekEnd: TODAY_PROGRESS.date, candidates: [], count: 0,
      excludedFriendOrPendingCount: 0, excludedBlockedCount: 0, excludedPrivateCount: 0,
    }),
  myReputation: () =>
    request<LearnerReputationProfile>('/v1/reputation/me', undefined, {
      learnerId: LEARNER_ID, riskScore: 0, riskBand: 'trusted', reviewRecommended: false, leaderboardEligible: true,
      latestSignalAt: null, signals: [],
      summary: { openXpAbuseFlagCount: 0, blockingXpAbuseFlagCount: 0, resolvedOrDismissedXpAbuseFlagCount: 0, incomingBlockCount: 0, outgoingBlockCount: 0, weekXp: 0, weekEventCount: 0, weekSourceCount: 0, deviceCount: 1, trustedDeviceCount: 1, untrustedDeviceCount: 0, revokedDeviceCount: 0, activeSessionCount: 1 },
      xpAbuseFlags: [],
    }),

  trackEvent: (eventName: string, payload?: Record<string, unknown>) =>
    request<{ ok: boolean }>('/v1/events', post({ eventName, payload }), { ok: true }),
};
