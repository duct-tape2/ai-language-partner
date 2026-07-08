import React from 'react';
import Svg, { Circle, Line, Path, Polyline, Rect, Text as SvgText } from 'react-native-svg';

// Inline single-color line-icon set built on react-native-svg (already a dependency).
// Replaces the emoji-as-icon usage app-wide so the UI reads as an app, not a document.
// Usage: <Icon name="mic" size={22} color={theme.colors.accentDark} />
// Convention: 24x24 viewBox, round caps/joins, stroke-based; a few "glyph" icons
// (kana/kanji/counter/word) render a real Japanese character which is on-brand for
// a language app and crisper than any drawn approximation.

export type IconName =
  | 'home' | 'pencil' | 'cards' | 'chart' | 'gear'
  | 'gauge' | 'report' | 'flame' | 'bulb' | 'chat'
  | 'redo' | 'mic' | 'waveform' | 'ear' | 'people'
  | 'speech' | 'bag' | 'speaker' | 'headphones' | 'soundwave'
  | 'masks' | 'kana' | 'kanji' | 'pitch' | 'book'
  | 'shuffle' | 'person' | 'counter' | 'clock' | 'deck'
  | 'word' | 'puzzle' | 'alert' | 'quote' | 'lantern'
  | 'reading' | 'courses' | 'target' | 'exam' | 'gem'
  | 'play' | 'check' | 'star' | 'lock' | 'sparkle'
  | 'close' | 'search' | 'bookmark' | 'grid';

function glyph(ch: string, color: string) {
  return (
    <SvgText
      x={12}
      y={12}
      fontSize={17}
      fontWeight="800"
      fill={color}
      stroke="none"
      textAnchor="middle"
      alignmentBaseline="central"
    >
      {ch}
    </SvgText>
  );
}

function paths(name: IconName, color: string): React.ReactNode {
  switch (name) {
    case 'home':
      return (
        <>
          <Path d="M4 11.5 L12 4 L20 11.5" />
          <Path d="M6 10.5 V20 H18 V10.5" />
          <Path d="M10 20 V14.5 H14 V20" />
        </>
      );
    case 'pencil':
      return (
        <>
          <Path d="M4 17.25 V20 H6.75 L17 9.75 L14.25 7 Z" />
          <Path d="M14.25 7 L17 4.25 L19.75 7 L17 9.75" />
        </>
      );
    case 'cards':
      return (
        <>
          <Rect x={4} y={7.5} width={12} height={12.5} rx={2} />
          <Path d="M8 7.5 V4 H20 V16.5" />
        </>
      );
    case 'chart':
      return (
        <>
          <Line x1={4} y1={20} x2={20} y2={20} />
          <Rect x={6} y={12} width={3} height={8} rx={1} />
          <Rect x={11} y={8} width={3} height={12} rx={1} />
          <Rect x={16} y={14} width={3} height={6} rx={1} />
        </>
      );
    case 'gear':
      return (
        <>
          <Circle cx={12} cy={12} r={2.7} />
          <Circle cx={12} cy={12} r={6} />
          {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => {
            const a = (deg * Math.PI) / 180;
            return (
              <Line key={deg} x1={12 + 6 * Math.cos(a)} y1={12 + 6 * Math.sin(a)} x2={12 + 8.6 * Math.cos(a)} y2={12 + 8.6 * Math.sin(a)} />
            );
          })}
        </>
      );
    case 'gauge':
      return (
        <>
          <Path d="M4 16 A8 8 0 0 1 20 16" />
          <Line x1={12} y1={16} x2={15.5} y2={11} />
          <Circle cx={12} cy={16} r={1.4} fill={color} stroke="none" />
        </>
      );
    case 'report':
      return (
        <>
          <Rect x={5} y={3} width={14} height={18} rx={2} />
          <Line x1={9} y1={16} x2={9} y2={13} />
          <Line x1={12} y1={16} x2={12} y2={10} />
          <Line x1={15} y1={16} x2={15} y2={12} />
        </>
      );
    case 'flame':
      return <Path d="M12 21 C8 21 6 18 6 15 C6 11 10 9 9 4 C12 6 13 8 13 10 C14 9 14.5 8 14.5 6.5 C17 9 18 12 18 15 C18 18 16 21 12 21 Z" />;
    case 'bulb':
      return (
        <>
          <Path d="M9 15.5 A5 5 0 1 1 15 15.5 C14.4 16.3 14 17 14 18 H10 C10 17 9.6 16.3 9 15.5 Z" />
          <Line x1={10} y1={20} x2={14} y2={20} />
          <Line x1={10.5} y1={22} x2={13.5} y2={22} />
        </>
      );
    case 'chat':
      return <Path d="M4 6 A2 2 0 0 1 6 4 H18 A2 2 0 0 1 20 6 V14 A2 2 0 0 1 18 16 H9 L5 20 V16 A2 2 0 0 1 4 14 Z" />;
    case 'redo':
      return (
        <>
          <Path d="M19 12 A7 7 0 1 1 16.5 6.6" />
          <Path d="M16.5 3 V7 H12.5" />
        </>
      );
    case 'mic':
      return (
        <>
          <Rect x={9} y={3} width={6} height={11} rx={3} />
          <Path d="M6 11 A6 6 0 0 0 18 11" />
          <Line x1={12} y1={17} x2={12} y2={21} />
          <Line x1={8} y1={21} x2={16} y2={21} />
        </>
      );
    case 'waveform':
      return (
        <>
          <Line x1={5} y1={10} x2={5} y2={14} />
          <Line x1={8} y1={6} x2={8} y2={18} />
          <Line x1={11} y1={9} x2={11} y2={15} />
          <Line x1={14} y1={4} x2={14} y2={20} />
          <Line x1={17} y1={8} x2={17} y2={16} />
          <Line x1={20} y1={11} x2={20} y2={13} />
        </>
      );
    case 'ear':
      return <Path d="M9 20 C7 18 6.5 15.5 6.5 11.5 A5.5 5.5 0 0 1 17.5 11.5 C17.5 14 15 14 15 16 A3 3 0 0 1 9.5 17" />;
    case 'people':
      return (
        <>
          <Circle cx={9} cy={8} r={3} />
          <Path d="M4 19 C4 15 14 15 14 19" />
          <Circle cx={16.5} cy={9} r={2.4} />
          <Path d="M14 18.5 C14.5 15.2 20 15.2 20 18.5" />
        </>
      );
    case 'speech':
      return (
        <>
          <Path d="M8 4 H20 A1.5 1.5 0 0 1 21.5 5.5 V10.5 A1.5 1.5 0 0 1 20 12 H17.5" />
          <Path d="M3.5 8 H14 A1.5 1.5 0 0 1 15.5 9.5 V15 A1.5 1.5 0 0 1 14 16.5 H8 L5 20 V16.5 H3.5 A1.5 1.5 0 0 1 2 15 V9.5 A1.5 1.5 0 0 1 3.5 8 Z" />
        </>
      );
    case 'bag':
      return (
        <>
          <Rect x={4} y={8} width={16} height={11} rx={2} />
          <Path d="M9 8 V6 A2 2 0 0 1 11 4 H13 A2 2 0 0 1 15 6 V8" />
          <Line x1={12} y1={8} x2={12} y2={19} />
        </>
      );
    case 'speaker':
      return (
        <>
          <Path d="M4 9 H7 L12 5 V19 L7 15 H4 Z" />
          <Path d="M15 9.5 A4 4 0 0 1 15 14.5" />
          <Path d="M17.5 7 A7 7 0 0 1 17.5 17" />
        </>
      );
    case 'headphones':
      return (
        <>
          <Path d="M5 14 V12 A7 7 0 0 1 19 12 V14" />
          <Rect x={3.5} y={13} width={3.5} height={6} rx={1.5} />
          <Rect x={17} y={13} width={3.5} height={6} rx={1.5} />
        </>
      );
    case 'soundwave':
      return (
        <>
          <Circle cx={12} cy={12} r={9} />
          <Line x1={8} y1={10} x2={8} y2={14} />
          <Line x1={11} y1={7.5} x2={11} y2={16.5} />
          <Line x1={13.5} y1={9.5} x2={13.5} y2={14.5} />
          <Line x1={16} y1={11} x2={16} y2={13} />
        </>
      );
    case 'masks':
      return (
        <>
          <Path d="M5 5 H19 V11 A7 7 0 0 1 5 11 Z" />
          <Circle cx={9.5} cy={9.5} r={0.9} fill={color} stroke="none" />
          <Circle cx={14.5} cy={9.5} r={0.9} fill={color} stroke="none" />
          <Path d="M9.5 13 Q12 15 14.5 13" />
        </>
      );
    case 'kana':
      return glyph('あ', color);
    case 'kanji':
      return glyph('文', color);
    case 'counter':
      return glyph('数', color);
    case 'word':
      return glyph('語', color);
    case 'pitch':
      return (
        <>
          <Path d="M4 15 H8 V8 H14 V15 H20" />
          <Circle cx={8} cy={8} r={1.4} fill={color} stroke="none" />
          <Circle cx={14} cy={8} r={1.4} fill={color} stroke="none" />
        </>
      );
    case 'book':
      return (
        <>
          <Path d="M12 6 C10 4.3 6.5 4.3 4.5 5 V18 C6.5 17.3 10 17.3 12 19 C14 17.3 17.5 17.3 19.5 18 V5 C17.5 4.3 14 4.3 12 6 Z" />
          <Line x1={12} y1={6} x2={12} y2={19} />
        </>
      );
    case 'shuffle':
      return (
        <>
          <Path d="M4 7 H7 C9 7 10.5 9.5 12 12 C13.5 14.5 15 17 17 17 H20" />
          <Path d="M4 17 H7 C8.5 17 9.5 15.5 10.5 14" />
          <Path d="M13.5 10 C14.5 8.5 15.5 7 17 7 H20" />
          <Path d="M17.5 4.5 L20.5 7 L17.5 9.5" />
          <Path d="M17.5 14.5 L20.5 17 L17.5 19.5" />
        </>
      );
    case 'person':
      return (
        <>
          <Circle cx={12} cy={8} r={3.2} />
          <Path d="M5 20 C5 15 19 15 19 20" />
        </>
      );
    case 'clock':
      return (
        <>
          <Circle cx={12} cy={12} r={8} />
          <Path d="M12 7 V12 L15.5 14" />
        </>
      );
    case 'deck':
      return (
        <>
          <Path d="M12 4 L20 8 L12 12 L4 8 Z" />
          <Path d="M4 12 L12 16 L20 12" />
          <Path d="M4 16 L12 20 L20 16" />
        </>
      );
    case 'puzzle':
    case 'grid':
      return (
        <>
          <Rect x={4} y={4} width={7} height={7} rx={1.6} />
          <Rect x={13} y={4} width={7} height={7} rx={1.6} />
          <Rect x={4} y={13} width={7} height={7} rx={1.6} />
          <Rect x={13} y={13} width={7} height={7} rx={1.6} />
        </>
      );
    case 'alert':
      return (
        <>
          <Path d="M12 4 L21 19 H3 Z" />
          <Line x1={12} y1={10} x2={12} y2={14} />
          <Circle cx={12} cy={16.6} r={0.7} fill={color} stroke="none" />
        </>
      );
    case 'quote':
      return (
        <>
          <Path d="M6 14 C6 11 7 9.2 10 8 M6 14 V11 H9" />
          <Path d="M14 14 C14 11 15 9.2 18 8 M14 14 V11 H17" />
        </>
      );
    case 'lantern':
      return (
        <>
          <Line x1={12} y1={3} x2={12} y2={5} />
          <Path d="M7 8 A5 5 0 0 1 17 8 V15 A5 5 0 0 1 7 15 Z" />
          <Line x1={7} y1={8} x2={17} y2={8} />
          <Line x1={7} y1={15} x2={17} y2={15} />
          <Line x1={12} y1={5} x2={12} y2={8} />
          <Line x1={12} y1={18} x2={12} y2={20} />
        </>
      );
    case 'reading':
      return (
        <>
          <Rect x={6} y={4} width={13} height={16} rx={1.6} />
          <Line x1={9} y1={4} x2={9} y2={20} />
          <Line x1={11.5} y1={9} x2={16} y2={9} />
          <Line x1={11.5} y1={12} x2={16} y2={12} />
          <Line x1={11.5} y1={15} x2={14} y2={15} />
        </>
      );
    case 'courses':
      return (
        <>
          <Rect x={4} y={15} width={16} height={4} rx={1} />
          <Rect x={5.5} y={10.5} width={13} height={4} rx={1} />
          <Rect x={7} y={6} width={10} height={4} rx={1} />
        </>
      );
    case 'target':
      return (
        <>
          <Circle cx={12} cy={12} r={8} />
          <Circle cx={12} cy={12} r={4.3} />
          <Circle cx={12} cy={12} r={1.2} fill={color} stroke="none" />
        </>
      );
    case 'exam':
      return (
        <>
          <Rect x={5} y={4} width={14} height={17} rx={2} />
          <Path d="M9 4 V2.8 H15 V4" />
          <Path d="M8.5 12 L10.5 14 L15 9.5" />
        </>
      );
    case 'gem':
      return (
        <>
          <Path d="M6 5 H18 L21 10 L12 21 L3 10 Z" />
          <Path d="M3 10 H21" />
          <Path d="M9 5 L12 21 M15 5 L12 21 M6.5 5 L9 10 M17.5 5 L15 10" />
        </>
      );
    case 'play':
      return <Path d="M7 5 L19 12 L7 19 Z" />;
    case 'check':
      return <Path d="M5 13 L10 18 L19 6" />;
    case 'star':
      return <Path d="M12 3 L14.6 9 L21 9.5 L16 13.8 L17.6 20 L12 16.5 L6.4 20 L8 13.8 L3 9.5 L9.4 9 Z" />;
    case 'lock':
      return (
        <>
          <Rect x={5} y={11} width={14} height={9} rx={2} />
          <Path d="M8 11 V8 A4 4 0 0 1 16 8 V11" />
        </>
      );
    case 'sparkle':
      return (
        <>
          <Path d="M12 4 C12.4 8 13 8.6 17 9 C13 9.4 12.4 10 12 14 C11.6 10 11 9.4 7 9 C11 8.6 11.6 8 12 4 Z" />
          <Path d="M18 14 C18.2 16 18.5 16.3 20.5 16.5 C18.5 16.7 18.2 17 18 19 C17.8 17 17.5 16.7 15.5 16.5 C17.5 16.3 17.8 16 18 14 Z" />
        </>
      );
    case 'close':
      return <Path d="M6 6 L18 18 M18 6 L6 18" />;
    case 'search':
      return (
        <>
          <Circle cx={11} cy={11} r={6} />
          <Line x1={15.5} y1={15.5} x2={20} y2={20} />
        </>
      );
    case 'bookmark':
      return <Path d="M7 4 H17 V20 L12 16 L7 20 Z" />;
    default:
      return null;
  }
}

export function Icon({
  name,
  size = 22,
  color = '#333',
  strokeWidth = 1.8,
}: {
  name: IconName;
  size?: number;
  color?: string;
  strokeWidth?: number;
}) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round">
      {paths(name, color)}
    </Svg>
  );
}

// Maps a legacy emoji string to an icon name so screens that still carry emoji
// data (e.g. content tables) can be migrated incrementally. Unknown → undefined.
export const EMOJI_TO_ICON: Record<string, IconName> = {
  '🏠': 'home', '📝': 'pencil', '🗂': 'cards', '🗂️': 'deck', '📈': 'chart', '⚙️': 'gear',
  '📊': 'gauge', '🔥': 'flame', '🔎': 'bulb', '🔍': 'search', '💬': 'chat', '🔁': 'redo',
  '🎙': 'mic', '🎙️': 'waveform', '👂': 'ear', '🤝': 'people', '🗣️': 'speech', '🗣': 'speech',
  '🧳': 'bag', '🔊': 'speaker', '🎧': 'headphones', '🎭': 'masks', '🈂️': 'kana', '🈷️': 'kanji',
  '🎵': 'pitch', '📘': 'book', '🔀': 'shuffle', '🙇': 'person', '🔢': 'counter', '🕐': 'clock',
  '🔤': 'word', '🧩': 'puzzle', '⚠️': 'alert', '🏮': 'lantern', '📔': 'book', '🎯': 'target',
  '🅰️': 'exam', '📖': 'reading', '📚': 'courses', '💎': 'gem', '▶️': 'play', '▶': 'play',
  '✅': 'check', '⭐': 'star', '🔒': 'lock', '✨': 'sparkle', '📋': 'exam', '🎴': 'cards',
};
