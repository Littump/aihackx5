import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DomovoyAvatar } from "../DomovoyAvatar";
import { MOOD_LABEL, type DomovoyMood } from "../moodLabels";

const MOODS: DomovoyMood[] = ["cheerful", "cozy", "healthy", "bored", "sleepy"];

describe("DomovoyAvatar", () => {
  it.each(MOODS)("рендерит символ #dom-%s для соответствующего настроения", (mood) => {
    const { container } = render(<DomovoyAvatar mood={mood} size={48} />);
    expect(container.querySelector("use")).toHaveAttribute("href", `#dom-${mood}`);
  });

  it.each(MOODS)("aria-label содержит русское название для %s", (mood) => {
    render(<DomovoyAvatar mood={mood} size={48} />);
    expect(screen.getByRole("img")).toHaveAttribute(
      "aria-label",
      `Домовой, настроение: ${MOOD_LABEL[mood]}`,
    );
  });

  it("без уровня рендерит только символ настроения", () => {
    const { container } = render(<DomovoyAvatar mood="cozy" size={48} />);
    expect(container.querySelectorAll("use")).toHaveLength(1);
    expect(container.querySelector("use")).toHaveAttribute("href", "#dom-cozy");
  });

  it("для низкого уровня обжитости слоёв нет", () => {
    const { container } = render(<DomovoyAvatar mood="cozy" size={48} level={3} />);
    expect(container.querySelectorAll("use")).toHaveLength(1);
  });

  it("для среднего уровня добавляются плед и чашка", () => {
    const { container } = render(<DomovoyAvatar mood="cozy" size={48} level={5} />);
    const hrefs = Array.from(container.querySelectorAll("use")).map((el) =>
      el.getAttribute("href"),
    );
    expect(hrefs).toEqual(["#dom-cozy", "#dom-blanket", "#dom-cup"]);
  });

  it("для высокого уровня добавляется ещё полка", () => {
    const { container } = render(<DomovoyAvatar mood="cozy" size={48} level={8} />);
    const hrefs = Array.from(container.querySelectorAll("use")).map((el) =>
      el.getAttribute("href"),
    );
    expect(hrefs).toEqual(["#dom-cozy", "#dom-blanket", "#dom-cup", "#dom-shelf"]);
  });

  it("проставляет размер через width/height", () => {
    render(<DomovoyAvatar mood="cheerful" size={32} />);
    const svg = screen.getByRole("img");
    expect(svg).toHaveAttribute("width", "32");
    expect(svg).toHaveAttribute("height", "32");
  });
});
