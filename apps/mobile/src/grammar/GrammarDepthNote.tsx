// Presentational depth block for the Grammar screen. Renders an optional
// '비슷한 표현' (similar-expression contrast) card and an optional '추가 예문'
// (extra examples) list. Safe to render with undefined props (returns null).
import React from 'react';
import { Text, View } from 'react-native';
import { Card, Muted, FuriganaTokens } from '../components';
import { useTheme } from '../ThemeContext';
import type { FuriTok } from './grammarData';

type ExtraExample = { ja: string; tokens: FuriTok[]; ko: string };

export function GrammarDepthNote({
  koPitfall,
  similar,
  extraExamples,
}: {
  koPitfall?: string;
  similar?: string;
  extraExamples?: ExtraExample[];
}) {
  const { theme } = useTheme();
  const hasPitfall = typeof koPitfall === 'string' && koPitfall.trim().length > 0;
  const hasSimilar = typeof similar === 'string' && similar.trim().length > 0;
  const hasExamples = Array.isArray(extraExamples) && extraExamples.length > 0;

  if (!hasPitfall && !hasSimilar && !hasExamples) return null;

  return (
    <View>
      {hasPitfall ? (
        <Card style={{ marginTop: 14, borderColor: theme.colors.bad }}>
          <View
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              marginBottom: 8,
            }}
          >
            <Text style={{ fontSize: 16 }}>⚠️</Text>
            <Text
              style={{
                fontSize: 15,
                fontWeight: '800',
                color: theme.colors.bad,
                marginLeft: 6,
              }}
            >
              한국인 함정
            </Text>
          </View>
          <Text
            style={{
              fontSize: 14,
              lineHeight: 22,
              color: theme.colors.text,
            }}
          >
            {koPitfall}
          </Text>
        </Card>
      ) : null}

      {hasSimilar ? (
        <Card style={{ marginTop: 14, borderColor: theme.colors.accentSoft }}>
          <View
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              marginBottom: 8,
            }}
          >
            <Text style={{ fontSize: 16 }}>🔍</Text>
            <Text
              style={{
                fontSize: 15,
                fontWeight: '800',
                color: theme.colors.accentDark,
                marginLeft: 6,
              }}
            >
              비슷한 표현과의 차이
            </Text>
          </View>
          <Text
            style={{
              fontSize: 14,
              lineHeight: 22,
              color: theme.colors.text,
            }}
          >
            {similar}
          </Text>
        </Card>
      ) : null}

      {hasExamples ? (
        <Card style={{ marginTop: 14 }}>
          <View
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              marginBottom: 10,
            }}
          >
            <Text style={{ fontSize: 16 }}>📝</Text>
            <Text
              style={{
                fontSize: 15,
                fontWeight: '800',
                color: theme.colors.text,
                marginLeft: 6,
              }}
            >
              추가 예문
            </Text>
          </View>
          {extraExamples!.map((ex, i) => (
            <View
              key={i}
              style={{
                marginTop: i === 0 ? 0 : 14,
                paddingTop: i === 0 ? 0 : 14,
                borderTopWidth: i === 0 ? 0 : 1,
                borderTopColor: theme.colors.border,
              }}
            >
              <FuriganaTokens tokens={ex.tokens} size={24} />
              <View style={{ marginTop: 6 }}>
                <Muted>{ex.ko}</Muted>
              </View>
            </View>
          ))}
        </Card>
      ) : null}
    </View>
  );
}
