import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { RetryButton } from "@/shared/ui/RetryButton";

describe("RetryButton", () => {
  it("вызывает onClick по клику на «Повторить»", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<RetryButton onClick={onClick} />);

    await user.click(screen.getByRole("button", { name: "Повторить" }));

    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
