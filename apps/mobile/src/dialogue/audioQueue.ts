// F4. Sentence-level audio queue. Real packs play pre-synthesized wav via expo-av;
// the fixture (uri === null) falls back to device TTS (expo-speech) so the full
// flow is demoable without real audio. cancel() powers barge-in.
//
// Plays are SERIALIZED on an internal chain so overlapping play() calls never run
// concurrently and corrupt shared state. Cancellation is scoped to a token so a new
// play() sequence cannot un-cancel an in-flight barge-in.
import { Audio } from 'expo-av';
import * as Speech from 'expo-speech';
import { personaVoice } from '../personaStyle';

export type PlayItem = {
  uri: string | null; // full audio URL/uri, or null → speak `text` via device TTS
  text: string;
  personaId: string;
};

type CancelToken = { cancelled: boolean };

export class AudioQueue {
  private current: Audio.Sound | null = null;
  private tail: Promise<void> = Promise.resolve();
  private token: CancelToken = { cancelled: false };
  private active = 0;

  play(items: PlayItem[]): Promise<void> {
    const token = this.token; // whichever sequence-token is live now
    this.tail = this.tail.catch(() => undefined).then(() => this.playInner(items, token));
    return this.tail;
  }

  isPlaying(): boolean {
    return this.active > 0 || this.current != null;
  }

  private async playInner(items: PlayItem[], token: CancelToken): Promise<void> {
    this.active++;
    try {
      for (const item of items) {
        if (token.cancelled) return;
        await this.playOne(item, token);
      }
    } finally {
      this.active--;
    }
  }

  private playOne(item: PlayItem, token: CancelToken): Promise<void> {
    if (item.uri) return this.playUri(item.uri, token);
    return this.speak(item.text, item.personaId, token);
  }

  private async playUri(uri: string, token: CancelToken): Promise<void> {
    let sound: Audio.Sound | null = null;
    try {
      const created = await Audio.Sound.createAsync({ uri }, { shouldPlay: true });
      sound = created.sound;
      if (token.cancelled) return;
      this.current = sound;
      await new Promise<void>((resolve) => {
        sound!.setOnPlaybackStatusUpdate((status) => {
          if (!status.isLoaded || status.didJustFinish) resolve();
        });
      });
    } finally {
      if (sound) {
        try {
          await sound.unloadAsync();
        } catch {
          // already unloaded
        }
        if (this.current === sound) this.current = null;
      }
    }
  }

  private speak(text: string, personaId: string, token: CancelToken): Promise<void> {
    const v = personaVoice(personaId);
    return new Promise<void>((resolve) => {
      if (token.cancelled || !text) return resolve();
      Speech.stop();
      Speech.speak(text, {
        language: 'ja-JP',
        rate: v.rate,
        pitch: v.pitch,
        onDone: () => resolve(),
        onStopped: () => resolve(),
        onError: () => resolve(),
      });
    });
  }

  cancel(): void {
    this.token.cancelled = true; // cancel everything queued under the live token
    this.token = { cancelled: false }; // future play() calls start fresh
    this.tail = Promise.resolve(); // drop the cancelled chain
    Speech.stop();
    const s = this.current;
    this.current = null;
    if (s) {
      s.stopAsync().catch(() => undefined);
      s.unloadAsync().catch(() => undefined);
    }
  }
}
