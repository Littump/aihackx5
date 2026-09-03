import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DomovoyAvatar } from "../DomovoyAvatar";
import { DomovoyDefs } from "../DomovoyDefs";

const EXPECTED_IDS = [
  "dom-fur",
  "dom-cap",
  "dom-blanket",
  "dom-cup",
  "dom-shelf",
  "dom-cheerful",
  "dom-cozy",
  "dom-healthy",
  "dom-bored",
  "dom-sleepy",
];

describe("DomovoyDefs", () => {
  it("рендерит один раз все слои и символы настроений с ожидаемыми id", () => {
    const { container } = render(<DomovoyDefs />);
    for (const id of EXPECTED_IDS) {
      expect(container.querySelector(`#${id}`)).not.toBeNull();
    }
  });

  it("id символов и слоёв не дублируются при нескольких инстансах DomovoyAvatar", () => {
    const { container } = render(
      <>
        <DomovoyDefs />
        <DomovoyAvatar mood="cozy" size={48} level={8} />
        <DomovoyAvatar mood="cozy" size={48} level={8} />
        <DomovoyAvatar mood="cheerful" size={32} />
      </>,
    );
    for (const id of EXPECTED_IDS) {
      expect(container.querySelectorAll(`[id="${id}"]`)).toHaveLength(1);
    }
  });
});
