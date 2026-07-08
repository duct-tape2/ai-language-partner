import React from 'react';
import { Text, View, Pressable } from 'react-native';
import { useTheme } from '../ThemeContext';
import { STRINGS } from '../i18n';
import { personaColor } from '../personaStyle';
import { Button, Card, Fade, Furigana, Muted, Pill, ProgressRing, Row, StreakFlame, Title } from '../components';
import { Icon, EMOJI_TO_ICON, type IconName } from '../icons';
import { Mascot } from '../characters/Mascot';
import { personaCoaching } from '../coaching';
import { nextActionLabel } from '../labels';
import { recommendNext } from '../mastery/masterySkills';
import type { AppController } from '../store';

function QuestRow({ label, progress, target }: { label: string; progress: number; target: number }) {
  const { theme } = useTheme();
  const done = progress >= target;
  return (
    <View style={{ marginTop: 10 }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
        <Text style={{ color: theme.colors.text, fontSize: 14, fontWeight: '600' }}>
          {done ? '✓ ' : ''}
          {label}
        </Text>
        <Text style={{ color: theme.colors.subtext, fontSize: 13 }}>
          {Math.min(progress, target)}/{target}
        </Text>
      </View>
      <View style={{ height: 7, borderRadius: 999, backgroundColor: theme.colors.track, marginTop: 5, overflow: 'hidden' }}>
        <View style={{ width: `${Math.min(100, (progress / target) * 100)}%`, height: 7, backgroundColor: done ? theme.colors.good : theme.colors.accent }} />
      </View>
    </View>
  );
}

export function HomeTodayScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const { room, persona, settings, progress, dueCards } = app;
  const ctaName = persona?.displayName ?? '유이';
  const goalPct = Math.min(1, progress.spokenSentenceCount / Math.max(1, settings.dailyGoal));

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Muted>{STRINGS.appTagline}</Muted>
          <StreakFlame days={progress.streakDays} />
        </View>
        <Title>{STRINGS.home.title}</Title>
      </Fade>

      <Fade delay={30}>
        <Button title={`${STRINGS.dailyTalk.entry} · ${ctaName}랑 실제 대화`} onPress={() => app.navigate('dailytalk')} color={personaColor(app.selectedPersonaId)} />
      </Fade>

      <Fade delay={35}>
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 2, marginBottom: 6 }}>
          {[
            { k: 'mastery' as const, icon: 'gauge' as IconName, label: '학습 현황' },
            { k: 'kanji' as const, icon: 'kanji' as IconName, label: '한자' },
            { k: 'grammar' as const, icon: 'book' as IconName, label: '문법' },
            { k: 'vocab' as const, icon: 'deck' as IconName, label: '어휘' },
            { k: 'exam' as const, icon: 'exam' as IconName, label: '모의고사' },
            { k: 'hub' as const, icon: 'grid' as IconName, label: '전체 학습' },
          ].map((m) => (
            <Pressable
              key={m.k}
              onPress={() => app.navigate(m.k)}
              accessibilityRole="button"
              accessibilityLabel={m.label}
              style={{ width: '31%', margin: '1.1%', backgroundColor: theme.colors.card, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 14, paddingVertical: 12, alignItems: 'center' }}
            >
              <Icon name={m.icon} size={24} color={theme.colors.accentDark} strokeWidth={1.9} />
              <Text style={{ fontSize: 12, fontWeight: '700', color: theme.colors.text, marginTop: 5 }}>{m.label}</Text>
            </Pressable>
          ))}
        </View>
      </Fade>

      <Fade delay={38}>
        <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
          <Muted>오늘의 추천 학습</Muted>
          {recommendNext(progress).map((s) => (
            <Pressable
              key={s.key}
              onPress={() => {
                app.track('home_reco_tapped', { key: s.key });
                app.navigate(s.navKey);
              }}
              accessibilityRole="button"
              accessibilityLabel={s.labelKo}
              style={{ flexDirection: 'row', alignItems: 'center', paddingVertical: 8 }}
            >
              <View style={{ width: 30 }}>
                {EMOJI_TO_ICON[s.icon] ? (
                  <Icon name={EMOJI_TO_ICON[s.icon]} size={22} color={theme.colors.accentDark} />
                ) : (
                  <Text style={{ fontSize: 20 }}>{s.icon}</Text>
                )}
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.text }}>{s.labelKo}</Text>
                <Text style={{ fontSize: 12, color: theme.colors.subtext }}>{s.blurbKo}</Text>
              </View>
              <Text style={{ fontSize: 18, color: theme.colors.subtext }}>›</Text>
            </Pressable>
          ))}
        </Card>
      </Fade>

      <Fade delay={40}>
        <View style={{ alignItems: 'center', marginBottom: 4 }}>
          <Mascot personaId={app.selectedPersonaId} size={132} speaking={app.speaking} outfit="scarf" />
          <View style={{ backgroundColor: theme.colors.card, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 16, paddingHorizontal: 14, paddingVertical: 8, marginTop: -8, maxWidth: 300 }}>
            <Text style={{ color: theme.colors.text, fontSize: 14, textAlign: 'center' }}>{personaCoaching(app.selectedPersonaId).opening}</Text>
          </View>
        </View>
      </Fade>

      <Fade delay={60}>
        <Card>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <ProgressRing size={92} stroke={10} pct={goalPct} centerTop={`${progress.spokenSentenceCount}/${settings.dailyGoal}`} centerBottom="문장" />
            <View style={{ flex: 1, marginLeft: 16 }}>
              <Text style={{ fontSize: 22, fontWeight: '900', color: theme.colors.text }}>{room?.primaryPhraseKo ?? '오늘 너무 피곤했어'}</Text>
              <View style={{ marginTop: 4 }}>
                <Furigana phrase={room?.primaryPhraseJa ?? '今日めっちゃ疲れた'} size={20} />
              </View>
            </View>
          </View>
          <Row>{(room?.tags ?? ['감정표현', '친구말투', '일상']).map((t) => <Pill key={t} label={t} />)}</Row>
        </Card>
      </Fade>

      <Fade delay={120}>
        <Button title={STRINGS.home.startWith(ctaName)} onPress={app.startPractice} secondary color={personaColor(app.selectedPersonaId)} />
      </Fade>

      <Fade delay={140}>
        <Card>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <View style={{ flex: 1, paddingRight: 10 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <Icon name="reading" size={18} color={theme.colors.text} />
                <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text, marginLeft: 6 }}>미니 스토리</Text>
              </View>
              <Muted>짧은 대화 속에서 오늘 표현을 이해해요</Muted>
            </View>
            <Pill label={`${app.storyTotal}개`} />
          </View>
          <Button title="맥락으로 이해하기" onPress={app.startStories} secondary color={personaColor(app.selectedPersonaId)} />
        </Card>
      </Fade>

      {app.recommendation && (
        <Fade delay={150}>
          <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
            <Muted>오늘의 추천 {app.apiInfo.mode === 'real' ? '(AI)' : ''}</Muted>
            <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.accentDark, marginTop: 2 }}>
              {nextActionLabel(app.recommendation.nextBestAction, app.recommendation.recommendedPracticeRooms[0]?.practiceRoom.title)}
            </Text>
            {app.recommendation.recommendedPracticeRooms.slice(0, 2).map((r) => (
              <Text key={r.practiceRoom.id} style={{ fontSize: 14, color: theme.colors.text, marginTop: 4 }}>
                · {r.practiceRoom.title} <Text style={{ color: theme.colors.subtext }}>— {r.reason}</Text>
              </Text>
            ))}
          </Card>
        </Fade>
      )}

      <Fade delay={160}>
        <Card>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text }}>{STRINGS.home.quests}</Text>
            <Text style={{ color: theme.colors.goldText, fontWeight: '800' }}>{STRINGS.progress.level(app.level)}</Text>
          </View>
          {app.gam.quests.map((q) => (
            <QuestRow key={q.id} label={q.label} progress={q.progress} target={q.target} />
          ))}
        </Card>
      </Fade>

      <Fade delay={200}>
        <Card>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <View>
              <Muted>{STRINGS.home.yesterdayReview}</Muted>
              <Text style={{ fontSize: 18, fontWeight: '700', color: theme.colors.text, marginTop: 2 }}>
                {dueCards.length > 0 ? STRINGS.home.dueReviews(dueCards.length) : STRINGS.home.savedCards(app.srsCards.length)}
              </Text>
            </View>
            {dueCards.length > 0 ? (
              <View style={{ backgroundColor: theme.colors.accent, borderRadius: 999, minWidth: 28, height: 28, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 8 }}>
                <Text style={{ color: '#fff', fontWeight: '800' }}>{dueCards.length}</Text>
              </View>
            ) : null}
          </View>
          <Button title={STRINGS.home.seeReviews} onPress={() => app.navigate('review')} secondary />
        </Card>
      </Fade>

      <Fade delay={240}>
        <Button title={STRINGS.home.pickPersona} onPress={() => app.navigate('personas')} secondary />
      </Fade>
    </View>
  );
}
