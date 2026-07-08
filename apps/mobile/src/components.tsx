import React, { useEffect, useRef } from 'react';
import { Animated, Easing, Platform, Pressable, Text, View, ViewStyle } from 'react-native';
import Svg, { Circle, Line, Path } from 'react-native-svg';
import { useTheme } from './ThemeContext';
import { Icon, type IconName } from './icons';
import { getFurigana, PITCH } from './i18n';
import type { FuriToken } from './i18n';
import type { DiffSeg } from './text';
import type { Grade } from './srs';

// ---------- motion ----------
export function Fade({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const { reducedMotion } = useTheme();
  const a = useRef(new Animated.Value(reducedMotion ? 1 : 0)).current;
  useEffect(() => {
    if (reducedMotion) return;
    Animated.timing(a, { toValue: 1, duration: 320, delay, easing: Easing.out(Easing.cubic), useNativeDriver: Platform.OS !== 'web' }).start();
  }, [a, delay, reducedMotion]);
  const translateY = a.interpolate({ inputRange: [0, 1], outputRange: [10, 0] });
  return <Animated.View style={{ opacity: a, transform: [{ translateY }] }}>{children}</Animated.View>;
}

export function Press({
  children,
  onPress,
  style,
  accessibilityLabel,
  selected,
}: {
  children: React.ReactNode;
  onPress?: () => void;
  style?: ViewStyle;
  accessibilityLabel?: string;
  selected?: boolean;
}) {
  const { reducedMotion } = useTheme();
  const s = useRef(new Animated.Value(1)).current;
  const to = (v: number) =>
    reducedMotion ? null : Animated.spring(s, { toValue: v, useNativeDriver: Platform.OS !== 'web', speed: 40, bounciness: 6 }).start();
  return (
    <Pressable
      onPress={onPress}
      onPressIn={() => to(0.96)}
      onPressOut={() => to(1)}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityState={selected != null ? { selected } : undefined}
    >
      <Animated.View style={[{ transform: [{ scale: s }] }, style]}>{children}</Animated.View>
    </Pressable>
  );
}

// ---------- primitives ----------
export function Card({ children, style }: { children: React.ReactNode; style?: ViewStyle }) {
  const { theme } = useTheme();
  return (
    <View
      style={[
        {
          backgroundColor: theme.colors.card,
          borderRadius: theme.radius.lg,
          padding: 18,
          borderWidth: 1,
          borderColor: theme.colors.border,
          marginBottom: theme.spacing.md,
        },
        style,
      ]}
    >
      {children}
    </View>
  );
}

export function Button({
  title,
  onPress,
  secondary,
  disabled,
  color,
  tone,
  icon,
}: {
  title: string;
  onPress: () => void;
  secondary?: boolean;
  disabled?: boolean;
  color?: string;
  tone?: 'accent' | 'good' | 'bad' | 'neutral';
  icon?: IconName;
}) {
  const { theme } = useTheme();
  const base =
    color ??
    (tone === 'good' ? theme.colors.good : tone === 'bad' ? theme.colors.bad : tone === 'neutral' ? theme.colors.subtext : theme.colors.accent);
  const fg = secondary ? base : '#fff';
  return (
    <Press onPress={disabled ? undefined : onPress} accessibilityLabel={title}>
      <View
        style={{
          backgroundColor: secondary ? theme.colors.card : base,
          borderColor: base,
          borderWidth: 1,
          borderRadius: theme.radius.md,
          paddingVertical: 14,
          paddingHorizontal: 18,
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'center',
          marginVertical: 6,
          opacity: disabled ? 0.45 : 1,
        }}
      >
        {icon ? <Icon name={icon} size={18} color={fg} strokeWidth={2} /> : null}
        <Text style={{ color: fg, fontSize: 16, fontWeight: '700', marginLeft: icon ? 8 : 0 }}>{title}</Text>
      </View>
    </Press>
  );
}

export function Title({ children }: { children: React.ReactNode }) {
  const { theme } = useTheme();
  return <Text style={{ fontSize: 28, fontWeight: '800', color: theme.colors.text, marginBottom: 8 }}>{children}</Text>;
}

export function Muted({ children }: { children: React.ReactNode }) {
  const { theme } = useTheme();
  return <Text style={{ fontSize: 14, color: theme.colors.subtext, lineHeight: 21 }}>{children}</Text>;
}

export function Pill({ label, color }: { label: string; color?: string }) {
  const { theme } = useTheme();
  return (
    <View style={{ backgroundColor: theme.colors.chip, borderRadius: 999, paddingHorizontal: 12, paddingVertical: 6, marginRight: 8, marginTop: 8 }}>
      <Text style={{ color: color ?? theme.colors.chipText, fontSize: 13, fontWeight: '600' }}>{label}</Text>
    </View>
  );
}

export function Row({ children }: { children: React.ReactNode }) {
  return <View style={{ flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center' }}>{children}</View>;
}

export function Stat({ label, value }: { label: string; value: string | number }) {
  const { theme } = useTheme();
  return (
    <View style={{ flex: 1, alignItems: 'center' }}>
      <Text style={{ fontSize: 28, fontWeight: '900', color: theme.colors.accentDark }}>{value}</Text>
      <Text style={{ fontSize: 13, color: theme.colors.subtext, marginTop: 4, textAlign: 'center' }}>{label}</Text>
    </View>
  );
}

// ---------- progress ring (SVG) ----------
export function ProgressRing({
  size = 120,
  stroke = 12,
  pct,
  color,
  centerTop,
  centerBottom,
}: {
  size?: number;
  stroke?: number;
  pct: number; // 0..1
  color?: string;
  centerTop?: string;
  centerBottom?: string;
}) {
  const { theme, reducedMotion } = useTheme();
  const c = color ?? theme.colors.accent;
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const anim = useRef(new Animated.Value(reducedMotion ? pct : 0)).current;
  const [shown, setShown] = React.useState(reducedMotion ? pct : 0);
  useEffect(() => {
    const id = anim.addListener((v) => setShown(v.value));
    Animated.timing(anim, { toValue: pct, duration: reducedMotion ? 0 : 800, easing: Easing.out(Easing.cubic), useNativeDriver: false }).start();
    return () => anim.removeListener(id);
  }, [pct, anim, reducedMotion]);
  const dash = circ * Math.min(1, Math.max(0, shown));
  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <Svg width={size} height={size}>
        <Circle cx={size / 2} cy={size / 2} r={r} stroke={theme.colors.track} strokeWidth={stroke} fill="none" />
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke={c}
          strokeWidth={stroke}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circ}`}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </Svg>
      <View style={{ position: 'absolute', alignItems: 'center' }}>
        {centerTop ? <Text style={{ fontSize: 26, fontWeight: '900', color: theme.colors.text }}>{centerTop}</Text> : null}
        {centerBottom ? <Text style={{ fontSize: 12, color: theme.colors.subtext }}>{centerBottom}</Text> : null}
      </View>
    </View>
  );
}

// ---------- XP bar ----------
export function XPBar({ level, pct }: { level: number; pct: number }) {
  const { theme, reducedMotion } = useTheme();
  const w = useRef(new Animated.Value(reducedMotion ? pct : 0)).current;
  useEffect(() => {
    Animated.timing(w, { toValue: pct, duration: reducedMotion ? 0 : 700, easing: Easing.out(Easing.cubic), useNativeDriver: false }).start();
  }, [pct, w, reducedMotion]);
  const width = w.interpolate({ inputRange: [0, 1], outputRange: ['0%', '100%'] });
  return (
    <View>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 }}>
        <Text style={{ fontWeight: '800', color: theme.colors.goldText }}>Lv.{level}</Text>
        <Text style={{ color: theme.colors.subtext, fontSize: 12 }}>{Math.round(pct * 100)}%</Text>
      </View>
      <View style={{ height: 10, borderRadius: 999, backgroundColor: theme.colors.track, overflow: 'hidden' }}>
        <Animated.View style={{ width, height: 10, backgroundColor: theme.colors.gold, borderRadius: 999 }} />
      </View>
    </View>
  );
}

// ---------- furigana ----------
// Render explicit furigana tokens (e.g. from the dialogue-bank manifest). The
// dialogue bank uses arbitrary Japanese not in i18n's FURIGANA table, so it must
// supply its own tokens rather than go through the phrase-lookup path.
export function FuriganaTokens({ tokens, size = 28, color }: { tokens: FuriToken[]; size?: number; color?: string }) {
  const { theme } = useTheme();
  return (
    <View style={{ flexDirection: 'row', flexWrap: 'wrap', alignItems: 'flex-end' }}>
      {tokens.map((t, i) => (
        <View key={i} style={{ alignItems: 'center', marginRight: 2 }}>
          {/* furigana reading: larger + higher contrast for beginners (was 0.42 / faint subtext) */}
          <Text style={{ fontSize: size * 0.5, fontWeight: '700', color: theme.colors.text, height: t.r ? size * 0.6 : 0 }}>{t.r ?? ''}</Text>
          <Text style={{ fontSize: size, fontWeight: '900', color: color ?? theme.colors.accentDark }}>{t.b}</Text>
        </View>
      ))}
    </View>
  );
}

export function Furigana({ phrase, size = 28, color }: { phrase: string; size?: number; color?: string }) {
  return <FuriganaTokens tokens={getFurigana(phrase)} size={size} color={color} />;
}

// ---------- pronunciation diff ----------
export function DiffText({ segs, size = 22 }: { segs: DiffSeg[]; size?: number }) {
  const { theme } = useTheme();
  const wrong = segs.filter((s) => s.status === 'wrong').map((s) => s.ch);
  const label = wrong.length ? `인식 결과, 틀린 글자: ${wrong.join(', ')}` : `인식 결과 정확: ${segs.map((s) => s.ch).join('')}`;
  return (
    <View accessible accessibilityLabel={label} style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
      {segs.map((s, i) => (
        <Text
          key={i}
          style={{
            fontSize: size,
            fontWeight: '800',
            color: s.status === 'correct' ? theme.colors.good : theme.colors.bad,
            textDecorationLine: s.status === 'wrong' ? 'underline' : 'none',
          }}
        >
          {s.ch}
        </Text>
      ))}
    </View>
  );
}

// ---------- pitch accent contour ----------
export function PitchAccent({ phrase }: { phrase: string }) {
  const { theme } = useTheme();
  const pattern = PITCH[phrase];
  if (!pattern) return null;
  const n = pattern.length;
  const W = Math.min(320, Math.max(160, n * 30));
  const H = 46;
  const stepX = W / n;
  const yHigh = 12;
  const yLow = 30;
  const pts = pattern.map((m, i) => ({ x: stepX * i + stepX / 2, y: m.high ? yHigh : yLow }));
  let d = '';
  pts.forEach((p, i) => {
    d += i === 0 ? `M ${p.x} ${p.y}` : ` L ${p.x} ${p.y}`;
  });
  return (
    <View style={{ marginTop: 6 }}>
      <Svg width={W} height={H}>
        <Path d={d} stroke={theme.colors.accent} strokeWidth={2.5} fill="none" />
        {pts.map((p, i) => (
          <Circle key={i} cx={p.x} cy={p.y} r={4} fill={theme.colors.accent} />
        ))}
        <Line x1={0} y1={yLow + 8} x2={W} y2={yLow + 8} stroke={theme.colors.border} strokeWidth={1} />
      </Svg>
      <View style={{ flexDirection: 'row', width: W }}>
        {pattern.map((m, i) => (
          <Text key={i} style={{ width: stepX, textAlign: 'center', fontSize: 12, color: theme.colors.subtext }}>
            {m.mora}
          </Text>
        ))}
      </View>
    </View>
  );
}

// ---------- SRS grade buttons ----------
export function GradeButtons({
  labels,
  onGrade,
}: {
  labels: Record<Grade, string>;
  onGrade: (g: Grade) => void;
}) {
  const { theme } = useTheme();
  // Shape symbol in addition to color so grades are distinguishable without
  // relying on color alone (accessibility).
  const items: { g: Grade; text: string; color: string; sym: string }[] = [
    { g: 'again', text: '다시', color: theme.colors.bad, sym: '✕' },
    { g: 'hard', text: '어려움', color: theme.colors.near, sym: '△' },
    { g: 'good', text: '알맞음', color: theme.colors.good, sym: '○' },
    { g: 'easy', text: '쉬움', color: theme.colors.accent, sym: '◎' },
  ];
  return (
    <View style={{ flexDirection: 'row', marginTop: 8 }}>
      {items.map((it) => (
        <View key={it.g} style={{ flex: 1, marginHorizontal: 3 }}>
          <Press onPress={() => onGrade(it.g)} accessibilityLabel={`${it.text}, 다음 복습 ${labels[it.g]}`}>
            <View style={{ borderWidth: 1.5, borderColor: it.color, borderRadius: theme.radius.md, paddingVertical: 10, alignItems: 'center' }}>
              <Text style={{ color: it.color, fontSize: 15, fontWeight: '900' }}>{it.sym}</Text>
              <Text style={{ color: it.color, fontWeight: '800', marginTop: 1 }}>{it.text}</Text>
              <Text style={{ color: theme.colors.subtext, fontSize: 11, marginTop: 2 }}>{labels[it.g]}</Text>
            </View>
          </Press>
        </View>
      ))}
    </View>
  );
}

// ---------- segmented control ----------
export function Segmented<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  const { theme } = useTheme();
  return (
    <View style={{ flexDirection: 'row', backgroundColor: theme.colors.track, borderRadius: 999, padding: 4 }}>
      {options.map((o) => {
        const active = o.value === value;
        return (
          <Pressable
            key={o.value}
            onPress={() => onChange(o.value)}
            style={{ flex: 1 }}
            accessibilityRole="button"
            accessibilityLabel={o.label}
            accessibilityState={{ selected: active }}
          >
            <View style={{ paddingVertical: 8, alignItems: 'center', borderRadius: 999, backgroundColor: active ? theme.colors.card : 'transparent' }}>
              <Text style={{ fontWeight: active ? '800' : '500', color: active ? theme.colors.accentDark : theme.colors.subtext, fontSize: 13 }}>{o.label}</Text>
            </View>
          </Pressable>
        );
      })}
    </View>
  );
}

// ---------- badge ----------
export function BadgeChip({ emoji, label, earned }: { emoji: string; label: string; earned: boolean }) {
  const { theme } = useTheme();
  return (
    <View style={{ alignItems: 'center', width: 84, marginBottom: 12, opacity: earned ? 1 : 0.3 }}>
      <Text style={{ fontSize: 30 }}>{emoji}</Text>
      <Text style={{ fontSize: 11, color: theme.colors.subtext, textAlign: 'center', marginTop: 2 }}>{label}</Text>
    </View>
  );
}

// ---------- empty state ----------
// A friendly placeholder for demo/zero-data screens so they don't read as broken.
// icon + title + one-line description + optional CTA, centered in a soft card.
export function EmptyState({
  icon,
  title,
  desc,
  cta,
}: {
  icon: IconName;
  title: string;
  desc?: string;
  cta?: { label: string; onPress: () => void; icon?: IconName };
}) {
  const { theme } = useTheme();
  return (
    <View style={{ alignItems: 'center', paddingVertical: 28, paddingHorizontal: 16 }}>
      <View
        style={{
          width: 72,
          height: 72,
          borderRadius: 36,
          backgroundColor: theme.colors.accentSoft,
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: 14,
        }}
      >
        <Icon name={icon} size={34} color={theme.colors.accentDark} strokeWidth={1.7} />
      </View>
      <Text style={{ fontSize: 17, fontWeight: '800', color: theme.colors.text, textAlign: 'center' }}>{title}</Text>
      {desc ? <Text style={{ fontSize: 14, color: theme.colors.subtext, textAlign: 'center', marginTop: 6, lineHeight: 21, maxWidth: 300 }}>{desc}</Text> : null}
      {cta ? (
        <View style={{ marginTop: 14, alignSelf: 'stretch' }}>
          <Button title={cta.label} onPress={cta.onPress} icon={cta.icon} />
        </View>
      ) : null}
    </View>
  );
}

// ---------- streak flame (pulse) ----------
export function StreakFlame({ days }: { days: number }) {
  const { theme, reducedMotion } = useTheme();
  const s = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    if (reducedMotion) return;
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(s, { toValue: 1.15, duration: 700, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(s, { toValue: 1, duration: 700, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [s, reducedMotion]);
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center' }}>
      <Animated.View style={{ transform: [{ scale: s }] }}>
        <Icon name="flame" size={18} color={theme.colors.gold} strokeWidth={2} />
      </Animated.View>
      <Text style={{ fontSize: 16, fontWeight: '800', color: theme.colors.goldText, marginLeft: 6 }}>{days}일 연속</Text>
    </View>
  );
}
