import React from 'react';
import { ActivityIndicator, Platform, ScrollView, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { ThemeProvider, useTheme } from './src/ThemeContext';
import { PoseSheet } from './src/characters/PoseSheet';
import { STRINGS } from './src/i18n';
import { Icon, type IconName } from './src/icons';
import { useApp, type Screen } from './src/store';

const POSE_DEBUG = Platform.OS === 'web' && typeof window !== 'undefined' && new URLSearchParams(window.location.search).has('pose');
import {
  OnboardingScreen,
  HomeTodayScreen,
  PersonaSelectScreen,
  PracticeRoomScreen,
  VoicePracticeScreen,
  ReviewCardsScreen,
  ProgressScreen,
  SettingsScreen,
  CoursesScreen,
  FriendsScreen,
  RewardShopScreen,
  SecurityScreen,
  StoryScreen,
  ListeningScreen,
  PracticeHubScreen,
  WordScreen,
  WordBankScreen,
  RoleplayScreen,
  DailyTalkScreen,
  VoiceGalleryScreen,
  KanjiScreen,
  GrammarScreen,
  MockExamScreen,
  PlacementTestScreen,
  KanaChartScreen,
  CountersScreen,
  ConjugationScreen,
  NumbersTimeScreen,
  VocabDecksScreen,
  PitchAccentScreen,
  DialogueShadowScreen,
  KeigoScreen,
  PitfallsScreen,
  ReadingScreen,
  MistakesScreen,
  PronunciationScreen,
  MasteryScreen,
  SituationsScreen,
  CultureScreen,
  IdiomsScreen,
  PeerReviewScreen,
  PronClinicScreen,
  ReportScreen,
  ChoukaiScreen,
  N5ExamScreen,
  PremiumScreen,
  InsightsScreen,
  DailyQuestScreen,
} from './src/screens';

const TABS: { key: Screen; icon: IconName }[] = [
  { key: 'home', icon: 'home' },
  { key: 'hub', icon: 'pencil' },
  { key: 'review', icon: 'cards' },
  { key: 'progress', icon: 'chart' },
  { key: 'settings', icon: 'gear' },
];

function tabLabel(key: Screen): string {
  switch (key) {
    case 'home':
      return STRINGS.common.home;
    case 'hub':
      return STRINGS.common.tabPractice;
    case 'review':
      return STRINGS.common.tabReview;
    case 'progress':
      return STRINGS.common.tabProgress;
    case 'settings':
      return STRINGS.common.tabSettings;
    default:
      return key;
  }
}

function AppInner() {
  const { theme, mode } = useTheme();
  const app = useApp();
  const { screen } = app;

  if (POSE_DEBUG) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: theme.colors.bg }} edges={['top', 'bottom']}>
        <StatusBar style={mode === 'dark' ? 'light' : 'dark'} />
        <PoseSheet />
      </SafeAreaView>
    );
  }

  if (!app.ready) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: theme.colors.bg, alignItems: 'center', justifyContent: 'center' }} edges={['top', 'bottom']}>
        <StatusBar style={mode === 'dark' ? 'light' : 'dark'} />
        <ActivityIndicator color={theme.colors.accent} />
      </SafeAreaView>
    );
  }

  if (!app.onboarded) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: theme.colors.bg }} edges={['top', 'bottom']}>
        <StatusBar style={mode === 'dark' ? 'light' : 'dark'} />
        <ScrollView contentContainerStyle={{ padding: 20, flexGrow: 1 }}>
          <OnboardingScreen app={app} />
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.colors.bg }} edges={['top', 'bottom']}>
      <StatusBar style={mode === 'dark' ? 'light' : 'dark'} />
      <ScrollView contentContainerStyle={{ padding: 20, paddingBottom: 40 }} style={{ flex: 1 }}>
        {screen === 'home' && <HomeTodayScreen app={app} />}
        {screen === 'personas' && <PersonaSelectScreen app={app} />}
        {screen === 'practice' && <PracticeRoomScreen app={app} />}
        {screen === 'voice' && <VoicePracticeScreen app={app} />}
        {screen === 'review' && <ReviewCardsScreen app={app} />}
        {screen === 'progress' && <ProgressScreen app={app} />}
        {screen === 'settings' && <SettingsScreen app={app} />}
        {screen === 'courses' && <CoursesScreen app={app} />}
        {screen === 'friends' && <FriendsScreen app={app} />}
        {screen === 'shop' && <RewardShopScreen app={app} />}
        {screen === 'security' && <SecurityScreen app={app} />}
        {screen === 'story' && <StoryScreen app={app} />}
        {screen === 'listening' && <ListeningScreen app={app} />}
        {screen === 'hub' && <PracticeHubScreen app={app} />}
        {screen === 'words' && <WordScreen app={app} />}
        {screen === 'wordbank' && <WordBankScreen app={app} />}
        {screen === 'roleplay' && <RoleplayScreen app={app} />}
        {screen === 'dailytalk' && <DailyTalkScreen app={app} />}
        {screen === 'voicegallery' && <VoiceGalleryScreen app={app} />}
        {screen === 'kanji' && <KanjiScreen app={app} />}
        {screen === 'grammar' && <GrammarScreen app={app} />}
        {screen === 'exam' && <MockExamScreen app={app} />}
        {screen === 'placement' && <PlacementTestScreen app={app} />}
        {screen === 'kanaChart' && <KanaChartScreen app={app} />}
        {screen === 'counters' && <CountersScreen app={app} />}
        {screen === 'conjugation' && <ConjugationScreen app={app} />}
        {screen === 'numbers' && <NumbersTimeScreen app={app} />}
        {screen === 'vocab' && <VocabDecksScreen app={app} />}
        {screen === 'pitch' && <PitchAccentScreen app={app} />}
        {screen === 'dialogueshadow' && <DialogueShadowScreen app={app} />}
        {screen === 'keigo' && <KeigoScreen app={app} />}
        {screen === 'pitfalls' && <PitfallsScreen app={app} />}
        {screen === 'reading' && <ReadingScreen app={app} />}
        {screen === 'mistakes' && <MistakesScreen app={app} />}
        {screen === 'pronunciation' && <PronunciationScreen app={app} />}
        {screen === 'mastery' && <MasteryScreen app={app} />}
        {screen === 'situations' && <SituationsScreen app={app} />}
        {screen === 'culture' && <CultureScreen app={app} />}
        {screen === 'idioms' && <IdiomsScreen app={app} />}
        {screen === 'peerreview' && <PeerReviewScreen app={app} />}
        {screen === 'pronclinic' && <PronClinicScreen app={app} />}
        {screen === 'report' && <ReportScreen app={app} />}
        {screen === 'choukai' && <ChoukaiScreen app={app} />}
        {screen === 'n5exam' && <N5ExamScreen app={app} />}
        {screen === 'premium' && <PremiumScreen app={app} />}
        {screen === 'insights' && <InsightsScreen app={app} />}
        {screen === 'quests' && <DailyQuestScreen app={app} />}
      </ScrollView>

      <View style={{ flexDirection: 'row', borderTopWidth: 1, borderTopColor: theme.colors.border, backgroundColor: theme.colors.card, paddingVertical: 8 }}>
        {TABS.map((t) => {
          const active = screen === t.key;
          const label = tabLabel(t.key);
          return (
            <TouchableOpacity
              key={t.key}
              accessibilityRole="button"
              accessibilityLabel={label}
              accessibilityState={{ selected: active }}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              onPress={() => app.navigate(t.key)}
              style={{ flex: 1, alignItems: 'center', paddingVertical: 6 }}
            >
              <Icon name={t.icon} size={23} color={active ? theme.colors.accentDark : theme.colors.subtext} strokeWidth={active ? 2 : 1.7} />
              <Text style={{ fontSize: 13, marginTop: 3, fontWeight: active ? '800' : '600', color: active ? theme.colors.accentDark : theme.colors.subtext }}>{label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </SafeAreaView>
  );
}

// On web the app is often shown as a shared demo link in a wide desktop browser.
// Without a phone-width frame every card/button stretches full-width and looks
// crude. This constrains the app to a centered phone column on web only; native
// is a passthrough.
function WebFrame({ children }: { children: React.ReactNode }) {
  const { theme, mode } = useTheme();
  if (Platform.OS !== 'web') return <>{children}</>;
  const outerBg = mode === 'dark' ? '#050505' : '#cdc6ba';
  return (
    <View style={{ flex: 1, backgroundColor: outerBg, alignItems: 'center' }}>
      <View
        style={{
          flex: 1,
          width: '100%',
          maxWidth: 448,
          backgroundColor: theme.colors.bg,
          borderLeftWidth: 1,
          borderRightWidth: 1,
          borderColor: mode === 'dark' ? '#1c1c1c' : '#00000010',
          boxShadow: mode === 'dark' ? 'none' : '0 0 40px rgba(0,0,0,0.14)',
        }}
      >
        {children}
      </View>
    </View>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <WebFrame>
          <AppInner />
        </WebFrame>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
