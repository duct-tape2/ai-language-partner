import React, { useState } from 'react';
import { Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { STRINGS } from '../i18n';
import { Button, Card, Fade, Furigana, GradeButtons, Muted, Pill, Row, Segmented, Title } from '../components';
import { Mascot } from '../characters/Mascot';
import type { ReviewMode, AppController } from '../store';
import type { Grade, SrsCard } from '../srs';

const MODE_DESC: Record<ReviewMode, string> = {
  shadow: '듣고 따라 말하며 발음을 훈련해요.',
  listen: '소리만 듣고 의미를 떠올려요. 피곤한 날 가볍게.',
  recall: '한국어만 보고 일본어를 스스로 떠올려요.',
};

export function ReviewCardsScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const { dueCards, reviewMode } = app;
  const [revealed, setRevealed] = useState(false);

  const active: SrsCard | undefined = dueCards[0];

  const onGrade = (g: Grade) => {
    if (!active) return;
    app.gradeReview(active, g);
    setRevealed(false);
  };

  const labels: Record<Grade, string> = active
    ? {
        again: app.gradeLabel(active, 'again'),
        hard: app.gradeLabel(active, 'hard'),
        good: app.gradeLabel(active, 'good'),
        easy: app.gradeLabel(active, 'easy'),
      }
    : { again: '', hard: '', good: '', easy: '' };

  return (
    <View>
      <Fade>
        {app.lastSaveState === 'saved' && (
          <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 4 }}>
            <Mascot personaId={app.selectedPersonaId} size={70} expression="cheer" />
            <Text style={{ flex: 1, marginLeft: 8, fontSize: 15, fontWeight: '700', color: theme.colors.accentDark }}>
              저장 완료! 오늘도 한 문장 늘었어요 🎉
            </Text>
          </View>
        )}
        <Title>{STRINGS.review.title}</Title>
        <Segmented<ReviewMode>
          value={reviewMode}
          onChange={app.setReviewMode}
          options={[
            { value: 'shadow', label: STRINGS.review.modeShadow },
            { value: 'listen', label: STRINGS.review.modeListen },
            { value: 'recall', label: STRINGS.review.modeRecall },
          ]}
        />
        <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 8 }}>{MODE_DESC[reviewMode]}</Text>
      </Fade>

      <Fade delay={60}>
        <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
          <Text style={{ fontSize: 18, fontWeight: '800', color: theme.colors.accentDark }}>
            {dueCards.length > 0
              ? STRINGS.review.dueNow(dueCards.length)
              : app.srsCards.length === 0
                ? STRINGS.review.noCardsYet
                : STRINGS.review.allDone}
          </Text>
          <Muted>{STRINGS.review.todaySaved(app.srsCards.length)}</Muted>
        </Card>
      </Fade>

      {active ? (
        <Fade delay={120}>
          <Card>
            <Muted>{STRINGS.review.front}</Muted>
            <Text style={{ fontSize: 24, fontWeight: '800', color: theme.colors.text }}>{active.front}</Text>

            {reviewMode === 'recall' && !revealed ? (
              <Button title="정답 보기" onPress={() => setRevealed(true)} secondary />
            ) : (
              <>
                <Muted>{STRINGS.review.back}</Muted>
                <View style={{ marginTop: 4 }}>
                  <Furigana phrase={active.back} size={26} />
                </View>
                {active.example ? <Muted>{active.example}</Muted> : null}
                <Row>{(active.tags ?? []).map((t) => <Pill key={t} label={t} />)}</Row>
                <Button title={STRINGS.review.replay} onPress={() => app.speak(active.back)} secondary />
              </>
            )}

            {(reviewMode !== 'recall' || revealed) && (
              <>
                <Text style={{ fontSize: 12, color: theme.colors.subtext, marginTop: 12 }}>
                  선택에 따라 다음 복습 날짜가 정해져요 (간격은 버튼 아래 표시).
                </Text>
                <GradeButtons labels={labels} onGrade={onGrade} />
              </>
            )}
          </Card>
        </Fade>
      ) : (
        <Fade delay={120}>
          <Card>
            {app.srsCards.length === 0 ? (
              <>
                <Text style={{ fontSize: 16, color: theme.colors.text }}>📇 {STRINGS.review.noCardsYet}</Text>
                <Muted>{STRINGS.review.noCardsYetHint}</Muted>
              </>
            ) : (
              <>
                <Text style={{ fontSize: 16, color: theme.colors.text }}>🎉 {STRINGS.review.allDone}</Text>
                <Muted>다음 복습은 예약돼 있어요. 새 표현을 더 연습해볼까요?</Muted>
              </>
            )}
            <Button title={STRINGS.home.startWith(app.persona?.displayName ?? '유이')} onPress={app.startPractice} />
          </Card>
        </Fade>
      )}

      <Fade delay={160}>
        <Button title={STRINGS.review.seeProgress} onPress={() => app.navigate('progress')} secondary />
      </Fade>
    </View>
  );
}
