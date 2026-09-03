import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Skeleton } from "@/shared/ui/Skeleton";

describe("Skeleton", () => {
  it("рендерит заглушку с анимацией и переданным размером", () => {
    const { container } = render(<Skeleton className="h-4 w-20" />);
    const skeleton = container.firstChild as HTMLElement;
    expect(skeleton).toHaveClass("animate-pulse", "bg-canvas", "h-4", "w-20");
    expect(skeleton).toHaveAttribute("aria-hidden", "true");
  });
});
