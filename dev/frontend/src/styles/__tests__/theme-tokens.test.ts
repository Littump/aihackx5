import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const cssPath = resolve(process.cwd(), "src/styles/index.css");
const css = readFileSync(cssPath, "utf-8");

function extractBlock(pattern: RegExp): string {
  const match = css.match(pattern);
  if (!match) {
    throw new Error(`Block not found for pattern ${pattern}`);
  }
  return match[1];
}

function tokenNames(block: string): string[] {
  return [...block.matchAll(/--([a-zA-Z0-9-]+)\s*:/g)].map((m) => m[1]);
}

describe("styles/index.css theme tokens", () => {
  it("объявляет новый блок токенов как @theme static", () => {
    expect(css).toMatch(/@theme static\s*\{/);
  });

  it("legacy @theme и новый @theme static не переопределяют одни и те же переменные", () => {
    const legacyBlock = extractBlock(/@theme\s*\{([^}]*)\}/);
    const staticBlock = extractBlock(/@theme static\s*\{([^}]*)\}/);

    const legacyNames = new Set(tokenNames(legacyBlock));
    const staticNames = new Set(tokenNames(staticBlock));
    const collisions = [...legacyNames].filter((name) => staticNames.has(name));

    expect(collisions).toEqual([]);
  });
});
