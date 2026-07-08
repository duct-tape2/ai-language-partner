// Provider / repository boundary. The store talks ONLY to these services, never
// to the raw API client or fixtures. Today they wrap the mock/contract client +
// local storage; when Codex's backend lands, only these implementations change,
// not the screens or store.
import { api, apiMode, API_BASE } from './api/client';
import { loadJSON, saveJSON, KEYS } from './storage';
import { sttOutcomeFor } from './sttFixtures';
import type { SttStatus } from './sttFixtures';
import {
  gradeSrsCard,
  isDue,
  makeSrsCard,
  reviveCards,
  type Grade,
  type SrsCard,
} from './srs';
import type {
  AchievementsSummary,
  Course,
  Entitlement,
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
  RewardShopResponse,
  ReviewCard,
  TodayProgress,
  UsageSummary,
  WeeklyLeaderboard,
} from '../../../packages/shared/src/types';

// ---- speaking-loop contract (frozen shape so the real backend can drop in) ----
export type SpeechRequest = {
  targetText: string;
  locale: string;
  personaId: string;
  missionId: string;
  attempt: number;
};
export type SpeechResult = {
  transcript: string;
  confidence: number;
  status: SttStatus;
  warning?: string;
  note: string;
};

export const SpeechService = {
  // Mock provider: rotates demo outcomes so the loop is not always 100%.
  // A real provider would POST audio to /v1/stt/transcribe and map the response.
  async recognize(req: SpeechRequest): Promise<SpeechResult> {
    const o = sttOutcomeFor(req.attempt);
    await api.transcribeAudio(o.transcript || req.targetText); // exercise the contract endpoint
    const confidence = o.status === 'perfect' ? 0.95 : o.status === 'partial' ? 0.62 : 0;
    return { transcript: o.transcript, confidence, status: o.status, warning: o.warning, note: o.note };
  },
};

export const TtsService = {
  synthesize: (text: string, personaId: string) => api.synthesizeTts(text, personaId),
};

export const ConversationService = {
  create: (personaId: string, roomId: string) => api.createConversation(personaId, roomId),
  turn: (conversationId: string, text: string) => api.createTurn(conversationId, text),
};

export const ContentService = {
  personas: async (): Promise<Persona[]> => (await api.listPersonas()).personas,
  rooms: async (): Promise<PracticeRoom[]> => (await api.listPracticeRooms()).practiceRooms,
  todayProgress: (): Promise<TodayProgress> => api.getTodayProgress(),
  courses: async (): Promise<Course[]> => (await api.listCourses()).courses,
  course: async (id: string): Promise<Course> => (await api.getCourse(id)).course,
};

// Backend-backed learner features (courses/recommendations/server gamification/
// SRS/profile/insights). In mock mode these resolve to fixture stubs.
export const LearnerService = {
  recommendations: (): Promise<RecommendationsResponse> => api.recommendationsToday(),
  gamification: (): Promise<GamificationSummary> => api.gamificationMe(),
  leaderboard: (): Promise<WeeklyLeaderboard> => api.leaderboardWeekly(),
  league: (): Promise<LeagueStatus> => api.leagueMe(),
  achievements: (): Promise<AchievementsSummary> => api.achievementsMe(),
  profile: (): Promise<LearnerProfile> => api.profileMe(),
  memory: (): Promise<MemorySummary> => api.memorySummary(),
  usage: (): Promise<UsageSummary> => api.usageSummary(),
  providers: () => api.providersStatus(),
  dueCards: async (): Promise<ReviewCard[]> => (await api.dueReviewCards()).reviewCards,
  gradeServerCard: (id: string, grade: 'again' | 'hard' | 'good' | 'easy') => api.gradeReviewCard(id, grade),
  scorePronunciation: (expected: string, actual: string): Promise<PronunciationScore> => api.scorePronunciation(expected, actual),
  // friends / social + reward shop (new in iter2)
  friends: (): Promise<FriendsSummary> => api.friends(),
  friendRecommendations: (): Promise<FriendRecommendationsResponse> => api.friendRecommendations(),
  invite: (friendLearnerId: string, message?: string) => api.createFriendInvite(friendLearnerId, message),
  acceptInvite: (inviteId: string) => api.acceptFriendInvite(inviteId),
  removeFriend: (friendLearnerId: string) => api.removeFriend(friendLearnerId),
  rewardShop: (): Promise<RewardShopResponse> => api.rewardShop(),
  purchaseReward: (rewardKey: string) => api.purchaseReward(rewardKey),
  activateBoost: (rewardKey: string) => api.activateBoost(rewardKey),
  friendQuests: () => api.friendQuests(),
  claimFriendQuest: (questId: string) => api.claimFriendQuest(questId),
  // social settings / blocks / discovery / reputation (iter3)
  socialSettings: () => api.socialSettings(),
  updateSocialSettings: (body: { discoverable: boolean; allowFriendInvites: boolean; showWeeklyXp: boolean }) => api.updateSocialSettings(body),
  socialBlocks: () => api.socialBlocks(),
  blockLearner: (id: string) => api.blockLearner(id),
  unblockLearner: (id: string) => api.unblockLearner(id),
  socialDiscovery: () => api.socialDiscovery(),
  myReputation: () => api.myReputation(),
};

export const EntitlementService = {
  me: (): Promise<Entitlement> => api.getEntitlements(),
};

// Resolved API target, exposed for the dev-only diagnostics panel.
export const apiInfo: { mode: 'mock' | 'real'; base: string } = { mode: apiMode, base: API_BASE };

export const UsageService = {
  track: (eventName: string, payload?: Record<string, unknown>) => void api.trackEvent(eventName, payload),
  health: () => api.health(),
};

// ---- local repositories (today AsyncStorage; later server-backed) ----
export const ReviewRepository = {
  async list(): Promise<SrsCard[]> {
    return reviveCards(await loadJSON<SrsCard[]>(KEYS.srsCards, []));
  },
  async persist(cards: SrsCard[]): Promise<void> {
    await saveJSON(KEYS.srsCards, cards);
  },
  // Persist a saved card to the backend (mock today via the contract endpoint).
  create: (card: ReviewCard) => api.createReviewCard(card),
  add(cards: SrsCard[], card: ReviewCard): { cards: SrsCard[]; added: boolean } {
    if (cards.some((c) => c.id === card.id)) return { cards, added: false };
    return { cards: [makeSrsCard(card), ...cards], added: true };
  },
  grade(cards: SrsCard[], card: SrsCard, grade: Grade): SrsCard[] {
    return cards.map((c) => (c.id === card.id ? gradeSrsCard(c, grade) : c));
  },
  due: (cards: SrsCard[], cap: number) => cards.filter((c) => isDue(c)).slice(0, cap),
};
