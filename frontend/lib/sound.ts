const SOUND_KEY = "medtwin.sound";

export function isSoundOn(): boolean {
  try {
    return localStorage.getItem(SOUND_KEY) !== "off";
  } catch {
    return true;
  }
}

export function setSoundOn(on: boolean) {
  try {
    localStorage.setItem(SOUND_KEY, on ? "on" : "off");
  } catch {
    // Storage blocked (e.g. private window): the setting just won't be remembered.
  }
}

let lastPlayed = 0;

/**
 * A short two-tone alarm, made by the browser itself (no sound file needed).
 * Plays at most once every 3 seconds, so a burst of critical alerts doesn't become a siren.
 */
export function playAlarm() {
  if (!isSoundOn() || Date.now() - lastPlayed < 3_000) return;
  lastPlayed = Date.now();
  try {
    const audio = new AudioContext();
    [0, 0.25].forEach((offset, index) => {
      const tone = audio.createOscillator();
      const volume = audio.createGain();
      tone.frequency.value = index === 0 ? 880 : 660;
      const start = audio.currentTime + offset;
      volume.gain.setValueAtTime(0.0001, start);
      volume.gain.exponentialRampToValueAtTime(0.2, start + 0.02);
      volume.gain.exponentialRampToValueAtTime(0.0001, start + 0.2);
      tone.connect(volume).connect(audio.destination);
      tone.start(start);
      tone.stop(start + 0.22);
    });
    setTimeout(() => audio.close(), 1_000);
  } catch {
    // Some browsers block sound until the user has clicked on the page; the pop-up still shows.
  }
}
