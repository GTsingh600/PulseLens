import { describe, expect, it } from "vitest";
import { isStrictlyIncreasing, now } from "../../src/shared/clock";

describe("one clock", () => {
  it("now() is performance.now() and never goes backwards", () => {
    const a = now();
    const b = performance.now();
    const c = now();
    expect(a).toBeLessThanOrEqual(b);
    expect(b).toBeLessThanOrEqual(c);
  });

  it("isStrictlyIncreasing rejects repeats and reversals", () => {
    expect(isStrictlyIncreasing([])).toBe(true);
    expect(isStrictlyIncreasing([1, 2, 3.5])).toBe(true);
    expect(isStrictlyIncreasing([1, 1, 2])).toBe(false);
    expect(isStrictlyIncreasing([1, 3, 2])).toBe(false);
    expect(isStrictlyIncreasing([1, Number.NaN])).toBe(false);
  });
});
