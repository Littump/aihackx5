import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ReferralCodeCard } from "../components/ReferralCodeCard";

describe("ReferralCodeCard — QR", () => {
  it("рендерит настоящий QR-код, чьё содержимое зависит от ссылки, а не статичный паттерн", () => {
    const { container: containerA } = render(
      <ReferralCodeCard code="DOM-1AAA" link="https://x5club.ru/i/DOM-1AAA" />,
    );
    const { container: containerB } = render(
      <ReferralCodeCard code="DOM-2BBB" link="https://x5club.ru/i/DOM-2BBB" />,
    );

    const svgA = screen.getAllByRole("img", { name: "QR-код приглашения" })[0];
    const svgB = containerB.querySelector('svg[aria-label="QR-код приглашения"]');

    expect(svgA).toBeInTheDocument();
    expect(svgB).not.toBeNull();
    expect(svgA.innerHTML).not.toBe(svgB!.innerHTML);
    expect(containerA.querySelectorAll("svg path, svg rect").length).toBeGreaterThan(4);
  });
});
