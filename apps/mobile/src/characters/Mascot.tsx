import React, { useEffect, useRef } from 'react';
import { Animated, Easing, Image, Text, View } from 'react-native';
import { useTheme } from '../ThemeContext';
import { personaColor } from '../personaStyle';
import { Icon } from '../icons';

// 시로쿠마 — the fluffy white baby-bear art (the reference renders), brought to life
// with a 2.5D motion rig: ground shadow, idle bob/breathe/sway, squash/stretch,
// per-persona motion personality, an expression-driven reaction (joy bounce, sad
// droop, thinking tilt, listening lean), and a talking nod during TTS. The face is
// the rendered art (per persona: 유이 wave, 하루카 glasses+book, 렌 hoodie+wink).
export type Expression =
  | 'idle' | 'talking' | 'happy' | 'sad' | 'thinking' | 'wink' | 'cheer'
  | 'listening' | 'correcting' | 'tryagain';
export type Outfit = 'none' | 'scarf' | 'beanie';

const IMAGES: Record<string, number> = {
  yui: require('../../assets/persona_yui_cut.png'),
  haruka: require('../../assets/persona_haruka_cut.png'),
  ren: require('../../assets/persona_ren_cut.png'),
};

type Motion = { bobUp: number; bobDown: number; sway: number; tilt: number; breathe: number };
const MOTION: Record<string, Motion> = {
  yui: { bobUp: 9, bobDown: 3, sway: 5, tilt: 3, breathe: 1600 }, // bouncy, lively
  haruka: { bobUp: 4, bobDown: 2, sway: 2.5, tilt: 1.4, breathe: 2300 }, // calm, composed
  ren: { bobUp: 7, bobDown: 3, sway: 6.5, tilt: 4.5, breathe: 2000 }, // big, confident
};

export function Mascot({
  personaId,
  size = 150,
  expression = 'idle',
  speaking = false,
  displayName,
}: {
  personaId: string;
  size?: number;
  expression?: Expression;
  speaking?: boolean;
  outfit?: Outfit;
  displayName?: string;
}) {
  const { theme, reducedMotion } = useTheme();
  // Personas without dedicated art (e.g. the 5 extended voices) get a clean initial
  // badge in the persona color instead of borrowing another persona's face.
  const src = IMAGES[personaId];
  const hasImage = !!src;
  const initial = (displayName?.trim()?.[0] ?? personaId.charAt(0)).toUpperCase();
  const m = MOTION[personaId] ?? MOTION.yui;

  const bob = useRef(new Animated.Value(0)).current;
  const breathe = useRef(new Animated.Value(0)).current;
  const sway = useRef(new Animated.Value(0.5)).current;
  const react = useRef(new Animated.Value(0)).current;
  const talk = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (reducedMotion) return;
    const mk = (v: Animated.Value, dur: number) =>
      Animated.loop(
        Animated.sequence([
          Animated.timing(v, { toValue: 1, duration: dur, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
          Animated.timing(v, { toValue: 0, duration: dur, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        ]),
      );
    const a = mk(bob, m.breathe * 0.8);
    const b = mk(breathe, m.breathe);
    const c = mk(sway, 2600);
    a.start(); b.start(); c.start();
    return () => { a.stop(); b.stop(); c.stop(); };
  }, [bob, breathe, sway, reducedMotion, m.breathe]);

  const isJoy = expression === 'happy' || expression === 'cheer';
  const isSad = expression === 'sad';
  useEffect(() => {
    if (reducedMotion) return;
    if (isJoy || isSad) {
      react.setValue(0);
      Animated.spring(react, { toValue: 1, useNativeDriver: true, friction: 4, tension: 120 }).start();
    }
  }, [expression, react, reducedMotion, isJoy, isSad]);

  // talking nod during TTS (subtle vertical pulse, since the face art is fixed)
  useEffect(() => {
    if (!speaking || reducedMotion) { talk.stopAnimation(); talk.setValue(0); return; }
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(talk, { toValue: 1, duration: 160, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
        Animated.timing(talk, { toValue: 0, duration: 160, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [speaking, reducedMotion, talk]);

  // static tilt/offset for held expressions (body language when the face can't change)
  const leaning = expression === 'listening';
  const thinking = expression === 'thinking' || expression === 'correcting';
  const staticTilt = isSad ? '-5deg' : thinking ? '4deg' : leaning ? '-3deg' : '0deg';
  const staticShift = leaning ? -6 : 0;

  const translateY = Animated.add(
    bob.interpolate({ inputRange: [0, 1], outputRange: [m.bobDown, -m.bobUp] }),
    talk.interpolate({ inputRange: [0, 1], outputRange: [0, -3] }),
  );
  const breatheScale = breathe.interpolate({ inputRange: [0, 1], outputRange: [1, 1.03] });
  const squashY = bob.interpolate({ inputRange: [0, 1], outputRange: [0.98, 1.05] });
  const squashX = bob.interpolate({ inputRange: [0, 1], outputRange: [1.03, 0.97] });
  const swayRotate = sway.interpolate({ inputRange: [0, 1], outputRange: [`-${m.tilt}deg`, `${m.tilt}deg`] });
  const shadowScale = bob.interpolate({ inputRange: [0, 1], outputRange: [1.06, 0.82] });
  const shadowOpacity = bob.interpolate({ inputRange: [0, 1], outputRange: [0.16, 0.07] });
  const reactScale = react.interpolate({ inputRange: [0, 0.5, 1], outputRange: [1, isJoy ? 1.12 : 0.95, 1] });

  const h = size * 1.4;

  return (
    <View style={{ width: size, height: h, alignItems: 'center', justifyContent: 'flex-end' }}>
      <Animated.View
        style={{ position: 'absolute', bottom: h * 0.03, width: size * 0.5, height: size * 0.06, borderRadius: 999, backgroundColor: '#000', opacity: shadowOpacity, transform: [{ scaleX: shadowScale }] }}
      />
      <Animated.View
        style={{
          transform: [
            { translateX: staticShift },
            { translateY },
            { scaleX: squashX },
            { scaleY: squashY },
            { scale: breatheScale },
            { scale: reactScale },
            { rotate: swayRotate },
            { rotate: staticTilt },
          ],
        }}
      >
        {hasImage ? (
          <Image source={src} style={{ width: size, height: h, resizeMode: 'contain' }} />
        ) : (
          <View style={{ width: size, height: h, alignItems: 'center', justifyContent: 'center' }}>
            <View
              style={{
                width: size * 0.72,
                height: size * 0.72,
                borderRadius: size * 0.36,
                backgroundColor: personaColor(personaId),
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Text style={{ color: '#fff', fontSize: size * 0.34, fontWeight: '900' }}>{initial}</Text>
            </View>
          </View>
        )}
      </Animated.View>
      {isJoy && (
        <>
          <Icon name="sparkle" size={size * 0.18} color={theme.colors.gold} />
        </>
      )}
      {expression === 'thinking' && (
        <View style={{ position: 'absolute', top: h * 0.02, right: size * 0.02 }}>
          <Icon name="chat" size={size * 0.2} color={theme.colors.subtext} />
        </View>
      )}
    </View>
  );
}
