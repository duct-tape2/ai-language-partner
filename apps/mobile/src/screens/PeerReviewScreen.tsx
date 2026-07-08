import React from 'react';
import { Text, View, Pressable } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Button, Card, Fade, FuriganaTokens, Muted, Pill, Row, Title } from '../components';
import type { AppController } from '../store';
import {
  PEER_REVIEW_ITEMS,
  PEER_REVIEW_TOTAL,
  MY_ANSWER_PROMPTS,
  type PeerReviewItem,
  type PeerReviewIssues,
} from '../social/peerReviewData';

type Tab = 'correct' | 'mine';
type Axis = keyof PeerReviewIssues;

const AXES: { key: Axis; label: string }[] = [
  { key: 'naturalness', label: '자연스러움' },
  { key: 'pronunciation', label: '발음' },
  { key: 'grammar', label: '문법' },
];

// Honest badge: no real social backend yet. Every entry point shows this.
function DemoBadge() {
  const { theme } = useTheme();
  return (
    <View
      style={{
        alignSelf: 'flex-start',
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: theme.colors.chip,
        borderRadius: 999,
        paddingHorizontal: 10,
        paddingVertical: 5,
        marginTop: 6,
      }}
    >
      <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.near, marginRight: 6 }}>데모</Text>
      <Text style={{ fontSize: 12, color: theme.colors.subtext }}>실제 커뮤니티 연동 예정</Text>
    </View>
  );
}

// Tappable 3-star row for one axis (1..3). Stars are the rating; taps update state.
function StarRow({
  label,
  value,
  onRate,
  color,
}: {
  label: string;
  value: number;
  onRate: (v: 1 | 2 | 3) => void;
  color: string;
}) {
  const { theme } = useTheme();
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 10 }}>
      <Text style={{ fontSize: 14, fontWeight: '700', color: theme.colors.text }}>{label}</Text>
      <View style={{ flexDirection: 'row' }}>
        {[1, 2, 3].map((n) => {
          const on = n <= value;
          return (
            <Pressable
              key={n}
              onPress={() => onRate(n as 1 | 2 | 3)}
              accessibilityRole="button"
              accessibilityLabel={`${label} ${n}점`}
              accessibilityState={{ selected: on }}
              hitSlop={6}
            >
              <Text style={{ fontSize: 24, marginLeft: 4, color: on ? color : theme.colors.track }}>
                {on ? '★' : '☆'}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

// ---- '교정하기' tab: list of other learners' answers, then a detail/rate view. ----
function CorrectTab({ app, color }: { app: AppController; color: string }) {
  const { theme } = useTheme();
  const [openId, setOpenId] = React.useState<string | null>(null);
  const [ratings, setRatings] = React.useState<PeerReviewIssues | null>(null);
  const [showFix, setShowFix] = React.useState(false);
  const [sentIds, setSentIds] = React.useState<string[]>([]);

  const item: PeerReviewItem | undefined = openId ? PEER_REVIEW_ITEMS.find((i) => i.id === openId) : undefined;

  const open = (it: PeerReviewItem) => {
    setOpenId(it.id);
    setRatings({ ...it.issues });
    setShowFix(false);
  };
  const close = () => {
    setOpenId(null);
    setRatings(null);
    setShowFix(false);
  };
  const rate = (axis: Axis, v: 1 | 2 | 3) => setRatings((r) => (r ? { ...r, [axis]: v } : r));
  const submit = () => {
    if (!item) return;
    app.track('peer_review_submitted', { id: item.id, ratings });
    setSentIds((prev) => (prev.includes(item.id) ? prev : [...prev, item.id]));
    close();
  };

  if (item && ratings) {
    return (
      <View>
        <Fade>
          <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
            <Muted>상황</Muted>
            <Text style={{ fontSize: 15, color: theme.colors.text, marginTop: 4 }}>{item.promptKo}</Text>
            <Text style={{ fontSize: 12, color: theme.colors.subtext, marginTop: 10 }}>{item.learnerName} 님의 답변</Text>
            <Text style={{ fontSize: 20, fontWeight: '800', color: theme.colors.text, marginTop: 4 }}>{item.learnerAnswerJa}</Text>
            <View style={{ marginTop: 8, alignSelf: 'flex-start' }}>
              <Button icon="speaker" title="이 답변 듣기" onPress={() => app.speak(item.learnerAnswerJa)} secondary color={color} />
            </View>
          </Card>
        </Fade>

        <Fade delay={60}>
          <Card>
            <Muted>모범답안</Muted>
            <View style={{ marginTop: 8 }}>
              <FuriganaTokens tokens={item.tokens} size={24} color={color} />
            </View>
            <View style={{ marginTop: 8, alignSelf: 'flex-start' }}>
              <Button icon="speaker" title="모범답안 듣기" onPress={() => app.speak(item.targetJa)} secondary color={color} />
            </View>
          </Card>
        </Fade>

        <Fade delay={120}>
          <Card style={{ borderColor: color, borderWidth: 1.5 }}>
            <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text }}>별점 평가</Text>
            <Muted>세 가지 축으로 이 답변을 평가해 주세요.</Muted>
            {AXES.map((a) => (
              <StarRow key={a.key} label={a.label} value={ratings[a.key]} onRate={(v) => rate(a.key, v)} color={color} />
            ))}
          </Card>
        </Fade>

        <Fade delay={160}>
          <Card>
            {showFix ? (
              <View>
                <Muted>추천 수정문</Muted>
                <Text style={{ fontSize: 19, fontWeight: '800', color: color, marginTop: 4 }}>{item.suggestedFixJa}</Text>
                <Text style={{ fontSize: 14, color: theme.colors.text, marginTop: 6, lineHeight: 21 }}>{item.suggestedFixKo}</Text>
                <View style={{ marginTop: 8, alignSelf: 'flex-start' }}>
                  <Button icon="speaker" title="수정문 듣기" onPress={() => app.speak(item.suggestedFixJa)} secondary color={color} />
                </View>
              </View>
            ) : (
              <Button title="추천 수정문 보기" onPress={() => setShowFix(true)} secondary color={color} />
            )}
          </Card>
        </Fade>

        <Fade delay={200}>
          <Button title="교정 보내기" onPress={submit} color={color} />
          <Button title="목록으로" onPress={close} secondary />
        </Fade>
      </View>
    );
  }

  return (
    <View>
      <Fade>
        <Muted>다른 학습자 {PEER_REVIEW_TOTAL}명의 답변이에요. 하나를 골라 평가하고 교정을 보내보세요.</Muted>
      </Fade>
      {PEER_REVIEW_ITEMS.map((it, i) => {
        const sent = sentIds.includes(it.id);
        return (
          <Fade key={it.id} delay={40 + i * 20}>
            <Pressable onPress={() => open(it)} accessibilityRole="button" accessibilityLabel={`${it.learnerName} 답변 교정하기`}>
              <Card>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text style={{ fontSize: 13, fontWeight: '700', color: theme.colors.subtext }}>{it.learnerName} 님</Text>
                  {sent ? (
                    <Text style={{ fontSize: 12, fontWeight: '800', color: theme.colors.good }}>교정 보냄 ✓</Text>
                  ) : (
                    <Text style={{ fontSize: 12, color: color, fontWeight: '700' }}>교정하기 →</Text>
                  )}
                </View>
                <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 6 }}>{it.promptKo}</Text>
                <Text style={{ fontSize: 17, fontWeight: '700', color: theme.colors.text, marginTop: 4 }}>{it.learnerAnswerJa}</Text>
              </Card>
            </Pressable>
          </Fade>
        );
      })}
    </View>
  );
}

// ---- '내 답변' tab: pick a prompt, see model answer. Recording+sharing is 데모. ----
function MineTab({ app, color }: { app: AppController; color: string }) {
  const { theme } = useTheme();
  const [pickId, setPickId] = React.useState<string>(MY_ANSWER_PROMPTS[0]?.id ?? '');
  const [saved, setSaved] = React.useState(false);
  const picked = MY_ANSWER_PROMPTS.find((p) => p.id === pickId) ?? MY_ANSWER_PROMPTS[0];
  if (!picked) return <Muted>준비된 상황이 없어요.</Muted>;

  return (
    <View>
      <Fade>
        <Card style={{ backgroundColor: theme.colors.accentSoft, borderColor: theme.colors.accentSoft }}>
          <Text style={{ fontSize: 14, color: theme.colors.text, lineHeight: 21 }}>
            내 답변을 녹음해 커뮤니티에 공유하고 다른 학습자의 교정을 받는 기능이에요. 지금은 녹음·공유가 데모라 모범답안만 확인할 수 있어요.
          </Text>
          <DemoBadge />
        </Card>
      </Fade>

      <Fade delay={60}>
        <Muted>상황 고르기</Muted>
        <Row>
          {MY_ANSWER_PROMPTS.map((p, i) => {
            const on = p.id === pickId;
            return (
              <Pressable
                key={p.id}
                onPress={() => {
                  setPickId(p.id);
                  setSaved(false);
                }}
                accessibilityRole="button"
                accessibilityLabel={`상황 ${i + 1}`}
                accessibilityState={{ selected: on }}
              >
                <View
                  style={{
                    borderWidth: 1.5,
                    borderColor: on ? color : theme.colors.border,
                    backgroundColor: on ? color : theme.colors.card,
                    borderRadius: 999,
                    paddingHorizontal: 14,
                    paddingVertical: 8,
                    marginRight: 8,
                    marginTop: 8,
                  }}
                >
                  <Text style={{ fontSize: 13, fontWeight: '800', color: on ? '#fff' : theme.colors.subtext }}>{i + 1}</Text>
                </View>
              </Pressable>
            );
          })}
        </Row>
      </Fade>

      <Fade delay={120}>
        <Card>
          <Muted>상황</Muted>
          <Text style={{ fontSize: 15, color: theme.colors.text, marginTop: 4 }}>{picked.promptKo}</Text>

          <View style={{ height: 1, backgroundColor: theme.colors.border, marginVertical: 14 }} />

          <Muted>모범답안</Muted>
          <View style={{ marginTop: 8 }}>
            <FuriganaTokens tokens={picked.tokens} size={24} color={color} />
          </View>
          <Row>
            <View style={{ marginTop: 10, marginRight: 8 }}>
              <Button icon="speaker" title="듣기" onPress={() => app.speak(picked.targetJa)} secondary color={color} />
            </View>
            <View style={{ marginTop: 10 }}>
              <Button icon="mic" title="녹음 (데모)" onPress={() => app.track('peer_review_record_demo', { id: picked.id })} secondary />
            </View>
          </Row>
        </Card>
      </Fade>

      <Fade delay={160}>
        {saved ? (
          <Card style={{ borderColor: theme.colors.good, borderWidth: 1.5 }}>
            <Text style={{ fontSize: 15, fontWeight: '800', color: theme.colors.good }}>오답노트에 저장했어요 ✓</Text>
            <Muted>복습 화면에서 다시 연습할 수 있어요. (데모)</Muted>
          </Card>
        ) : (
          <Button
            title="오답노트에 저장"
            onPress={() => {
              app.track('peer_review_saved_note', { id: picked.id });
              setSaved(true);
            }}
            color={color}
          />
        )}
      </Fade>
    </View>
  );
}

// Peer correction (커뮤니티 교정) MVP. Honest demo of the correction LOOP:
// review others' answers -> rate 3 axes -> send; or draft your own (record is 데모).
export function PeerReviewScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const color = personaColor(app.selectedPersonaId);
  const [tab, setTab] = React.useState<Tab>('correct');

  const tabs: { value: Tab; label: string }[] = [
    { value: 'correct', label: '교정하기' },
    { value: 'mine', label: '내 답변' },
  ];

  return (
    <View>
      <Fade>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title>커뮤니티 교정</Title>
          <Pill label={`${PEER_REVIEW_TOTAL}명`} />
        </View>
        <Muted>서로의 일본어 답변을 교정해 주는 학습 커뮤니티예요.</Muted>
        <DemoBadge />
      </Fade>

      <Fade delay={60}>
        <View style={{ flexDirection: 'row', backgroundColor: theme.colors.track, borderRadius: 999, padding: 4, marginTop: 14, marginBottom: 14 }}>
          {tabs.map((t) => {
            const on = t.value === tab;
            return (
              <Pressable
                key={t.value}
                onPress={() => setTab(t.value)}
                style={{ flex: 1 }}
                accessibilityRole="button"
                accessibilityLabel={t.label}
                accessibilityState={{ selected: on }}
              >
                <View style={{ paddingVertical: 9, alignItems: 'center', borderRadius: 999, backgroundColor: on ? theme.colors.card : 'transparent' }}>
                  <Text style={{ fontWeight: on ? '800' : '600', color: on ? color : theme.colors.subtext, fontSize: 14 }}>{t.label}</Text>
                </View>
              </Pressable>
            );
          })}
        </View>
      </Fade>

      {tab === 'correct' ? <CorrectTab app={app} color={color} /> : <MineTab app={app} color={color} />}

      <Fade delay={220}>
        <Button title="홈으로" onPress={() => app.navigate('home')} secondary />
      </Fade>
    </View>
  );
}
