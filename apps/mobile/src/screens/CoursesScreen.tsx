import React, { useState } from 'react';
import { Pressable, Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { Button, Card, Fade, Muted, Pill, Row, Title } from '../components';
import { Icon } from '../icons';
import { STRINGS } from '../i18n';
import { courseLevelLabel, courseTitle } from '../labels';
import type { Course, CourseLesson, CourseUnit } from '../../../../packages/shared/src/types';
import type { AppController } from '../store';

// Course path: whatever GET /v1/courses returns renders as a vertical path of
// lesson nodes (locked / unlocked / completed). Lesson N+1 unlocks only when
// lesson N is completed; the first lesson is always open. Completion persists
// locally via the store's courseProgress map. Tapping an open lesson expands an
// honest MVP detail card (its practice rooms + "완료로 표시"); the hardwired
// speaking flow is offered only when the lesson covers that room.
type LessonNode = {
  unit: CourseUnit;
  lesson: CourseLesson;
  key: string;
  unitStart: boolean;
  done: boolean;
  unlocked: boolean;
};

function pathNodes(course: Course, progress: Record<string, boolean>): LessonNode[] {
  const nodes: LessonNode[] = [];
  let prevDone = true; // first lesson is always unlocked
  const units = [...course.units].sort((a, b) => a.order - b.order);
  for (const unit of units) {
    const lessons = [...unit.lessons].sort((a, b) => a.order - b.order);
    lessons.forEach((lesson, li) => {
      const key = `${course.id}:${lesson.id}`;
      const done = !!progress[key];
      nodes.push({ unit, lesson, key, unitStart: li === 0, done, unlocked: prevDone });
      prevDone = done;
    });
  }
  return nodes;
}

export function CoursesScreen({ app }: { app: AppController }) {
  const { theme } = useTheme();
  const { courses, courseProgress } = app;
  const [openKey, setOpenKey] = useState<string | null>(null);

  return (
    <View>
      <Fade>
        <Muted>{STRINGS.courses.title}</Muted>
        <Title>한국인을 위한 일본어</Title>
        <Muted>{app.apiInfo.mode === 'real' ? '학습 코스' : '학습 코스 (오프라인 미리보기)'}</Muted>
      </Fade>

      {courses.length === 0 && (
        <Fade delay={60}>
          <Card>
            <Muted>{STRINGS.courses.loading}</Muted>
          </Card>
        </Fade>
      )}

      {courses.map((c, ci) => {
        const nodes = pathNodes(c, courseProgress);
        const doneCount = nodes.filter((n) => n.done).length;
        return (
          <Fade key={c.id} delay={60 + ci * 60}>
            <Card>
              <Text style={{ fontSize: 20, fontWeight: '800', color: theme.colors.text }}>{courseTitle(c.id, c.title)}</Text>
              {c.descriptionKo ? <Muted>{c.descriptionKo}</Muted> : null}
              <Row>
                <Pill label={courseLevelLabel(c.level)} />
                <Pill label={`유닛 ${c.units.length}`} />
                <Pill label={STRINGS.courses.progressOf(doneCount, nodes.length)} color={doneCount > 0 ? theme.colors.good : undefined} />
              </Row>

              <View style={{ marginTop: 12 }}>
                {nodes.map((n, idx) => {
                  const state = n.done ? 'done' : n.unlocked ? 'open' : 'locked';
                  const circleBg = state === 'done' ? theme.colors.good : state === 'open' ? theme.colors.accent : theme.colors.track;
                  const open = openKey === n.key;
                  const tappable = state !== 'locked';
                  const rooms = n.lesson.practiceRoomIds.flatMap((id) => {
                    const r = app.rooms.find((x) => x.id === id);
                    return r ? [r] : [];
                  });
                  const pendingRooms = n.lesson.practiceRoomIds.length - rooms.length;
                  const canStartSpeaking = app.room != null && n.lesson.practiceRoomIds.includes(app.room.id);
                  return (
                    <View key={n.key}>
                      {n.unitStart && (
                        <Text style={{ fontSize: 15, fontWeight: '700', color: theme.colors.text, marginTop: idx === 0 ? 0 : 12, marginBottom: 4 }}>
                          {n.unit.order}. {n.unit.title}
                        </Text>
                      )}
                      <Pressable
                        onPress={tappable ? () => setOpenKey(open ? null : n.key) : undefined}
                        disabled={!tappable}
                        accessibilityRole="button"
                        accessibilityLabel={`${n.lesson.title}, ${state === 'done' ? '완료' : state === 'open' ? '열림' : '잠김'}`}
                        accessibilityState={{ disabled: !tappable, expanded: open }}
                      >
                        <View style={{ flexDirection: 'row', alignItems: 'stretch', opacity: tappable ? 1 : 0.5 }}>
                          <View style={{ width: 44, alignItems: 'center' }}>
                            <View style={{ width: 3, flex: 1, backgroundColor: idx === 0 ? 'transparent' : theme.colors.border }} />
                            <View style={{ width: 34, height: 34, borderRadius: 17, backgroundColor: circleBg, alignItems: 'center', justifyContent: 'center' }}>
                              <Icon
                                name={state === 'done' ? 'check' : state === 'open' ? 'play' : 'lock'}
                                size={16}
                                color={state === 'locked' ? theme.colors.subtext : '#fff'}
                              />
                            </View>
                            <View style={{ width: 3, flex: 1, backgroundColor: idx === nodes.length - 1 ? 'transparent' : theme.colors.border }} />
                          </View>
                          <View style={{ flex: 1, paddingVertical: 10 }}>
                            <Text style={{ fontSize: 16, fontWeight: '700', color: theme.colors.text }}>{n.lesson.title}</Text>
                            <Muted>
                              {state === 'locked' ? STRINGS.courses.locked : STRINGS.courses.roomCount(n.lesson.practiceRoomIds.length)}
                            </Muted>
                          </View>
                        </View>
                      </Pressable>

                      {open && tappable && (
                        <Fade>
                          <Card style={{ marginLeft: 44, borderColor: n.done ? theme.colors.good : theme.colors.accentSoft, borderWidth: 1.5 }}>
                            {rooms.map((r) => (
                              <View key={r.id} style={{ marginBottom: 10 }}>
                                <Text style={{ fontSize: 15, fontWeight: '700', color: theme.colors.text }}>{r.title}</Text>
                                <Text style={{ fontSize: 16, color: theme.colors.accentDark, fontWeight: '700', marginTop: 2 }}>{r.primaryPhraseJa}</Text>
                                <Muted>{r.primaryPhraseKo}</Muted>
                              </View>
                            ))}
                            {pendingRooms > 0 ? <Muted>{STRINGS.courses.pendingRooms(pendingRooms)}</Muted> : null}
                            {canStartSpeaking && <Button title={STRINGS.courses.startRoom} onPress={app.startPractice} />}
                            {n.done ? (
                              <Muted>{STRINGS.courses.completedLesson}</Muted>
                            ) : (
                              <Button title={STRINGS.courses.markDone} tone="good" onPress={() => app.completeLesson(c.id, n.lesson.id)} />
                            )}
                          </Card>
                        </Fade>
                      )}
                    </View>
                  );
                })}
              </View>
            </Card>
          </Fade>
        );
      })}
    </View>
  );
}
