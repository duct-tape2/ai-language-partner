import React from 'react';
import { Pressable, Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Fade, Muted, Pill, Title } from '../components';
import { Icon, type IconName } from '../icons';
import type { AppController } from '../store';

// Practice Hub — every learning mode, grouped into curriculum sections so the
// growing module list stays navigable (기초→말하기→문자→문법→어휘→시험).
type Mode = { key: string; icon: IconName; label: string; desc: string; count?: number; onPress?: () => void };
type Section = { title: string; subtitle?: string; modes: Mode[] };

export function PracticeHubScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const color = personaColor(app.selectedPersonaId);
  const nav = (s: Parameters<AppController['navigate']>[0]) => () => app.navigate(s);

  const sections: Section[] = [
    {
      title: '오늘의 학습',
      subtitle: '여기서 시작하세요',
      modes: [
        { key: 'mastery', icon: 'gauge', label: '학습 현황', desc: '내 진도·약점·추천 학습 한눈에', onPress: nav('mastery') },
        { key: 'report', icon: 'report', label: '주간 리포트', desc: '이번 주 학습 요약과 응원', onPress: nav('report') },
        { key: 'quests', icon: 'flame', label: '데일리 퀘스트', desc: '오늘의 목표·스트릭·XP', onPress: nav('quests') },
        { key: 'insights', icon: 'bulb', label: '학습 인사이트', desc: '내 진도·SRS 성숙도·개선 제안', onPress: nav('insights') },
        { key: 'dailytalk', icon: 'chat', label: '일상대화', desc: '실제 대화처럼 말하고 바로 답 듣기', onPress: nav('dailytalk') },
        { key: 'review', icon: 'cards', label: '복습', desc: '저장한 카드 복습 (FSRS)', count: app.dueCards.length, onPress: nav('review') },
        { key: 'mistakes', icon: 'redo', label: '오답노트', desc: '틀린 문제만 다시 풀기', onPress: nav('mistakes') },
      ],
    },
    {
      title: '말하기 · 듣기',
      modes: [
        { key: 'speak', icon: 'mic', label: '따라 말하기', desc: '문장을 듣고 따라 말하기', count: app.practiceTotal, onPress: app.startPractice },
        { key: 'pronunciation', icon: 'waveform', label: '발음 채점', desc: '문장 읽고 발음 피드백 받기', onPress: nav('pronunciation') },
        { key: 'pronclinic', icon: 'ear', label: '발음 클리닉', desc: '장음·촉음·ん·억양 최소대립쌍 훈련', onPress: nav('pronclinic') },
        { key: 'peerreview', icon: 'people', label: '커뮤니티 교정', desc: '다른 학습자 답변 교정 (데모)', onPress: nav('peerreview') },
        { key: 'dialogueshadow', icon: 'speech', label: '회화 섀도잉', desc: '실전 대화 듣고 따라 말하기', onPress: nav('dialogueshadow') },
        { key: 'situations', icon: 'bag', label: '상황별 표현집', desc: '공항·호텔·식당… 바로 쓰는 문장', onPress: nav('situations') },
        { key: 'listen', icon: 'speaker', label: '듣기', desc: '듣고 뜻 고르기 / 받아쓰기', count: app.listeningTotal, onPress: app.startListening },
        { key: 'choukai', icon: 'headphones', label: '청해 연습', desc: '대화 듣고 질문에 답하기 (JLPT 청해)', onPress: nav('choukai') },
        { key: 'roleplay', icon: 'masks', label: '롤플레이', desc: '상황에 맞게 대답하기', count: app.roleplayTotal, onPress: app.startRoleplay },
        { key: 'voicegallery', icon: 'soundwave', label: '목소리 갤러리', desc: '페르소나별 실제 합성 음성 미리듣기', onPress: nav('voicegallery') },
      ],
    },
    {
      title: '문자 · 한자',
      modes: [
        { key: 'kanaChart', icon: 'kana', label: '가나 차트', desc: '히라가나·가타카나 표 + 발음', onPress: nav('kanaChart') },
        { key: 'kanji', icon: 'kanji', label: '한자 학습', desc: '음훈독·부수·획수·니모닉', onPress: nav('kanji') },
        { key: 'pitch', icon: 'pitch', label: '피치 악센트', desc: '억양 패턴 시각화 + 퀴즈', onPress: nav('pitch') },
      ],
    },
    {
      title: '문법 · 활용',
      modes: [
        { key: 'grammar', icon: 'book', label: '문법 설명', desc: 'N5·N4 문형 의미·접속·예문·비교', onPress: nav('grammar') },
        { key: 'conjugation', icon: 'shuffle', label: '활용 드릴', desc: '동사·형용사 활용 연습', onPress: nav('conjugation') },
        { key: 'keigo', icon: 'person', label: '존댓말·경어', desc: '존경어·겸양어 정리', onPress: nav('keigo') },
        { key: 'counters', icon: 'counter', label: '조수사', desc: '개·명·마리… 세는 말 읽기', onPress: nav('counters') },
        { key: 'numbers', icon: 'clock', label: '숫자·시간·날짜', desc: '헷갈리는 읽기 정리', onPress: nav('numbers') },
      ],
    },
    {
      title: '어휘 · 표현 · 문화',
      modes: [
        { key: 'vocab', icon: 'deck', label: '테마별 어휘', desc: '일상·음식·여행… 100+ 단어장', onPress: nav('vocab') },
        { key: 'words', icon: 'word', label: '단어 회상', desc: '뜻 보고 단어 떠올리기', count: app.wordTotal, onPress: app.startWords },
        { key: 'wordbank', icon: 'puzzle', label: '문장 조립', desc: '단어 칩으로 문장 만들기', count: app.wordBankTotal, onPress: app.startWordBank },
        { key: 'pitfalls', icon: 'alert', label: '자주 틀리는 일본어', desc: '한국인이 헷갈리는 표현 교정', onPress: nav('pitfalls') },
        { key: 'idioms', icon: 'quote', label: '관용구·사자성어', desc: '慣用句·四字熟語 + 한국어 대응', onPress: nav('idioms') },
        { key: 'culture', icon: 'lantern', label: '문화·매너', desc: '일본 생활·예절, 한국과의 차이', onPress: nav('culture') },
        { key: 'stories', icon: 'bookmark', label: '이야기', desc: '대화 맥락 이해하기', count: app.storyTotal, onPress: app.startStories },
      ],
    },
    {
      title: '시험 · 평가',
      modes: [
        { key: 'placement', icon: 'target', label: '배치 테스트', desc: '6문항으로 내 레벨·약점 확인', onPress: nav('placement') },
        { key: 'exam', icon: 'exam', label: 'N4 모의고사', desc: '36문항 + 해설로 실전 점검', onPress: nav('exam') },
        { key: 'n5exam', icon: 'exam', label: 'N5 모의고사', desc: '기초 20문항 + 해설', onPress: nav('n5exam') },
        { key: 'reading', icon: 'reading', label: '독해 연습', desc: '짧은 지문 + 문제 풀이', onPress: nav('reading') },
        { key: 'courses', icon: 'courses', label: '코스', desc: '학습 코스 고르기', onPress: nav('courses') },
        { key: 'premium', icon: 'gem', label: '소개·프리미엄', desc: '앱 차별점·무료/프리미엄·개인정보', onPress: nav('premium') },
      ],
    },
  ];

  return (
    <View>
      <Fade>
        <Title>연습 허브</Title>
        <Muted>가나부터 회화·시험까지, 매일 다른 방식으로 익혀요</Muted>
      </Fade>
      {sections.map((sec, si) => (
        <Fade key={sec.title} delay={40 + si * 30}>
          <View style={{ marginTop: si === 0 ? 8 : 18 }}>
            <View style={{ flexDirection: 'row', alignItems: 'baseline', marginBottom: 8 }}>
              <Text style={{ fontSize: 15, fontWeight: '900', color: theme.colors.accentDark }}>{sec.title}</Text>
              {sec.subtitle ? <Text style={{ fontSize: 12, color: theme.colors.subtext, marginLeft: 8 }}>{sec.subtitle}</Text> : null}
            </View>
            {sec.modes.map((m) => (
              <Pressable key={m.key} onPress={m.onPress} accessibilityRole="button" accessibilityLabel={m.label}>
                <View
                  style={{
                    flexDirection: 'row',
                    alignItems: 'center',
                    backgroundColor: theme.colors.card,
                    borderRadius: 14,
                    borderWidth: 1,
                    borderColor: theme.colors.border,
                    padding: 12,
                    marginBottom: 8,
                  }}
                >
                  <View style={{ width: 44, height: 44, borderRadius: 12, backgroundColor: theme.colors.chip, alignItems: 'center', justifyContent: 'center' }}>
                    <Icon name={m.icon} size={24} color={theme.colors.accentDark} strokeWidth={1.9} />
                  </View>
                  <View style={{ flex: 1, marginLeft: 12 }}>
                    <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.text }}>{m.label}</Text>
                    <Muted>{m.desc}</Muted>
                  </View>
                  {m.count != null && m.count > 0 ? <Pill label={`${m.count}`} color={color} /> : null}
                  <Text style={{ fontSize: 20, color: theme.colors.subtext, marginLeft: 6 }}>›</Text>
                </View>
              </Pressable>
            ))}
          </View>
        </Fade>
      ))}
    </View>
  );
}
