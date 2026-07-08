import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Platform } from 'react-native';
import * as Speech from 'expo-speech';
import * as Haptics from 'expo-haptics';
import { DEFAULT_PERSONA_ID, FIRST_PRACTICE_ROOM_ID } from '../../../packages/shared/src/types';
import { PRACTICE_SEQUENCE, PRACTICE_TOTAL } from './practiceSequence';
import { MINI_STORIES, MINI_STORY_TOTAL, type MiniStory } from './miniStories';
import { LISTENING_ITEMS, LISTENING_TOTAL, type ListeningItem } from './listeningItems';
import { WORD_ITEMS, WORD_TOTAL, type WordItem } from './wordItems';
import { WORD_BANK_ITEMS, WORD_BANK_TOTAL, type WordBankItem } from './wordBankItems';
import { ROLEPLAY_ITEMS, ROLEPLAY_TOTAL, type RoleplayItem } from './roleplayItems';
import type {
  Correction,
  Course,
  Entitlement,
  FriendQuestsResponse,
  FriendRecommendationsResponse,
  FriendsSummary,
  GamificationSummary,
  LearnerReputationProfile,
  SocialBlocksResponse,
  SocialDiscoveryResponse,
  SocialSettings,
  Persona,
  PracticeRoom,
  RecommendationsResponse,
  RewardShopResponse,
  ReviewCard,
  TodayProgress,
} from '../../../packages/shared/src/types';
import { KEYS, clearAll, exportAll, loadJSON, migrate, saveJSON } from './storage';
import { setUiLocale, type UiLocale } from './i18n';
import { previewIntervalLabel, type Grade, type SrsCard } from './srs';
import {
  addXp,
  awardBadge,
  bumpQuest,
  initialGamState,
  levelProgress,
  registerActivity,
  todayStr,
  XP,
  type GamState,
} from './gamification';
import { personaVoice } from './personaStyle';
import { coachingLine } from './coaching';
import { accuracyOf, diffChars, type DiffSeg } from './text';
import type { SttStatus } from './sttFixtures';
import { DEMO_MODE } from './devConfig';
import {
  ContentService,
  ConversationService,
  EntitlementService,
  LearnerService,
  ReviewRepository,
  SpeechService,
  TtsService,
  UsageService,
  apiInfo,
} from './services';

export type Screen =
  | 'home' | 'personas' | 'practice' | 'voice' | 'review' | 'progress' | 'settings' | 'courses' | 'friends' | 'shop' | 'security' | 'story' | 'listening' | 'hub' | 'words' | 'roleplay' | 'wordbank' | 'dailytalk' | 'voicegallery'
  | 'kanji' | 'grammar' | 'exam' | 'placement' | 'kanaChart' | 'counters' | 'conjugation' | 'numbers'
  | 'vocab' | 'pitch' | 'dialogueshadow' | 'keigo'
  | 'pitfalls' | 'reading' | 'mistakes'
  | 'pronunciation' | 'mastery' | 'situations'
  | 'culture' | 'idioms'
  | 'peerreview' | 'pronclinic' | 'report'
  | 'choukai' | 'n5exam' | 'premium'
  | 'insights' | 'quests';
export type ReviewMode = 'shadow' | 'listen' | 'recall';
export type SaveState = 'saved' | 'duplicate' | null;

export type Settings = {
  ttsSpeed: number;
  dailyGoal: number;
  reviewCap: number;
  reminderTime: string; // HH:MM
  uiLocale: UiLocale;
};

export type OnboardingChoice = { personaId: string; level: number; dailyGoal: number };

const DEFAULT_SETTINGS: Settings = { ttsSpeed: 1.0, dailyGoal: 5, reviewCap: 20, reminderTime: '21:00', uiLocale: 'ko' };
const SCREENS: Screen[] = ['home', 'personas', 'practice', 'voice', 'review', 'progress', 'settings', 'courses', 'friends', 'shop', 'security', 'story', 'listening', 'hub', 'words', 'roleplay', 'wordbank', 'dailytalk', 'voicegallery', 'kanji', 'grammar', 'exam', 'placement', 'kanaChart', 'counters', 'conjugation', 'numbers', 'vocab', 'pitch', 'dialogueshadow', 'keigo', 'pitfalls', 'reading', 'mistakes', 'pronunciation', 'mastery', 'situations', 'culture', 'idioms', 'peerreview', 'pronclinic', 'report', 'choukai', 'n5exam', 'premium', 'insights', 'quests'];

function initialScreenFromUrl(): Screen {
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    const q = new URLSearchParams(window.location.search).get('screen') as Screen | null;
    if (q && SCREENS.includes(q)) return q;
  }
  return 'home';
}

function haptic(kind: 'tap' | 'success' | 'warn') {
  if (Platform.OS === 'web') return;
  try {
    if (kind === 'tap') void Haptics.selectionAsync();
    else if (kind === 'success') void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    else void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
  } catch {
    // ignore
  }
}

export type AppController = {
  ready: boolean;
  onboarded: boolean;
  demoMode: boolean;
  completeOnboarding: (c: OnboardingChoice) => void;

  screen: Screen;
  navigate: (s: Screen) => void;

  personas: Persona[];
  rooms: PracticeRoom[];
  room?: PracticeRoom;
  persona?: Persona;

  selectedPersonaId: string;
  selectPersona: (id: string) => void;

  assistantText: string;
  spokenText: string;
  phraseIndex: number;
  practiceTotal: number;
  currentPhraseKo: string;
  nextPhrase: () => void;
  storyIndex: number;
  storyTotal: number;
  currentStory: MiniStory | null;
  storyChoiceId: string | null;
  storyCorrectCount: number;
  startStories: () => void;
  answerStory: (choiceId: string) => void;
  nextStory: () => void;
  listeningIndex: number;
  listeningTotal: number;
  currentListening: ListeningItem | null;
  listeningChoiceId: string | null;
  listeningCorrectCount: number;
  startListening: () => void;
  answerListening: (choiceId: string) => void;
  answerListeningDictation: (correct: boolean) => void;
  nextListening: () => void;
  wordBankIndex: number;
  wordBankTotal: number;
  currentWordBank: WordBankItem | null;
  wordBankSolved: boolean;
  wordBankCorrectCount: number;
  startWordBank: () => void;
  checkWordBank: (assembled: string) => boolean;
  nextWordBank: () => void;
  wordIndex: number;
  wordTotal: number;
  currentWord: WordItem | null;
  wordRevealed: boolean;
  wordKnownCount: number;
  startWords: () => void;
  revealWord: () => void;
  gradeWord: (known: boolean) => void;
  roleplayIndex: number;
  roleplayTotal: number;
  currentRoleplay: RoleplayItem | null;
  roleplayRevealed: boolean;
  startRoleplay: () => void;
  revealRoleplay: () => void;
  nextRoleplay: () => void;
  sttResult: string | null;
  sttStatus: SttStatus | null;
  sttWarning: string | null;
  sttNote: string | null;
  coachingNow: string | null;
  diff: DiffSeg[];
  accuracy: number | null;
  corrections: Correction[];

  candidateCards: ReviewCard[];
  srsCards: SrsCard[];
  dueCards: SrsCard[];
  reviewMode: ReviewMode;
  setReviewMode: (m: ReviewMode) => void;
  lastSaveState: SaveState;

  progress: TodayProgress;
  entitlement: Entitlement | null;

  // backend-backed (real mode adds live data; mock returns fixture stubs)
  courses: Course[];
  // course path: per-lesson completion map, keyed `${courseId}:${lessonId}`
  courseProgress: Record<string, boolean>;
  completeLesson: (courseId: string, lessonId: string) => void;
  recommendation: RecommendationsResponse | null;
  serverGam: GamificationSummary | null;
  friends: FriendsSummary | null;
  friendRecs: FriendRecommendationsResponse | null;
  shop: RewardShopResponse | null;
  friendQuests: FriendQuestsResponse | null;
  shopMessage: string | null;
  clearShopMessage: () => void;
  socialSettings: SocialSettings | null;
  socialSaveState: 'idle' | 'saving' | 'saved' | 'error';
  socialBlocks: SocialBlocksResponse | null;
  discovery: SocialDiscoveryResponse | null;
  reputation: LearnerReputationProfile | null;
  inviteFriend: (friendLearnerId: string) => void;
  acceptInvite: (inviteId: string) => void;
  unfriend: (friendLearnerId: string) => void;
  purchaseReward: (rewardKey: string) => Promise<void>;
  activateBoost: (rewardKey: string) => Promise<void>;
  claimQuest: (questId: string) => void;
  updateSocial: (body: { discoverable: boolean; allowFriendInvites: boolean; showWeeklyXp: boolean }) => void;
  blockLearner: (id: string) => void;
  unblockLearner: (id: string) => void;

  gam: GamState;
  level: number;
  levelPct: number;

  settings: Settings;
  updateSettings: (p: Partial<Settings>) => void;

  speaking: boolean;
  healthText: string;
  apiInfo: { mode: 'mock' | 'real'; base: string };

  speak: (text?: string) => void;
  startPractice: () => Promise<void>;
  submitTurn: () => Promise<void>;
  runMockStt: () => Promise<void>;
  saveReviewCard: () => Promise<void>;
  gradeReview: (card: SrsCard, grade: Grade) => void;
  gradeLabel: (card: SrsCard, grade: Grade) => string;
  completeMission: () => void;
  checkHealth: () => Promise<void>;
  resetData: () => Promise<void>;
  exportData: () => Promise<string>;
  track: (event: string, payload?: Record<string, unknown>) => void;
};

export function useApp(): AppController {
  const [ready, setReady] = useState(false);
  const [onboarded, setOnboarded] = useState(false);

  const [screen, setScreen] = useState<Screen>(initialScreenFromUrl);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [rooms, setRooms] = useState<PracticeRoom[]>([]);
  const [selectedPersonaId, setSelectedPersonaId] = useState(DEFAULT_PERSONA_ID);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const [assistantText, setAssistantText] = useState('');
  const [spokenText, setSpokenText] = useState('今日めっちゃ疲れた。');
  const [phraseIndex, setPhraseIndex] = useState(0);
  // Mini Story (맥락 이해) state. Swaps to GET/POST /practice-hub/stories later.
  const [storyIndex, setStoryIndex] = useState(0);
  const [storyChoiceId, setStoryChoiceId] = useState<string | null>(null);
  const [storyCorrectCount, setStoryCorrectCount] = useState(0);
  // Listening (듣기) state. Swaps to GET/POST /practice-hub/listening later.
  const [listeningIndex, setListeningIndex] = useState(0);
  const [listeningChoiceId, setListeningChoiceId] = useState<string | null>(null);
  const [listeningCorrectCount, setListeningCorrectCount] = useState(0);
  // Word bank (문장 조립) state: assemble shuffled chips into the heard sentence.
  const [wordBankIndex, setWordBankIndex] = useState(0);
  const [wordBankSolved, setWordBankSolved] = useState(false);
  const [wordBankCorrectCount, setWordBankCorrectCount] = useState(0);
  // Course path: per-lesson completion (`${courseId}:${lessonId}` -> true).
  const [courseProgress, setCourseProgress] = useState<Record<string, boolean>>({});
  // Words (단어) recall state: reveal the answer, then self-grade known/again.
  const [wordIndex, setWordIndex] = useState(0);
  const [wordRevealed, setWordRevealed] = useState(false);
  const [wordKnownCount, setWordKnownCount] = useState(0);
  // Roleplay (롤플레이) state: situation -> reveal a suggested reply -> practice.
  const [roleplayIndex, setRoleplayIndex] = useState(0);
  const [roleplayRevealed, setRoleplayRevealed] = useState(false);
  const [sttResult, setSttResult] = useState<string | null>(null);
  const [sttStatus, setSttStatus] = useState<SttStatus | null>(null);
  const [sttWarning, setSttWarning] = useState<string | null>(null);
  const [sttNote, setSttNote] = useState<string | null>(null);
  const [coachingNow, setCoachingNow] = useState<string | null>(null);
  const [diff, setDiff] = useState<DiffSeg[]>([]);
  const [accuracy, setAccuracy] = useState<number | null>(null);
  const [corrections, setCorrections] = useState<Correction[]>([]);

  const [candidateCards, setCandidateCards] = useState<ReviewCard[]>([]);
  const [srsCards, setSrsCards] = useState<SrsCard[]>([]);
  const [reviewMode, setReviewMode] = useState<ReviewMode>('shadow');
  const [lastSaveState, setLastSaveState] = useState<SaveState>(null);

  const [progress, setProgress] = useState<TodayProgress>({
    date: todayStr(),
    streakDays: 1,
    completedMissions: 0,
    spokenSentenceCount: 0,
    reviewCardsCreated: 0,
  });
  const [entitlement, setEntitlement] = useState<Entitlement | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [recommendation, setRecommendation] = useState<RecommendationsResponse | null>(null);
  const [serverGam, setServerGam] = useState<GamificationSummary | null>(null);
  const [friends, setFriends] = useState<FriendsSummary | null>(null);
  const [friendRecs, setFriendRecs] = useState<FriendRecommendationsResponse | null>(null);
  const [shop, setShop] = useState<RewardShopResponse | null>(null);
  const [friendQuests, setFriendQuests] = useState<FriendQuestsResponse | null>(null);
  const [shopMessage, setShopMessage] = useState<string | null>(null);
  const [socialSettings, setSocialSettings] = useState<SocialSettings | null>(null);
  const [socialBlocks, setSocialBlocks] = useState<SocialBlocksResponse | null>(null);
  const [discovery, setDiscovery] = useState<SocialDiscoveryResponse | null>(null);
  const [reputation, setReputation] = useState<LearnerReputationProfile | null>(null);
  const [socialSaveState, setSocialSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [gam, setGam] = useState<GamState>(() => initialGamState());
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [speaking, setSpeaking] = useState(false);
  const [healthText, setHealthText] = useState('확인 전');
  const utteranceId = useRef(0);
  const sttAttempt = useRef(0);
  // Phrase indices already counted toward today's progress, so re-recording the
  // same sentence doesn't inflate the daily ring vs the 5-sentence set.
  const countedPhrases = useRef<Set<number>>(new Set());

  const room = useMemo(() => rooms.find((r) => r.id === FIRST_PRACTICE_ROOM_ID), [rooms]);
  const persona = useMemo(() => personas.find((p) => p.id === selectedPersonaId), [personas, selectedPersonaId]);
  const dueCards = useMemo(() => ReviewRepository.due(srsCards, settings.reviewCap), [srsCards, settings.reviewCap]);
  const lp = useMemo(() => levelProgress(gam.xp), [gam.xp]);

  const track = useCallback((event: string, payload?: Record<string, unknown>) => UsageService.track(event, payload), []);
  const persistGam = useCallback((g: GamState) => void saveJSON(KEYS.gamification, g), []);

  // Real mode: re-pull server gamification + recommendation so league/XP/quests
  // reflect the learning event that just happened on the server.
  const refreshServer = useCallback(async () => {
    if (apiInfo.mode !== 'real') return;
    try {
      const [sgam, rec] = await Promise.all([LearnerService.gamification(), LearnerService.recommendations()]);
      setServerGam(sgam);
      setRecommendation(rec);
    } catch {
      // non-fatal
    }
  }, []);

  const refreshSocial = useCallback(async () => {
    try {
      const [f, fr, sh, fq, ss, sb, sd, rep] = await Promise.all([
        LearnerService.friends(),
        LearnerService.friendRecommendations(),
        LearnerService.rewardShop(),
        LearnerService.friendQuests(),
        LearnerService.socialSettings(),
        LearnerService.socialBlocks(),
        LearnerService.socialDiscovery(),
        LearnerService.myReputation(),
      ]);
      setFriends(f);
      setFriendRecs(fr);
      setShop(sh);
      setFriendQuests(fq);
      setSocialSettings(ss);
      setSocialBlocks(sb);
      setDiscovery(sd);
      setReputation(rep);
    } catch {
      // non-fatal
    }
  }, []);

  // After a mutation, server gamification (gems balance, friend count, quests,
  // inventory, active boosts) and the social lists must both re-pull so the UI
  // reflects the server immediately — no optimistic local guesswork.
  const refreshAfterMutation = useCallback(async () => {
    await Promise.all([refreshSocial(), refreshServer()]);
  }, [refreshSocial, refreshServer]);

  const inviteFriend = useCallback((friendLearnerId: string) => { haptic('tap'); void LearnerService.invite(friendLearnerId).then(refreshAfterMutation); }, [refreshAfterMutation]);
  const acceptInvite = useCallback((inviteId: string) => { haptic('success'); void LearnerService.acceptInvite(inviteId).then(refreshAfterMutation); }, [refreshAfterMutation]);
  const unfriend = useCallback((friendLearnerId: string) => { haptic('warn'); void LearnerService.removeFriend(friendLearnerId).then(refreshAfterMutation); }, [refreshAfterMutation]);

  // Returns a promise so the screen can tie its loading state to real completion.
  // On failure (e.g. 409 not-enough-gems / already-owned in real mode) we surface
  // a message AND refetch so the UI matches the server instead of faking success.
  const purchaseReward = useCallback(async (rewardKey: string) => {
    haptic('success');
    setShopMessage(null);
    try {
      const res = await LearnerService.purchaseReward(rewardKey);
      setShopMessage(res.purchased === false ? '구매하지 못했어요. 젬 잔액을 확인해 주세요.' : '보상을 구매했어요! 🎉');
    } catch {
      setShopMessage('구매에 실패했어요. 젬이 부족하거나 이미 보유 중일 수 있어요.');
    } finally {
      await refreshAfterMutation();
    }
  }, [refreshAfterMutation]);
  const activateBoost = useCallback(async (rewardKey: string) => {
    haptic('success');
    setShopMessage(null);
    try {
      const res = await LearnerService.activateBoost(rewardKey);
      setShopMessage(res.activated === false ? '지금은 사용할 수 없어요. 보유 상태를 확인해 주세요.' : '부스트가 시작됐어요! ⚡');
    } catch {
      setShopMessage('보상을 사용하지 못했어요. 잠시 후 다시 시도해 주세요.');
    } finally {
      await refreshAfterMutation();
    }
  }, [refreshAfterMutation]);
  const claimQuest = useCallback((questId: string) => { haptic('success'); void LearnerService.claimFriendQuest(questId).then(refreshAfterMutation); }, [refreshAfterMutation]);
  const clearShopMessage = useCallback(() => setShopMessage(null), []);
  const updateSocial = useCallback((body: { discoverable: boolean; allowFriendInvites: boolean; showWeeklyXp: boolean }) => {
    haptic('tap');
    setSocialSaveState('saving');
    setSocialSettings((prev) => (prev ? { ...prev, ...body } : prev)); // optimistic
    void LearnerService.updateSocialSettings(body)
      .then(() => { setSocialSaveState('saved'); return refreshSocial(); })
      .catch(() => { setSocialSaveState('error'); return refreshSocial(); }); // refetch reverts the optimistic value on failure
  }, [refreshSocial]);
  const blockLearner = useCallback((id: string) => { haptic('warn'); void LearnerService.blockLearner(id).then(refreshAfterMutation); }, [refreshAfterMutation]);
  const unblockLearner = useCallback((id: string) => { haptic('tap'); void LearnerService.unblockLearner(id).then(refreshAfterMutation); }, [refreshAfterMutation]);

  const navigate = useCallback(
    (s: Screen) => {
      haptic('tap');
      setScreen(s);
      if (s === 'home') track('home_today_viewed');
      if (s === 'practice') track('practice_room_opened', { practiceRoomId: FIRST_PRACTICE_ROOM_ID });
      if (s === 'progress' || s === 'home') void refreshServer();
    },
    [track, refreshServer],
  );

  const selectPersona = useCallback(
    (id: string) => {
      haptic('tap');
      setSelectedPersonaId(id);
      void saveJSON(KEYS.selectedPersona, id);
      track('persona_selected', { personaId: id });
    },
    [track],
  );

  const speak = useCallback(
    (text?: string) => {
      const value = text ?? spokenText;
      const myId = ++utteranceId.current;
      const clear = () => {
        if (utteranceId.current === myId) setSpeaking(false);
      };
      const v = personaVoice(selectedPersonaId);
      Speech.stop();
      setSpeaking(true);
      Speech.speak(value, {
        language: 'ja-JP',
        rate: v.rate * settings.ttsSpeed,
        pitch: v.pitch,
        onDone: clear,
        onStopped: clear,
        onError: clear,
      });
      void TtsService.synthesize(value, selectedPersonaId);
      track('first_tts_played', { text: value });
    },
    [spokenText, selectedPersonaId, settings.ttsSpeed, track],
  );

  const startPractice = useCallback(async () => {
    const res = await ConversationService.create(selectedPersonaId, FIRST_PRACTICE_ROOM_ID);
    setConversationId(res.conversationId);
    track('practice_room_started', { practiceRoomId: FIRST_PRACTICE_ROOM_ID, personaId: selectedPersonaId });
    setScreen('practice');
  }, [selectedPersonaId, track]);

  const resetSttState = () => {
    setSttResult(null);
    setSttStatus(null);
    setSttWarning(null);
    setSttNote(null);
    setCoachingNow(null);
    setDiff([]);
    setAccuracy(null);
    setLastSaveState(null);
    sttAttempt.current = 0;
  };

  // Roleplay loop: read the situation + partner line, reveal a natural reply,
  // practice saying it, advance (XP per completed scenario).
  const startRoleplay = () => {
    setRoleplayIndex(0);
    setRoleplayRevealed(false);
    track('roleplay_review_started', { total: ROLEPLAY_TOTAL });
    setScreen('roleplay');
  };
  const revealRoleplay = () => {
    setRoleplayRevealed(true);
    haptic('tap');
  };
  const nextRoleplay = () => {
    const item = ROLEPLAY_ITEMS[roleplayIndex];
    if (item) {
      setGam((g) => {
        const next = addXp(g, item.xpReward);
        persistGam(next);
        return next;
      });
      track('roleplay_review_answered', { itemId: item.id });
    }
    haptic('success');
    if (roleplayIndex + 1 < ROLEPLAY_TOTAL) {
      setRoleplayIndex((i) => i + 1);
      setRoleplayRevealed(false);
    } else {
      void refreshServer();
      completeMission();
      setScreen('progress');
    }
  };

  // Words loop: recall the JA word from its KO meaning, reveal, self-grade.
  const startWords = () => {
    setWordIndex(0);
    setWordRevealed(false);
    setWordKnownCount(0);
    track('word_review_started', { total: WORD_TOTAL });
    setScreen('words');
  };
  const revealWord = () => {
    setWordRevealed(true);
    haptic('tap');
  };
  const gradeWord = (known: boolean) => {
    const w = WORD_ITEMS[wordIndex];
    if (!w) return;
    if (known) {
      setWordKnownCount((n) => n + 1);
      setGam((g) => {
        const next = addXp(g, w.xpReward);
        persistGam(next);
        return next;
      });
    }
    haptic(known ? 'success' : 'tap');
    track('word_review_answered', { wordId: w.id, known });
    if (wordIndex + 1 < WORD_TOTAL) {
      setWordIndex((i) => i + 1);
      setWordRevealed(false);
    } else {
      void refreshServer();
      completeMission();
      setScreen('progress');
    }
  };

  // Listening loop: hear the sentence (TTS), pick the correct Korean meaning.
  const startListening = () => {
    setListeningIndex(0);
    setListeningChoiceId(null);
    setListeningCorrectCount(0);
    track('listening_review_started', { total: LISTENING_TOTAL });
    setScreen('listening');
  };
  const answerListening = (choiceId: string) => {
    if (listeningChoiceId) return;
    const item = LISTENING_ITEMS[listeningIndex];
    if (!item) return;
    const correct = choiceId === item.correctChoiceId;
    setListeningChoiceId(choiceId);
    if (correct) {
      setListeningCorrectCount((n) => n + 1);
      setGam((g) => {
        const next = addXp(g, item.xpReward);
        persistGam(next);
        return next;
      });
    }
    haptic(correct ? 'success' : 'warn');
    track('listening_review_answered', { itemId: item.id, correct });
    void refreshServer();
  };
  // 받아쓰기 (dictation) answer path: same XP/advance flow as the MCQ mode, but
  // the screen judges correctness (kana-normalized compare) and reports it.
  const answerListeningDictation = (correct: boolean) => {
    if (listeningChoiceId) return;
    const item = LISTENING_ITEMS[listeningIndex];
    if (!item) return;
    setListeningChoiceId(correct ? item.correctChoiceId : 'dictation_wrong');
    if (correct) {
      setListeningCorrectCount((n) => n + 1);
      setGam((g) => {
        const next = addXp(g, item.xpReward);
        persistGam(next);
        return next;
      });
    }
    haptic(correct ? 'success' : 'warn');
    track('listening_review_answered', { itemId: item.id, correct, mode: 'dictation' });
    void refreshServer();
  };
  const nextListening = () => {
    haptic('tap');
    if (listeningIndex + 1 < LISTENING_TOTAL) {
      setListeningIndex((i) => i + 1);
      setListeningChoiceId(null);
    } else {
      completeMission();
      setScreen('progress');
    }
  };

  // Word bank (문장 조립) loop: see the meaning / hear the sentence, tap chips
  // in order, check. Wrong attempts stay retryable; XP only on the solve.
  const startWordBank = () => {
    setWordBankIndex(0);
    setWordBankSolved(false);
    setWordBankCorrectCount(0);
    track('word_bank_started', { total: WORD_BANK_TOTAL });
    setScreen('wordbank');
  };
  const checkWordBank = (assembled: string): boolean => {
    const item = WORD_BANK_ITEMS[wordBankIndex];
    if (!item || wordBankSolved) return wordBankSolved;
    const correct = assembled === item.answer;
    if (correct) {
      setWordBankSolved(true);
      setWordBankCorrectCount((n) => n + 1);
      setGam((g) => {
        const next = addXp(g, item.xpReward);
        persistGam(next);
        return next;
      });
    }
    haptic(correct ? 'success' : 'warn');
    track('word_bank_answered', { itemId: item.id, correct });
    if (correct) void refreshServer();
    return correct;
  };
  const nextWordBank = () => {
    haptic('tap');
    if (wordBankIndex + 1 < WORD_BANK_TOTAL) {
      setWordBankIndex((i) => i + 1);
      setWordBankSolved(false);
    } else {
      completeMission();
      setScreen('progress');
    }
  };

  // Course path: mark a lesson done (persisted locally). Lesson N+1 unlocks
  // only when lesson N is completed; the screen derives locking from this map.
  const completeLesson = useCallback(
    (courseId: string, lessonId: string) => {
      const key = `${courseId}:${lessonId}`;
      if (courseProgress[key]) return;
      const next = { ...courseProgress, [key]: true };
      setCourseProgress(next);
      void saveJSON(KEYS.courseProgress, next);
      setProgress((p) => ({ ...p, completedMissions: p.completedMissions + 1 }));
      setGam((g) => {
        const n = bumpQuest(addXp(g, XP.mission), 'mission').state;
        persistGam(n);
        return n;
      });
      haptic('success');
      track('course_lesson_completed', { courseId, lessonId });
      void refreshServer();
    },
    [courseProgress, persistGam, track, refreshServer],
  );

  // Mini Story loop: read a 3-line dialogue, answer a comprehension MCQ, see the
  // KO summary + XP. Understanding in context, beyond single-sentence shadowing.
  const startStories = () => {
    setStoryIndex(0);
    setStoryChoiceId(null);
    setStoryCorrectCount(0);
    track('story_review_started', { total: MINI_STORY_TOTAL });
    setScreen('story');
  };
  const answerStory = (choiceId: string) => {
    if (storyChoiceId) return; // already answered this story
    const story = MINI_STORIES[storyIndex];
    if (!story) return;
    const correct = choiceId === story.correctChoiceId;
    setStoryChoiceId(choiceId);
    if (correct) {
      setStoryCorrectCount((n) => n + 1);
      setGam((g) => {
        const next = addXp(g, story.xpReward);
        persistGam(next);
        return next;
      });
    }
    haptic(correct ? 'success' : 'warn');
    track('story_review_answered', { storyId: story.id, correct });
    void refreshServer();
  };
  const nextStory = () => {
    haptic('tap');
    if (storyIndex + 1 < MINI_STORY_TOTAL) {
      setStoryIndex((i) => i + 1);
      setStoryChoiceId(null);
    } else {
      completeMission();
      setScreen('progress');
    }
  };

  // Core loop: advance to the next sentence in today's set (resets the speaking
  // state). On the last sentence the screen completes the mission instead.
  const nextPhrase = () => {
    haptic('tap');
    setPhraseIndex((idx) => {
      const next = idx + 1;
      if (next < PRACTICE_TOTAL) {
        setSpokenText(PRACTICE_SEQUENCE[next].ja);
        resetSttState();
        return next;
      }
      return idx;
    });
  };

  const submitTurn = useCallback(async () => {
    let cid = conversationId;
    if (!cid) {
      const conv = await ConversationService.create(selectedPersonaId, FIRST_PRACTICE_ROOM_ID);
      cid = conv.conversationId;
      setConversationId(cid);
    }
    const res = await ConversationService.turn(cid, '나 오늘 너무 피곤했어. 일본어로 뭐라고 해?');
    setAssistantText(res.assistantText);
    setSpokenText(PRACTICE_SEQUENCE[0].ja); // start today's curated set (translations align)
    setPhraseIndex(0);
    countedPhrases.current = new Set();
    setCorrections(res.corrections);
    setCandidateCards(res.reviewCards);
    resetSttState();
    track('first_user_reply_submitted', { practiceRoomId: FIRST_PRACTICE_ROOM_ID });
    setScreen('voice');
  }, [conversationId, selectedPersonaId, track]);

  // Speaking attempt: rotates demo outcomes (perfect / partial / fail) so the
  // loop is honest, not always 100%. Real provider swaps in via SpeechService.
  const runMockStt = useCallback(async () => {
    const attempt = sttAttempt.current++;
    const target = spokenText;
    const res = await SpeechService.recognize({
      targetText: target.replace(/。/g, ''),
      locale: 'ja-JP',
      personaId: selectedPersonaId,
      missionId: FIRST_PRACTICE_ROOM_ID,
      attempt,
    });
    setSttStatus(res.status);
    setSttWarning(res.warning ?? null);
    setSttNote(res.note);
    setCoachingNow(coachingLine(selectedPersonaId, res.status));

    if (res.status === 'fail') {
      setSttResult('');
      setDiff([]);
      setAccuracy(null);
      haptic('warn');
    } else {
      const segs = diffChars(target, res.transcript);
      const acc = accuracyOf(segs);
      setSttResult(res.transcript);
      setDiff(segs);
      setAccuracy(acc);
      // Real mode: get the server pronunciation score (source of truth) and feedback.
      if (apiInfo.mode === 'real') {
        try {
          const ps = await LearnerService.scorePronunciation(target.replace(/。/g, ''), res.transcript);
          setAccuracy(ps.score);
          if (ps.feedbackKo) setSttNote(ps.feedbackKo);
        } catch {
          // keep local diff-based score on failure
        }
      }
      if (!countedPhrases.current.has(phraseIndex)) {
        countedPhrases.current.add(phraseIndex);
        setProgress((p) => ({ ...p, spokenSentenceCount: p.spokenSentenceCount + 1 }));
      }
      setGam((g) => {
        let next = addXp(g, XP.speak);
        next = bumpQuest(next, 'shadow3').state;
        next = awardBadge(next, 'first_word');
        if (res.status === 'perfect') {
          next = addXp(next, XP.perfect);
          next = awardBadge(next, 'perfect');
        }
        persistGam(next);
        return next;
      });
      haptic(res.status === 'perfect' ? 'success' : 'warn');
    }
    track('first_correction_shown', { practiceRoomId: FIRST_PRACTICE_ROOM_ID, status: res.status });
    void refreshServer();
  }, [spokenText, selectedPersonaId, phraseIndex, persistGam, track, refreshServer]);

  const saveReviewCard = useCallback(async () => {
    const card = candidateCards[0];
    if (!card) return;
    const { reviewCard } = await ReviewRepository.create(card);
    const { cards: nextCards, added } = ReviewRepository.add(srsCards, reviewCard);
    setLastSaveState(added ? 'saved' : 'duplicate');
    if (added) {
      setSrsCards(nextCards);
      void ReviewRepository.persist(nextCards);
      // Saving a card is a side action mid-loop — it must NOT complete the day's
      // mission or navigate away. Only completeMission (last sentence) does that.
      setProgress((p) => ({ ...p, reviewCardsCreated: nextCards.length }));
      setGam((g) => {
        let next = addXp(g, XP.save);
        next = awardBadge(next, 'first_card');
        if (nextCards.length >= 10) next = awardBadge(next, 'ten_cards');
        persistGam(next);
        return next;
      });
    }
    haptic('success');
    track('review_card_saved', { cardId: reviewCard.id, duplicate: !added });
    void refreshServer();
    // stay on the voice screen; lastSaveState drives an inline saved/dup confirmation
  }, [candidateCards, srsCards, persistGam, track, refreshServer]);

  const gradeReview = useCallback(
    (card: SrsCard, grade: Grade) => {
      haptic(grade === 'again' ? 'warn' : 'tap');
      setSrsCards((prev) => {
        const next = ReviewRepository.grade(prev, card, grade);
        void ReviewRepository.persist(next);
        return next;
      });
      setGam((g) => {
        const next = bumpQuest(addXp(g, XP.gradeReview), 'review2').state;
        persistGam(next);
        return next;
      });
      track('review_card_saved', { graded: grade, cardId: card.id });
      void refreshServer();
    },
    [persistGam, track, refreshServer],
  );

  const gradeLabel = useCallback((card: SrsCard, grade: Grade) => previewIntervalLabel(card, grade), []);

  const completeMission = useCallback(() => {
    setProgress((p) => ({ ...p, completedMissions: p.completedMissions + 1 }));
    setGam((g) => {
      const next = bumpQuest(addXp(g, XP.mission), 'mission').state;
      persistGam(next);
      return next;
    });
    haptic('success');
    track('practice_room_completed', { practiceRoomId: FIRST_PRACTICE_ROOM_ID });
    void refreshServer();
  }, [persistGam, track, refreshServer]);

  const updateSettings = useCallback((p: Partial<Settings>) => {
    if (p.uiLocale) setUiLocale(p.uiLocale); // swap the STRINGS table before the state update re-renders
    setSettings((prev) => {
      const next = { ...prev, ...p };
      void saveJSON(KEYS.settings, next);
      return next;
    });
  }, []);

  const completeOnboarding = useCallback(
    (c: OnboardingChoice) => {
      setSelectedPersonaId(c.personaId);
      void saveJSON(KEYS.selectedPersona, c.personaId);
      setSettings((prev) => {
        const next = { ...prev, dailyGoal: c.dailyGoal };
        void saveJSON(KEYS.settings, next);
        return next;
      });
      setOnboarded(true);
      void saveJSON(KEYS.onboarded, { done: true, level: c.level });
      haptic('success');
      setScreen('home');
      track('onboarding_completed', { personaId: c.personaId, level: c.level });
    },
    [track],
  );

  const checkHealth = useCallback(async () => {
    try {
      setHealthText(JSON.stringify(await UsageService.health()));
    } catch (e) {
      setHealthText(`error: ${String(e)}`);
    }
    track('backend_health_checked', { mode: apiInfo.mode });
  }, [track]);

  const resetData = useCallback(async () => {
    await clearAll();
    setSrsCards([]);
    setGam(initialGamState());
    setSettings(DEFAULT_SETTINGS);
    setUiLocale(DEFAULT_SETTINGS.uiLocale);
    setCourseProgress({});
    setProgress((p) => ({ ...p, completedMissions: 0, spokenSentenceCount: 0, reviewCardsCreated: 0 }));
    setOnboarded(false);
    haptic('warn');
  }, []);

  const exportData = useCallback(() => exportAll(), []);

  // ---- bootstrap ----
  const booted = useRef(false);
  useEffect(() => {
    if (booted.current) return;
    booted.current = true;
    const deepLink = initialScreenFromUrl();
    (async () => {
      await migrate();
      type StoredProgress = { date: string; completedMissions: number; spokenSentenceCount: number };
      const [personaList, roomList, ent, ob, st, savedPersona, storedCards, storedGam, storedProgress, storedCourseProgress] =
        await Promise.all([
          ContentService.personas(),
          ContentService.rooms(),
          EntitlementService.me(),
          loadJSON<{ done: boolean }>(KEYS.onboarded, { done: false }),
          loadJSON<Settings>(KEYS.settings, DEFAULT_SETTINGS),
          loadJSON<string>(KEYS.selectedPersona, DEFAULT_PERSONA_ID),
          ReviewRepository.list(),
          loadJSON<GamState | null>(KEYS.gamification, null),
          loadJSON<StoredProgress | null>(KEYS.progress, null),
          loadJSON<Record<string, boolean>>(KEYS.courseProgress, {}),
        ]);

      setPersonas(personaList);
      setRooms(roomList);
      setEntitlement(ent);
      // Settings persisted before uiLocale existed lack the field — merge defaults.
      const stFull: Settings = { ...DEFAULT_SETTINGS, ...st };
      setSettings(stFull);
      setUiLocale(stFull.uiLocale);
      setSelectedPersonaId(savedPersona);
      setSrsCards(storedCards);
      setCourseProgress(storedCourseProgress);

      const liveGam = registerActivity(storedGam ?? initialGamState());
      setGam(liveGam);
      persistGam(liveGam);

      const today = todayStr();
      const sameDay = storedProgress != null && storedProgress.date === today;
      setProgress({
        date: today,
        streakDays: liveGam.streakDays,
        completedMissions: sameDay ? storedProgress!.completedMissions : 0,
        spokenSentenceCount: sameDay ? storedProgress!.spokenSentenceCount : 0,
        reviewCardsCreated: storedCards.length,
      });

      const params =
        Platform.OS === 'web' && typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
      const forceOnboarding = params?.get('onboarding') === '1';
      const hasScreenParam = !!params?.get('screen');
      setOnboarded(forceOnboarding ? false : ob.done || (Platform.OS === 'web' && hasScreenParam));

      track('app_opened', { mode: apiInfo.mode });
      track('home_today_viewed');

      // Demo/screenshot navigation (web ?screen=) seeds ONE coherent snapshot so
      // every screen agrees: 1 saved card, 1 spoken sentence, 1 mission, and the
      // two immediate badges. Real native first-run never seeds (onboarding first).
      if (hasScreenParam && storedCards.length === 0) {
        const demoRoom = roomList.find((r) => r.id === FIRST_PRACTICE_ROOM_ID);
        const demoCard = {
          id: 'card_tired_today_001',
          front: demoRoom?.primaryPhraseKo ?? '오늘 너무 피곤했어',
          back: `${demoRoom?.primaryPhraseJa ?? '今日めっちゃ疲れた'}。`,
          example: 'A: 今日どうだった？ B: 今日めっちゃ疲れた。',
          tags: demoRoom?.tags ?? ['감정표현', '친구말투', '일상'],
        };
        const seededCards = ReviewRepository.add([], demoCard).cards;
        setSrsCards(seededCards);
        const seededGam = awardBadge(awardBadge(addXp(liveGam, 25), 'first_word'), 'first_card');
        setGam(seededGam);
        setProgress((p) => ({ ...p, spokenSentenceCount: 1, completedMissions: 1, reviewCardsCreated: seededCards.length }));
      }

      if (deepLink === 'voice' || deepLink === 'review') {
        const conv = await ConversationService.create(savedPersona, FIRST_PRACTICE_ROOM_ID);
        setConversationId(conv.conversationId);
        const turn = await ConversationService.turn(conv.conversationId, '나 오늘 너무 피곤했어. 일본어로 뭐라고 해?');
        setAssistantText(turn.assistantText);
        setSpokenText(turn.spokenText);
        setCorrections(turn.corrections);
        setCandidateCards(turn.reviewCards);
        // Seed a representative PARTIAL result so the diff/coaching is visible.
        const said = '今日めっちゃ疲た';
        const segs = diffChars(turn.spokenText, said);
        setSttResult(said);
        setSttStatus('partial');
        setSttNote('「れ」가 빠졌어요. 「つか-れ-た」 3박을 또박또박.');
        setCoachingNow(coachingLine(savedPersona, 'partial'));
        setDiff(segs);
        setAccuracy(accuracyOf(segs));
      }

      // Backend-backed catalog/recommendation/gamification (fixture stubs in mock mode).
      try {
        const [courseList, rec, sgam] = await Promise.all([
          ContentService.courses(),
          LearnerService.recommendations(),
          LearnerService.gamification(),
        ]);
        setCourses(courseList);
        setRecommendation(rec);
        setServerGam(sgam);
      } catch {
        // non-fatal; screens fall back to local data
      }
      void refreshSocial();

      setReady(true);
    })();
  }, [track, persistGam]);

  useEffect(() => {
    if (!ready) return;
    void saveJSON(KEYS.progress, {
      date: progress.date,
      completedMissions: progress.completedMissions,
      spokenSentenceCount: progress.spokenSentenceCount,
    });
  }, [ready, progress.date, progress.completedMissions, progress.spokenSentenceCount]);

  return {
    ready,
    onboarded,
    demoMode: DEMO_MODE,
    completeOnboarding,
    screen,
    navigate,
    personas,
    rooms,
    room,
    persona,
    selectedPersonaId,
    selectPersona,
    assistantText,
    spokenText,
    phraseIndex,
    practiceTotal: PRACTICE_TOTAL,
    currentPhraseKo: PRACTICE_SEQUENCE[phraseIndex]?.ko ?? '',
    nextPhrase,
    storyIndex,
    storyTotal: MINI_STORY_TOTAL,
    currentStory: MINI_STORIES[storyIndex] ?? null,
    storyChoiceId,
    storyCorrectCount,
    startStories,
    answerStory,
    nextStory,
    listeningIndex,
    listeningTotal: LISTENING_TOTAL,
    currentListening: LISTENING_ITEMS[listeningIndex] ?? null,
    listeningChoiceId,
    listeningCorrectCount,
    startListening,
    answerListening,
    answerListeningDictation,
    nextListening,
    wordBankIndex,
    wordBankTotal: WORD_BANK_TOTAL,
    currentWordBank: WORD_BANK_ITEMS[wordBankIndex] ?? null,
    wordBankSolved,
    wordBankCorrectCount,
    startWordBank,
    checkWordBank,
    nextWordBank,
    wordIndex,
    wordTotal: WORD_TOTAL,
    currentWord: WORD_ITEMS[wordIndex] ?? null,
    wordRevealed,
    wordKnownCount,
    startWords,
    revealWord,
    gradeWord,
    roleplayIndex,
    roleplayTotal: ROLEPLAY_TOTAL,
    currentRoleplay: ROLEPLAY_ITEMS[roleplayIndex] ?? null,
    roleplayRevealed,
    startRoleplay,
    revealRoleplay,
    nextRoleplay,
    sttResult,
    sttStatus,
    sttWarning,
    sttNote,
    coachingNow,
    diff,
    accuracy,
    corrections,
    candidateCards,
    srsCards,
    dueCards,
    reviewMode,
    setReviewMode,
    lastSaveState,
    progress,
    entitlement,
    courses,
    courseProgress,
    completeLesson,
    recommendation,
    serverGam,
    friends,
    friendRecs,
    shop,
    friendQuests,
    shopMessage,
    clearShopMessage,
    socialSettings,
    socialSaveState,
    socialBlocks,
    discovery,
    reputation,
    inviteFriend,
    acceptInvite,
    unfriend,
    purchaseReward,
    activateBoost,
    claimQuest,
    updateSocial,
    blockLearner,
    unblockLearner,
    gam,
    level: lp.level,
    levelPct: lp.pct,
    settings,
    updateSettings,
    speaking,
    healthText,
    apiInfo,
    speak,
    startPractice,
    submitTurn,
    runMockStt,
    saveReviewCard,
    gradeReview,
    gradeLabel,
    completeMission,
    checkHealth,
    resetData,
    exportData,
    track,
  };
}
