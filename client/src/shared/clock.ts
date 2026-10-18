/**
 * The one client clock (CLAUDE.md rule 1).
 * Every echo timestamp is performance.now() in ms, or a requestVideoFrameCallback time,
 * which shares the same time origin. Import now() from here; ESLint blocks Date.now() in capture code.
 */
export function now(): number {
  return performance.now();
}

/** True if each value is greater than the one before. Frame `t` values must satisfy this. */
export function isStrictlyIncreasing(ts: readonly number[]): boolean {
  for (let i = 1; i < ts.length; i++) {
    if (!(ts[i]! > ts[i - 1]!)) return false;
  }
  return true;
}
