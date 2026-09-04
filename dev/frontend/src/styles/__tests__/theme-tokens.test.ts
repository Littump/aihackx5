import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const cssPath = resolve(process.cwd(), "src/styles/index.css");
const css = readFileSync(cssPath, "utf-8");

describe("styles/index.css theme tokens", () => {
  it("объявляет единственный блок токенов как @theme static", () => {
    expect(css).toMatch(/@theme static\s*\{/);
    expect(css).not.toMatch(/@theme\s*\{/);
  });

  it("не содержит легаси-токенов исходной палитры", () => {
    for (const name of ["--color-brand-900", "--color-bg", "--color-text-secondary"]) {
      expect(css).not.toContain(`${name}:`);
    }
  });
});
