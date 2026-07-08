export type Persona = {
  id: string;
  displayName: string;
  japaneseName?: string;
  role: string;
  voiceStyle: string;
  teachingStyle?: string;
  avatarEmoji?: string;
  defaultLanguageMix?: { ko: number; ja: number };
};

export type PracticeRoom = {
  id: string;
  title: string;
  primaryPhraseKo: string;
  primaryPhraseJa: string;
  alternativePhrasesJa: string[];
  personaId: string;
  scenario: string;
  openingMessage: string;
  courseId?: string;
  courseTitle?: string;
  unitId?: string;
  unitTitle?: string;
  unitOrder?: number;
  lessonId?: string;
  lessonTitle?: string;
  lessonOrder?: number;
  roomOrder?: number;
  tags: string[];
};

export type CourseLesson = {
  id: string;
  title: string;
  order: number;
  practiceRoomIds: string[];
};

export type CourseUnit = {
  id: string;
  title: string;
  order: number;
  skillTags: string[];
  lessons: CourseLesson[];
};

export type Course = {
  id: string;
  title: string;
  targetLanguage: string;
  nativeLanguage: string;
  level: string;
  descriptionKo?: string;
  units: CourseUnit[];
};

export type ContentBundleRequest = {
  courses: Course[];
  practiceRooms: PracticeRoom[];
};

export type ContentImportRequest = ContentBundleRequest & {
  dryRun?: boolean;
  replaceExisting?: boolean;
};

export type ContentImportedCounts = {
  courses: number;
  practiceRooms: number;
};

export type ContentSnapshotCounts = {
  courses: number;
  practiceRooms: number;
};

export type ContentQualityIssue = {
  code: string;
  message: string;
  pointer: string;
  [key: string]: unknown;
};

export type ContentQualityReport = {
  valid: boolean;
  errors: ContentQualityIssue[];
  warnings: ContentQualityIssue[];
  counts: {
    personas: number;
    courses: number;
    units: number;
    lessons: number;
    practiceRooms: number;
    practiceRoomRefs: number;
    roomsWithCoursePlacement: number;
  };
  courseIds: string[];
  missingPersonaIds: string[];
  missingPracticeRoomRefs: string[];
  duplicatePracticeRoomRefs: string[];
  orphanPracticeRoomIds: string[];
  referencedPracticeRoomIds: string[];
};

export type TranslationMemoryEntry = {
  id: string;
  sourceLanguage: string;
  targetLanguage: string;
  sourceText: string;
  targetText: string;
  tags: string[];
  sourceRef?: string | null;
  quality: number;
  createdBy?: string | null;
  createdAt: string;
  updatedAt: string;
};

export type TranslationMemoryEntryRequest = {
  sourceLanguage?: string;
  targetLanguage?: string;
  sourceText: string;
  targetText: string;
  tags?: string[];
  sourceRef?: string | null;
  quality?: number;
};

export type TranslationMemoryUpsertRequest = {
  entries: TranslationMemoryEntryRequest[];
};

export type TranslationMemorySuggestRequest = {
  sourceText: string;
  sourceLanguage?: string;
  targetLanguage?: string;
  limit?: number;
};

export type TranslationMemorySuggestion = TranslationMemoryEntry & {
  similarityScore: number;
  matchType: 'exact' | 'fuzzy';
};

export type TranslationMemoryListResponse = {
  entries: TranslationMemoryEntry[];
};

export type TranslationMemorySuggestResponse = {
  suggestions: TranslationMemorySuggestion[];
};

export type TranslationMemoryUpsertResponse = {
  ok: boolean;
  upsertedCounts: { entries: number };
};

export type ContentBulkQaRequest = ContentBundleRequest & {
  versionId?: string | null;
  useCurrent?: boolean;
  includeTranslationMemory?: boolean;
};

export type ContentBulkQaReport = {
  valid: boolean;
  qualityReport: ContentQualityReport;
  issues: ContentQualityIssue[];
  counts: {
    roomsChecked: number;
    translationMemoryExactMatches: number;
    translationMemoryFuzzyMatches: number;
    translationMemoryMissing: number;
    translationMemoryConflicts: number;
  };
  translationMemorySuggestions: Array<{
    practiceRoomId?: string;
    sourceText: string;
    targetText: string;
    suggestions: TranslationMemorySuggestion[];
  }>;
};

export type ContentBulkQaResponse = {
  ok: boolean;
  source: string;
  report: ContentBulkQaReport;
};

export type ContentVersionSummary = {
  id: string;
  label?: string | null;
  status: 'draft' | 'in_review' | 'approved' | 'rejected' | 'published';
  parentVersionId?: string | null;
  branchName?: string | null;
  source: string;
  createdBy?: string | null;
  submittedBy?: string | null;
  reviewedBy?: string | null;
  reviewNote?: string | null;
  createdAt: string;
  submittedAt?: string | null;
  reviewedAt?: string | null;
  publishedAt?: string | null;
  importedCounts: ContentImportedCounts;
  report: ContentQualityReport;
  snapshotCounts: ContentSnapshotCounts;
};

export type ContentVersion = ContentVersionSummary & {
  courses: Course[];
  practiceRooms: PracticeRoom[];
};

export type ContentImportResponse = {
  ok: boolean;
  dryRun: boolean;
  applied: boolean;
  importedCounts: ContentImportedCounts;
  version: ContentVersionSummary;
  report: ContentQualityReport;
};

export type ContentVersionsResponse = {
  versions: ContentVersionSummary[];
};

export type ContentVersionResponse = {
  version: ContentVersion;
};

export type ContentReviewRequest = {
  note?: string | null;
};

export type ContentBranchRequest = {
  label?: string | null;
  branchName?: string | null;
  assignee?: string | null;
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  dueAt?: string | null;
  note?: string | null;
};

export type ContentAssignmentRequest = {
  assignee: string;
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  dueAt?: string | null;
  note?: string | null;
  status?: 'todo' | 'in_progress' | 'blocked' | 'done';
};

export type ContentAssignmentStatusRequest = {
  status: 'todo' | 'in_progress' | 'blocked' | 'done';
  note?: string | null;
};

export type ContentAssignment = {
  id: string;
  versionId: string;
  versionStatus?: string;
  versionLabel?: string | null;
  parentVersionId?: string | null;
  branchName?: string | null;
  assignee: string;
  status: 'todo' | 'in_progress' | 'blocked' | 'done';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  note?: string | null;
  dueAt?: string | null;
  createdBy?: string | null;
  updatedBy?: string | null;
  createdAt: string;
  updatedAt: string;
  completedAt?: string | null;
};

export type ContentAssignmentsResponse = {
  assignments: ContentAssignment[];
};

export type ContentBranchResponse = {
  ok: boolean;
  version: ContentVersion;
  assignment?: ContentAssignment | null;
};

export type ContentAssignmentResponse = {
  ok: boolean;
  assignment: ContentAssignment;
};

export type ContentReleaseStatus = 'planned' | 'scheduled' | 'applied' | 'rolled_back' | 'canceled';
export type ContentReleaseStrategy = 'immediate' | 'scheduled' | 'canary';
export type ContentCatalogScope = 'incremental' | 'full_catalog';

export type ContentReleaseRequest = {
  versionId: string;
  title: string;
  releaseStrategy?: ContentReleaseStrategy;
  rolloutPercent?: number;
  catalogScope?: ContentCatalogScope;
  scheduledAt?: string | null;
  guardrails?: Record<string, unknown>;
  note?: string | null;
};

export type ContentReleaseApplyRequest = {
  confirmation: 'apply-content-release';
  force?: boolean;
  note?: string | null;
};

export type ContentReleaseRunDueRequest = {
  confirmation: 'run-due-content-releases';
  limit?: number;
};

export type ContentReleaseRollbackRequest = {
  confirmation: 'rollback-content-release';
  note?: string | null;
};

export type ContentOperationJobType = 'validate_bundle' | 'import_bundle' | 'run_due_releases';
export type ContentOperationJobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'canceled';
export type ContentOperationJobPriority = 'low' | 'normal' | 'high' | 'urgent';

export type ContentOperationJobRequest = {
  jobType: ContentOperationJobType;
  priority?: ContentOperationJobPriority;
  payload?: Record<string, unknown>;
};

export type ContentOperationJobRunNextRequest = {
  confirmation: 'run-next-content-operation-job';
};

export type ContentOperationJobCancelRequest = {
  confirmation: 'cancel-content-operation-job';
};

export type ContentOperationJob = {
  id: string;
  jobType: ContentOperationJobType;
  status: ContentOperationJobStatus;
  priority: ContentOperationJobPriority;
  payload: Record<string, unknown>;
  result: Record<string, unknown>;
  error?: string | null;
  createdBy?: string | null;
  claimedBy?: string | null;
  canceledBy?: string | null;
  createdAt: string;
  updatedAt: string;
  claimedAt?: string | null;
  completedAt?: string | null;
  canceledAt?: string | null;
};

export type ContentOperationJobsResponse = {
  jobs: ContentOperationJob[];
};

export type ContentOperationJobResponse = {
  ok?: boolean;
  job: ContentOperationJob;
};

export type ContentOperationJobRunNextResponse = {
  ok: boolean;
  job: ContentOperationJob | null;
  result?: Record<string, unknown>;
  error?: string | null;
};

export type ContentSchedulerRunStatus = 'running' | 'succeeded' | 'failed';

export type ContentSchedulerRunOnceRequest = {
  confirmation: 'run-content-scheduler-once';
  schedulerKey?: string;
  leaseOwner?: string;
  maxOperationJobs?: number;
  releaseLimit?: number;
};

export type ContentSchedulerRun = {
  id: string;
  schedulerKey: string;
  status: ContentSchedulerRunStatus;
  leaseOwner: string;
  actor?: string | null;
  startedAt: string;
  heartbeatAt: string;
  completedAt?: string | null;
  maxOperationJobs: number;
  releaseLimit: number;
  result: Record<string, unknown>;
  error?: string | null;
};

export type ContentSchedulerRunsResponse = {
  runs: ContentSchedulerRun[];
};

export type ContentSchedulerRunOnceResponse = {
  ok: boolean;
  run: ContentSchedulerRun;
  releaseWorker?: Record<string, unknown>;
  operationJobs?: Array<Record<string, unknown>>;
  error?: string | null;
};

export type ContentRelease = {
  id: string;
  versionId: string;
  title: string;
  status: ContentReleaseStatus;
  releaseStrategy: ContentReleaseStrategy;
  rolloutPercent: number;
  catalogScope: ContentCatalogScope;
  scheduledAt?: string | null;
  guardrails: Record<string, unknown>;
  note?: string | null;
  previousPublishedVersionId?: string | null;
  importedCounts: Partial<ContentImportedCounts>;
  rollbackImportedCounts: Partial<ContentImportedCounts>;
  createdBy?: string | null;
  appliedBy?: string | null;
  rolledBackBy?: string | null;
  createdAt: string;
  appliedAt?: string | null;
  rolledBackAt?: string | null;
  rollbackNote?: string | null;
  version?: ContentVersion | null;
  previousPublishedVersion?: ContentVersion | null;
};

export type ContentReleasesResponse = {
  releases: ContentRelease[];
};

export type ContentReleaseResponse = {
  ok: boolean;
  release: ContentRelease;
  report?: ContentQualityReport;
  version?: ContentVersion | null;
  previousPublishedVersion?: ContentVersion | null;
};

export type ContentReleaseRunDueResponse = {
  ok: boolean;
  ranAt: string;
  checkedCount: number;
  appliedCount: number;
  skippedCount: number;
  appliedReleases: ContentRelease[];
  skipped: Array<Record<string, unknown>>;
};

export type ExperimentStatus = 'draft' | 'running' | 'paused' | 'archived';

export type ExperimentVariant = {
  key: string;
  label: string;
  weight: number;
  payload: Record<string, unknown>;
};

export type ExperimentVariantRequest = {
  key: string;
  label?: string | null;
  weight?: number;
  payload?: Record<string, unknown>;
};

export type Experiment = {
  id: string;
  key: string;
  name: string;
  status: ExperimentStatus;
  variants: ExperimentVariant[];
  allocation: Record<string, unknown>;
  createdBy?: string | null;
  createdAt: string;
  updatedAt: string;
};

export type ExperimentRequest = {
  key: string;
  name: string;
  status?: ExperimentStatus;
  variants: ExperimentVariantRequest[];
  allocation?: Record<string, unknown>;
};

export type ExperimentStatusRequest = {
  status: ExperimentStatus;
};

export type ExperimentAssignment = {
  id: string;
  learnerId: string;
  experimentKey: string;
  experimentName?: string | null;
  experimentStatus?: ExperimentStatus;
  variantKey: string;
  variant: ExperimentVariant;
  assignedAt: string;
  exposureEventId?: string;
};

export type ExperimentEventRequest = {
  eventName: string;
  payload?: Record<string, unknown>;
};

export type ExperimentEvent = {
  id: string;
  learnerId: string;
  experimentKey: string;
  variantKey: string;
  eventName: string;
  payload: Record<string, unknown>;
  createdAt: string;
  assignment?: ExperimentAssignment;
};

export type ExperimentAnalyticsTotals = {
  assignmentCount: number;
  exposureEventCount: number;
  exposedLearnerCount: number;
  conversionEventCount: number;
  convertedLearnerCount: number;
  customEventCount: number;
};

export type ExperimentVariantAnalytics = {
  variantKey: string;
  variant: ExperimentVariant;
  assignmentCount: number;
  exposureEventCount: number;
  exposedLearnerCount: number;
  conversionEventCount: number;
  convertedLearnerCount: number;
  customEventCount: number;
  eventCounts: Record<string, number>;
  uniqueLearnerEventCounts: Record<string, number>;
  assignmentExposureRate: number;
  exposedConversionRate: number;
  assignmentConversionRate: number;
  conversionRateConfidenceInterval95?: {
    lower?: number | null;
    upper?: number | null;
  };
  baselineVariantKey?: string | null;
  absoluteLiftFromBaseline?: number | null;
  relativeLiftFromBaseline?: number | null;
  standardError?: number | null;
  zScore?: number | null;
  pValue?: number | null;
  confidenceInterval95?: {
    lower?: number | null;
    upper?: number | null;
  };
  statisticallySignificant?: boolean;
  sampleSizeWarning?: string | null;
  decisionEligible: boolean;
  firstAssignedAt?: string | null;
  lastAssignedAt?: string | null;
  firstEventAt?: string | null;
  lastEventAt?: string | null;
};

export type ExperimentAnalytics = {
  experiment: Experiment;
  minimumExposedLearners: number;
  statisticalSignificanceAlpha?: number;
  controlVariantKey?: string | null;
  totals: ExperimentAnalyticsTotals;
  variants: ExperimentVariantAnalytics[];
  bestObservedVariantKey?: string | null;
  decisionReady: boolean;
  winnerVariantKey?: string | null;
  decisionRecommendation?: 'collect_more_data' | 'no_statistically_significant_winner' | 'promote_winner';
  significantPositiveVariantKeys?: string[];
  analysisNotes: string[];
};

export type ExperimentsResponse = {
  experiments: Experiment[];
};

export type ExperimentResponse = {
  ok: boolean;
  experiment: Experiment;
};

export type ExperimentAssignmentsResponse = {
  assignments: ExperimentAssignment[];
  exposureLogged: boolean;
  assignmentCount: number;
};

export type ExperimentEventResponse = {
  ok: boolean;
  event: ExperimentEvent;
};

export type ExperimentAnalyticsResponse = {
  ok: boolean;
  analytics: ExperimentAnalytics;
};

export type ExperimentDecisionAction = 'collect_more_data' | 'promote_variant' | 'pause' | 'archive' | 'no_winner';

export type ExperimentDecisionRequest = {
  action?: 'auto' | ExperimentDecisionAction;
  variantKey?: string | null;
  minimumExposedLearners?: number;
  reason?: string | null;
  requireDecisionReady?: boolean;
  requireStatisticalSignificance?: boolean;
};

export type ExperimentDecisionApplyRequest = {
  confirmation: 'apply-experiment-decision';
  note?: string | null;
};

export type ExperimentDecision = {
  id: string;
  experimentKey: string;
  action: ExperimentDecisionAction;
  variantKey?: string | null;
  status: 'proposed' | 'applied';
  reason?: string | null;
  minimumExposedLearners: number;
  analyticsSnapshot: ExperimentAnalytics;
  guardrail: Record<string, unknown>;
  createdBy?: string | null;
  createdAt: string;
  appliedBy?: string | null;
  appliedAt?: string | null;
  applyNote?: string | null;
  experimentAfterApply?: Experiment | null;
};

export type ExperimentDecisionsResponse = {
  decisions: ExperimentDecision[];
};

export type ExperimentDecisionResponse = {
  ok: boolean;
  decision: ExperimentDecision;
  guardrail?: Record<string, unknown>;
  experiment?: Experiment | null;
};

export type ContentVersionWorkflowResponse = {
  ok: boolean;
  version: ContentVersion;
};

export type ContentVersionPublishResponse = {
  ok: boolean;
  version: ContentVersion;
  importedCounts: ContentImportedCounts;
  report: ContentQualityReport;
};

export type AuthRegisterRequest = {
  email: string;
  password: string;
  learnerId?: string;
  deviceLabel?: string;
  deviceId?: string;
};

export type AuthLoginRequest = {
  email: string;
  password: string;
  deviceLabel?: string;
  deviceId?: string;
};

export type AuthOidcRequest = {
  provider: string;
  idToken: string;
  nonce?: string;
  learnerId?: string;
  deviceLabel?: string;
  deviceId?: string;
};

export type AuthOAuthPkceStartRequest = {
  provider: string;
  redirectUri: string;
  codeChallenge: string;
  codeChallengeMethod?: 'S256';
  scope?: string;
  nonce?: string;
  learnerId?: string;
  deviceLabel?: string;
};

export type AuthOAuthPkceStartResponse = {
  ok: boolean;
  provider: string;
  authorizationUrl: string;
  state: string;
  nonce: string;
  redirectUri: string;
  codeChallengeMethod: 'S256';
  expiresAt: string;
};

export type AuthOAuthPkceCallbackRequest = {
  provider: string;
  state: string;
  code: string;
  codeVerifier: string;
  redirectUri: string;
  learnerId?: string;
  deviceLabel?: string;
  deviceId?: string;
};

export type EnterpriseSsoConnection = {
  id: string;
  provider: string;
  organizationName: string;
  domains: string[];
  redirectUris: string[];
  requiredEmailDomain?: string | null;
  status: 'enabled' | 'disabled';
  enabled: boolean;
  createdAt?: string | null;
  updatedAt?: string | null;
};

export type AuthSsoConnectionRequest = {
  provider: string;
  organizationName: string;
  domains: string[];
  redirectUris: string[];
  requiredEmailDomain?: string | null;
  status?: 'enabled' | 'disabled';
};

export type AuthSsoConnectionListResponse = {
  connections: EnterpriseSsoConnection[];
  count: number;
};

export type AuthSsoConnectionResponse = {
  ok: boolean;
  connection: EnterpriseSsoConnection;
};

export type AuthSsoDiscoveryResponse = {
  ok: boolean;
  emailDomain: string;
  matched: boolean;
  connection?: EnterpriseSsoConnection | null;
};

export type AuthSsoPkceStartRequest = {
  email: string;
  redirectUri: string;
  codeChallenge: string;
  codeChallengeMethod?: 'S256';
  scope?: string;
  nonce?: string;
  learnerId?: string;
  deviceLabel?: string;
};

export type AuthSsoPkceStartResponse = {
  ok: boolean;
  provider: string;
  connectionId: string;
  connection: EnterpriseSsoConnection;
  authorizationUrl: string;
  state: string;
  nonce: string;
  redirectUri: string;
  codeChallengeMethod: 'S256';
  expiresAt: string;
};

export type AuthSsoPkceCallbackRequest = {
  connectionId: string;
  state: string;
  code: string;
  codeVerifier: string;
  redirectUri: string;
  learnerId?: string;
  deviceLabel?: string;
  deviceId?: string;
};

export type AuthRefreshRequest = {
  refreshToken: string;
  deviceLabel?: string;
  deviceId?: string;
};

export type AuthChangePasswordRequest = {
  currentPassword: string;
  newPassword: string;
  deviceLabel?: string;
  deviceId?: string;
};

export type AuthDeleteAccountRequest = {
  password?: string;
  confirmation?: string;
};

export type AuthTrustDeviceRequest = {
  confirmation: 'trust-this-device';
  deviceLabel?: string;
  platform?: string;
  attestationProvider?: string;
  attestationSubject?: string;
  evidence?: Record<string, unknown>;
};

export type AuthDeviceAttestationChallengeRequest = {
  attestationProvider?: string;
  attestationSubject?: string;
};

export type AuthDeviceAttestationChallengeResponse = {
  challengeId: string;
  challenge: string;
  expiresAt: string;
  attestationProvider: string;
  attestationSubject: string;
  signatureAlgorithm: 'hmac-sha256' | 'rs256' | 'webauthn-es256';
  message: string;
};

export type AuthAccount = {
  id: string;
  email: string;
  learnerId: string;
  createdAt?: string | null;
  disabledAt?: string | null;
  authProvider: 'password' | 'oidc';
  identityProvider?: string | null;
};

export type AuthDeviceTrust = {
  deviceId?: string | null;
  status: 'not_bound' | 'untracked' | 'untrusted' | 'trusted' | 'revoked';
  trusted: boolean;
  attestationProvider?: string | null;
  attestationVerified: boolean;
  verificationMode:
    | 'not_bound'
    | 'untracked'
    | 'not_verified'
    | 'account_confirmed_not_platform_verified'
    | 'signed_challenge_hmac'
    | 'public_key_challenge_rs256'
    | 'webauthn_assertion_es256'
    | 'platform_verified';
  trustedAt?: string | null;
  revokedAt?: string | null;
};

export type AuthDevice = {
  id: string;
  deviceLabel?: string | null;
  platform?: string | null;
  trustStatus: 'untrusted' | 'trusted' | 'revoked';
  trusted: boolean;
  attestationProvider?: string | null;
  attestationVerified: boolean;
  verificationMode:
    | 'not_verified'
    | 'account_confirmed_not_platform_verified'
    | 'signed_challenge_hmac'
    | 'public_key_challenge_rs256'
    | 'webauthn_assertion_es256'
    | 'platform_verified';
  trustedAt?: string | null;
  revokedAt?: string | null;
  lastSeenAt?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
  isCurrent?: boolean;
};

export type AuthSession = {
  id: string;
  deviceLabel?: string | null;
  deviceBound?: boolean;
  deviceTrust?: AuthDeviceTrust;
  accessExpiresAt: string;
  refreshExpiresAt: string;
  revokedAt?: string | null;
  createdAt?: string | null;
  lastUsedAt?: string | null;
  isCurrent?: boolean;
};

export type AuthSessionsResponse = {
  sessions: AuthSession[];
  currentSessionId: string;
  activeSessionCount: number;
};

export type AuthDevicesResponse = {
  devices: AuthDevice[];
  currentDeviceId?: string | null;
  activeDeviceCount: number;
};

export type AuthTrustDeviceResponse = {
  ok: boolean;
  device: AuthDevice;
};

export type AuthRevokeDeviceResponse = {
  ok: boolean;
  revokedDeviceId: string;
  revokedSessionCount: number;
  device: AuthDevice;
};

export type AuthRevokeSessionResponse = {
  ok: boolean;
  revokedSessionId: string;
  selfRevoked: boolean;
};

export type AuthLogoutAllResponse = {
  ok: boolean;
  revokedCount: number;
  currentSessionKept: boolean;
};

export type AuthTokenResponse = {
  account: AuthAccount;
  tokenType: 'Bearer';
  accessTokenFormat: 'jwt_hs256';
  accessToken: string;
  refreshToken: string;
  accessExpiresAt: string;
  refreshExpiresAt: string;
  deviceTrust?: AuthDeviceTrust;
  oauth?: {
    provider: string;
    stateConsumed: boolean;
    codeExchangeMode: 'token_endpoint_id_token' | 'local_signed_code' | 'unconfigured';
  } | null;
  sso?: {
    connectionId: string;
    provider: string;
    identityProvider: string;
    organizationName: string;
    emailDomain: string;
  } | null;
};

export type Correction = {
  category: string;
  original: string;
  corrected: string;
  explanationKo: string;
  severity: 'minor' | 'medium' | 'important';
  isKoreanLiteral?: boolean;
};

export type ReviewCard = {
  id: string;
  learnerId?: string;
  front: string;
  back: string;
  example?: string;
  tags: string[];
  dueAt?: string;
  easeFactor?: number;
  intervalDays?: number;
  reviewCount?: number;
  lapses?: number;
  memoryStrengthDays?: number;
  memoryDifficulty?: number;
  lastReviewQuality?: number | null;
  recallProbability?: number;
  recallRisk?: 'new' | 'high' | 'medium' | 'low' | 'unknown';
  daysSinceReview?: number | null;
  lastReviewedAt?: string | null;
};

export type ReviewCardRequest = {
  id?: string;
  front: string;
  back: string;
  example?: string;
  tags?: string[];
  dueAt?: string;
};

export type UsageRecord = {
  llmInputTokens?: number;
  llmOutputTokens?: number;
  sttSeconds?: number;
  ttsCharacters?: number;
  ttsSeconds?: number;
  cacheHit?: boolean;
};

export type CreateConversationRequest = {
  personaId: string;
  practiceRoomId: string;
  mode: 'practice' | 'free_chat' | 'shadowing' | 'roleplay';
};

export type CreateConversationResponse = {
  conversationId: string;
  learnerId?: string;
  persona: Persona;
  practiceRoom: PracticeRoom;
};

export type CreateTurnRequest = {
  inputType: 'text' | 'audio' | 'mock_audio';
  text?: string;
  audioBase64?: string;
  requestTts?: boolean;
};

export type CreateTurnResponse = {
  conversationId: string;
  learnerId?: string;
  userText?: string;
  assistantText: string;
  spokenText: string;
  suggestedUserReply: string;
  audioUrl?: string | null;
  corrections: Correction[];
  reviewCards: ReviewCard[];
  usage: UsageRecord;
  pronunciation?: PronunciationScore;
};

export type TtsRequest = {
  text: string;
  personaId: string;
  language: 'ja' | 'ko' | 'en';
  speed?: number;
  emotion?: string;
};

export type TtsResponse = {
  audioUrl?: string | null;
  audioBase64?: string | null;
  provider:
    | 'mock'
    | 'local_tts'
    | 'external_tts'
    | 'device_speech'
    | 'openai_tts'
    | 'elevenlabs_tts'
    | 'openai_tts_fallback_mock'
    | 'elevenlabs_tts_fallback_mock';
  cacheHit: boolean;
  spokenText: string;
  durationMs?: number;
  contentType?: string;
};

export type SttResponse = {
  text: string;
  provider: 'mock' | 'local_stt' | 'external_stt' | 'openai_stt' | 'openai_stt_fallback_mock';
  confidence?: number;
};

export type TodayProgress = {
  date: string;
  streakDays: number;
  completedMissions: number;
  spokenSentenceCount: number;
  reviewCardsCreated: number;
  xpEarnedToday?: number;
  dailyQuestsCompleted?: number;
  dailyQuestCount?: number;
};

export type XpSummary = {
  learnerId: string;
  todayXp: number;
  weekXp: number;
  totalXp: number;
  eventCount: number;
  weekStart: string;
};

export type StreakSummary = {
  learnerId: string;
  currentStreak: number;
  longestStreak: number;
  activeDays: number;
  lastActiveDate?: string | null;
  isActiveToday: boolean;
};

export type DailyQuest = {
  key: string;
  title: string;
  metric: 'source_count' | 'xp_sum';
  source: string;
  target: number;
  progress: number;
  rawProgress: number;
  rewardXp: number;
  completed: boolean;
  completedAt?: string | null;
  dayKey: string;
};

export type LeaderboardEntry = {
  rank: number;
  learnerId: string;
  xp: number;
  eventCount: number;
  isCurrentLearner: boolean;
  leaderboardExcluded: boolean;
  exclusionReasons: string[];
};

export type WeeklyLeaderboard = {
  weekStart: string;
  weekEnd: string;
  entries: LeaderboardEntry[];
  currentLearnerRank?: number | null;
  excludedLearnerCount: number;
};

export type LeagueTier = {
  key: string;
  name: string;
  minWeeklyXp: number;
};

export type LeagueStatus = {
  currentTier: LeagueTier;
  nextTier?: LeagueTier | null;
  weekXp: number;
  progressToNextTier?: number | null;
  currentRank?: number | null;
  weekStart: string;
};

export type AchievementProgress = {
  key: string;
  title: string;
  description: string;
  level: number;
  maxLevel: number;
  metric: string;
  source: string;
  target: number;
  progress: number;
  rawProgress: number;
  completed: boolean;
  rewardGems: number;
  awarded: boolean;
  awardedAt?: string | null;
};

export type AchievementsSummary = {
  awardedCount: number;
  totalCount: number;
  trackCount: number;
  completedTrackCount: number;
  achievements: AchievementProgress[];
};

export type XpAbuseFlag = {
  id: string;
  learnerId: string;
  dayKey: string;
  reason: string;
  severity: string;
  status: 'open' | 'reviewing' | 'resolved' | 'dismissed';
  evidence: Record<string, unknown>;
  leaderboardExcluded: boolean;
  reviewedBy?: string | null;
  resolutionNote?: string | null;
  resolvedAt?: string | null;
  createdAt: string;
};

export type XpAbuseFlagsResponse = {
  flags: XpAbuseFlag[];
  count: number;
};

export type XpAbuseFlagReviewRequest = {
  status: 'open' | 'reviewing' | 'resolved' | 'dismissed';
  note?: string | null;
};

export type XpAbuseFlagReviewResponse = {
  ok: boolean;
  flag: XpAbuseFlag;
};

export type ReputationSignal = {
  key: string;
  label: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  weight: number;
  evidence: Record<string, unknown>;
};

export type ReputationSummary = {
  openXpAbuseFlagCount: number;
  blockingXpAbuseFlagCount: number;
  resolvedOrDismissedXpAbuseFlagCount: number;
  incomingBlockCount: number;
  outgoingBlockCount: number;
  weekXp: number;
  weekEventCount: number;
  weekSourceCount: number;
  deviceCount: number;
  trustedDeviceCount: number;
  untrustedDeviceCount: number;
  revokedDeviceCount: number;
  activeSessionCount: number;
};

export type LearnerReputationProfile = {
  learnerId: string;
  riskScore: number;
  riskBand: 'trusted' | 'low' | 'medium' | 'high' | 'critical';
  reviewRecommended: boolean;
  leaderboardEligible: boolean;
  latestSignalAt?: string | null;
  signals: ReputationSignal[];
  summary: ReputationSummary;
  xpAbuseFlags: XpAbuseFlag[];
};

export type LearnerReputationListResponse = {
  profiles: LearnerReputationProfile[];
  count: number;
};

export type FriendInviteRequest = {
  friendLearnerId: string;
  message?: string | null;
};

export type FriendInvite = {
  id: string;
  requesterLearnerId: string;
  addresseeLearnerId: string;
  status: 'pending' | 'accepted' | 'declined' | 'blocked';
  message?: string | null;
  createdAt: string;
  updatedAt: string;
  respondedAt?: string | null;
};

export type FriendRelationship = {
  id: string;
  learnerId: string;
  friendLearnerId: string;
  status: 'active' | 'removed';
  createdAt: string;
  updatedAt: string;
  removedAt?: string | null;
};

export type FriendsSummary = {
  learnerId: string;
  friends: FriendRelationship[];
  incomingInvites: FriendInvite[];
  outgoingInvites: FriendInvite[];
  friendCount: number;
};

export type FriendRecommendationProfile = {
  nativeLanguage: string;
  targetLanguage: string;
  level: string;
  jlptLevel: string;
};

export type FriendRecommendation = {
  learnerId: string;
  score: number;
  reasonCodes: string[];
  weekXp: number;
  eventCount: number;
  lastActiveAt?: string | null;
  profile: FriendRecommendationProfile;
  sharedSources: string[];
  alreadyFriend: boolean;
  pendingInvite: boolean;
};

export type FriendRecommendationsResponse = {
  learnerId: string;
  weekStart: string;
  weekEnd: string;
  recommendations: FriendRecommendation[];
  count: number;
  excludedFriendCount: number;
  excludedPendingInviteCount: number;
  excludedBlockedCount: number;
  excludedPrivateCount: number;
};

export type SocialSettings = {
  learnerId: string;
  discoverable: boolean;
  allowFriendInvites: boolean;
  showWeeklyXp: boolean;
  createdAt: string;
  updatedAt: string;
};

export type SocialSettingsRequest = {
  discoverable: boolean;
  allowFriendInvites: boolean;
  showWeeklyXp: boolean;
};

export type SocialBlock = {
  id: string;
  blockerLearnerId: string;
  blockedLearnerId: string;
  createdAt: string;
};

export type SocialBlocksResponse = {
  learnerId: string;
  blocks: SocialBlock[];
  count: number;
};

export type SocialBlockResponse = {
  block?: SocialBlock | null;
  blocked: boolean;
  reason: string;
};

export type SocialUnblockResponse = {
  unblocked: boolean;
  learnerId: string;
  blockedLearnerId: string;
};

export type SocialDiscoveryCandidate = {
  learnerId: string;
  score: number;
  reasonCodes: string[];
  weekXp?: number | null;
  eventCount: number;
  lastActiveAt?: string | null;
  profile: FriendRecommendationProfile;
  mutualFriendCount: number;
  mutualFriendLearnerIds: string[];
  canInvite: boolean;
  friendQuestEligible: boolean;
};

export type SocialDiscoveryResponse = {
  learnerId: string;
  weekStart: string;
  weekEnd: string;
  candidates: SocialDiscoveryCandidate[];
  count: number;
  excludedFriendOrPendingCount: number;
  excludedBlockedCount: number;
  excludedPrivateCount: number;
};

export type FriendInviteResponse = {
  invite?: FriendInvite | null;
  relationship?: FriendRelationship | null;
  created: boolean;
  reason: string;
};

export type FriendInviteAcceptResponse = {
  invite: FriendInvite;
  relationship?: FriendRelationship | null;
  accepted: boolean;
  alreadyResponded: boolean;
};

export type RemoveFriendResponse = {
  relationship: FriendRelationship;
  removed: boolean;
};

export type RewardCatalogItem = {
  key: string;
  type: string;
  title: string;
  description?: string | null;
  multiplier?: number | null;
  durationSeconds?: number | null;
  quantity?: number | null;
};

export type RewardCurrencyBalance = {
  currencyKey: string;
  balance: number;
};

export type RewardShopItem = {
  rewardKey: string;
  rewardType: string;
  title: string;
  description?: string | null;
  priceCurrency: string;
  priceAmount: number;
  available: boolean;
  active: boolean;
  affordable: boolean;
  dailyPurchaseLimit?: number | null;
  inventoryLimit?: number | null;
  startsAt?: string | null;
  endsAt?: string | null;
  sortOrder: number;
  purchasedToday: number;
  remainingDailyPurchases?: number | null;
  currentInventoryQuantity: number;
  remainingInventory?: number | null;
};

export type RewardShopResponse = {
  items: RewardShopItem[];
  balances: RewardCurrencyBalance[];
};

export type RewardShopPolicyItem = {
  rewardKey: string;
  rewardType: string;
  title: string;
  description?: string | null;
  priceCurrency: string;
  priceAmount: number;
  available: boolean;
  dailyPurchaseLimit?: number | null;
  inventoryLimit?: number | null;
  startsAt?: string | null;
  endsAt?: string | null;
  sortOrder: number;
  createdAt: string;
  updatedAt: string;
  updatedBy?: string | null;
};

export type RewardShopAdminResponse = {
  items: RewardShopPolicyItem[];
  count: number;
  catalog: RewardCatalogItem[];
};

export type RewardShopItemUpdateRequest = {
  priceCurrency: string;
  priceAmount: number;
  available: boolean;
  dailyPurchaseLimit?: number | null;
  inventoryLimit?: number | null;
  startsAt?: string | null;
  endsAt?: string | null;
  sortOrder: number;
};

export type RewardShopItemUpdateResponse = {
  item: RewardShopPolicyItem;
  updated: boolean;
};

export type RewardInventoryItem = {
  id: string;
  learnerId: string;
  rewardKey: string;
  rewardType: string;
  title: string;
  description?: string | null;
  quantity: number;
  metadata: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
};

export type ActiveXpBoost = {
  id: string;
  learnerId: string;
  rewardKey: string;
  multiplier: number;
  startedAt: string;
  expiresAt: string;
  source: string;
  metadata: Record<string, unknown>;
};

export type RewardInventorySummary = {
  items: RewardInventoryItem[];
  activeXpBoosts: ActiveXpBoost[];
  catalog: RewardCatalogItem[];
  balances: RewardCurrencyBalance[];
};

export type FriendQuest = {
  id: string;
  key: string;
  title: string;
  learnerId: string;
  partnerLearnerId: string;
  weekKey: string;
  weekStart: string;
  weekEnd: string;
  targetXp: number;
  learnerXp: number;
  partnerXp: number;
  combinedXp: number;
  progress: number;
  progressRatio: number;
  completed: boolean;
  claimed: boolean;
  claimedAt?: string | null;
  reward: RewardCatalogItem;
  createdAt: string;
  updatedAt: string;
};

export type FriendQuestsResponse = {
  friendQuests: FriendQuest[];
  suggestedPartnerLearnerId: string;
  weekStart: string;
  weekEnd: string;
};

export type FriendQuestClaimResponse = {
  quest: FriendQuest;
  rewardItem?: RewardInventoryItem | null;
  claimed: boolean;
  alreadyClaimed: boolean;
};

export type ActivateXpBoostResponse = {
  activeBoost?: ActiveXpBoost | null;
  inventory: RewardInventorySummary;
  activated: boolean;
};

export type RewardPurchaseResponse = {
  purchased: boolean;
  reason: string;
  inventoryItem?: RewardInventoryItem | null;
  shop: RewardShopResponse;
};

export type GamificationSummary = {
  xp: XpSummary;
  streak: StreakSummary;
  dailyQuests: DailyQuest[];
  friends: FriendsSummary;
  friendQuests: FriendQuest[];
  rewardInventory: RewardInventorySummary;
  activeXpBoosts: ActiveXpBoost[];
  weeklyLeaderboard: WeeklyLeaderboard;
  league: LeagueStatus;
  achievements: AchievementsSummary;
  xpAbuseFlags: XpAbuseFlag[];
};

export type Entitlement = {
  plan: 'master_sandbox' | 'free' | 'basic' | 'plus' | 'pro';
  voiceMinutesPerMonth: number | 'unlimited_for_master_sandbox';
  maxPersonas: number | 'unlimited';
  customPersona: boolean;
  reviewCardsLimit: number | 'unlimited';
  premiumVoices: boolean;
};

export type LearnerProfile = {
  learnerId?: string;
  nativeLanguage: string;
  targetLanguage: string;
  level: string;
  jlptLevel: string;
  goals: string[];
  weakTags: string[];
  preferredPersonaId: string;
};

export type PronunciationScore = {
  provider: string;
  expectedText: string;
  actualText: string;
  score: number;
  rating: string;
  scoringMode: string;
  acousticEvidencePresent: boolean;
  feedbackKo?: string;
};

export type UsageSummary = {
  llmInputTokens: number;
  llmOutputTokens: number;
  sttSeconds: number;
  ttsCharacters: number;
  ttsSeconds: number;
  ttsCacheHits: number;
  usageRecords: number;
  ttsCacheEntries: number;
  estimatedMode: string;
};

export type LearnerSignalSummary = {
  weakTags: Array<{ tag: string; count: number }>;
  correctionCategories: Array<{ category: string; count: number }>;
  lapseTags: Array<{ tag: string; count: number }>;
  recentPracticeRoomIds: string[];
  completedPracticeRoomIdsToday: string[];
  pressureTags: string[];
};

export type TagMemoryMastery = {
  tag: string;
  cardCount: number;
  averageRecallProbability: number;
  atRiskCount: number;
  lapses: number;
  masteryState: 'new' | 'fragile' | 'developing' | 'stable';
};

export type MemorySummary = {
  cardCount: number;
  reviewedCardCount: number;
  newCardCount: number;
  averageRecallProbability: number | null;
  atRiskCards: ReviewCard[];
  tagMastery: TagMemoryMastery[];
  pressureTags: string[];
  model: string;
};

export type RecommendationsResponse = {
  profile: LearnerProfile;
  progress: TodayProgress;
  dueReviewCards: ReviewCard[];
  recommendedPracticeRooms: Array<{ score: number; practiceRoom: PracticeRoom; reason: string }>;
  nextBestAction: string;
  signalSummary?: LearnerSignalSummary;
  memorySummary?: MemorySummary;
};

export const PROJECT_ID = 'ai-language-partner-mobile-shared-20260629-v1';
export const FIRST_PRACTICE_ROOM_ID = 'tired_today';
export const DEFAULT_PERSONA_ID = 'yui';
