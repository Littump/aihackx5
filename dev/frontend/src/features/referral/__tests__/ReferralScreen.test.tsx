import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";
import { API } from "@/test/handlers";
import { getReferral } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";
import { server } from "@/test/setup";
import { ReferralScreen } from "../ReferralScreen";

function mockClipboard() {
  const writeText = vi.fn().mockResolvedValue(undefined);
  Object.defineProperty(navigator, "clipboard", {
    value: { writeText },
    configurable: true,
  });
  return writeText;
}

afterEach(() => {
  Reflect.deleteProperty(navigator, "share");
});

describe("ReferralScreen", () => {
  it("показывает код, QR и награды", async () => {
    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    expect(await screen.findByText("DOM-1F2B")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "QR-код приглашения" })).toBeInTheDocument();

    expect(screen.getByText("Вам").nextSibling?.textContent).toBe("150 баллов");
    expect(screen.getByText("Новому соседу").nextSibling?.textContent).toBe("200 баллов");
    expect(screen.getByText("Вернувшемуся").nextSibling?.textContent).toBe("150 баллов");
  });

  it("показывает правила приглашения нумерованным списком", async () => {
    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    expect(await screen.findByText("Пригласите соседа по коду")).toBeInTheDocument();
    expect(screen.getByText("Награда после второй покупки приглашённого")).toBeInTheDocument();
    expect(screen.getByText("1.")).toBeInTheDocument();
    expect(screen.getByText("2.")).toBeInTheDocument();
  });

  it("показывает лимит месяца прогресс-баром", async () => {
    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    expect(await screen.findByText("выплачено 4 из 5")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "4");
  });

  it("клик «Скопировать» копирует ссылку в буфер обмена", async () => {
    const user = userEvent.setup();
    const writeText = mockClipboard();

    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    const copyButton = await screen.findByRole("button", { name: /Скопировать/ });
    await user.click(copyButton);

    expect(writeText).toHaveBeenCalledWith("https://x5club.ru/i/DOM-1F2B");
    expect(await screen.findByRole("button", { name: /Скопировано/ })).toBeInTheDocument();
  });

  it("клик «Поделиться» вызывает navigator.share, если он доступен", async () => {
    const user = userEvent.setup();
    const share = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "share", { value: share, configurable: true });
    const writeText = mockClipboard();

    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    const shareButton = await screen.findByRole("button", { name: /Поделиться/ });
    await user.click(shareButton);

    expect(share).toHaveBeenCalledWith(
      expect.objectContaining({ url: "https://x5club.ru/i/DOM-1F2B" }),
    );
    expect(writeText).not.toHaveBeenCalled();
  });

  it("клик «Поделиться» падает обратно на copyReferralLink, если navigator.share недоступен", async () => {
    const user = userEvent.setup();
    Reflect.deleteProperty(navigator, "share");
    const writeText = mockClipboard();

    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    const shareButton = await screen.findByRole("button", { name: /Поделиться/ });
    await user.click(shareButton);

    expect(writeText).toHaveBeenCalledWith("https://x5club.ru/i/DOM-1F2B");
  });

  it("клик «Поделиться» не падает и не показывает ошибку, если пользователь отменил диалог", async () => {
    const user = userEvent.setup();
    const share = vi.fn().mockRejectedValue(new DOMException("AbortError"));
    Object.defineProperty(navigator, "share", { value: share, configurable: true });
    const writeText = mockClipboard();

    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    const shareButton = await screen.findByRole("button", { name: /Поделиться/ });
    await user.click(shareButton);

    expect(share).toHaveBeenCalled();
    expect(writeText).not.toHaveBeenCalled();
    expect(screen.queryByText(/ошиб/i)).not.toBeInTheDocument();
    expect(shareButton).toBeInTheDocument();
  });

  it("показывает приглашённых с прогрессом покупок", async () => {
    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    expect(await screen.findByText("Сосед №1")).toBeInTheDocument();
    const row = screen.getByText("Сосед №2").closest('[data-testid="referral-invitee-row"]');
    expect(row).not.toBeNull();
    expect(row!.textContent).toContain("1 из 2 покупок");
  });

  it("статусы on_review и blocked показываются нейтральным текстом без пугающих формулировок", async () => {
    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    const onReviewRow = (await screen.findByText("Сосед №3")).closest(
      '[data-testid="referral-invitee-row"]',
    );
    const blockedRow = screen.getByText("Сосед №4").closest('[data-testid="referral-invitee-row"]');

    expect(onReviewRow!.textContent).toContain("на проверке");
    expect(blockedRow!.textContent).toContain("отклонён");
    expect(blockedRow!.textContent).not.toMatch(/заблокирован|мошенн|запрещ/i);
  });

  it("показывает заглушку, когда приглашённых пока нет", async () => {
    server.use(
      http.get(`${API}/users/:user_id/referral`, () =>
        HttpResponse.json({
          code: "DOM-1F2B",
          link: "https://x5club.ru/i/DOM-1F2B",
          rules: ["Пригласите соседа по коду"],
          referrer_reward_points: 150,
          referee_reward_points_new: 200,
          referee_reward_points_dormant: 150,
          invitees: [],
          paid_this_month: 0,
          paid_limit_month: 5,
        }),
      ),
    );

    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    expect(await screen.findByText("Пока никого не пригласили")).toBeInTheDocument();
    expect(screen.getByText("Приглашённые")).toBeInTheDocument();
    expect(screen.queryByTestId("referral-invitee-row")).not.toBeInTheDocument();
  });

  it("показывает скелетон, пока данные не пришли", () => {
    const { container } = renderWithProviders(<ReferralScreen />, ["/?user=1"]);
    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("показывает ошибку с персонажем и повторяет запрос по клику «Повторить»", async () => {
    let calls = 0;
    server.use(
      http.get(`${API}/users/:user_id/referral`, () => {
        calls += 1;
        if (calls === 1) {
          return HttpResponse.json(
            { error: { code: "internal_error", message: "БД недоступна" } },
            { status: 500 },
          );
        }
        return HttpResponse.json(getReferral(1));
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    expect(await screen.findByText("Не получилось загрузить")).toBeInTheDocument();
    expect(screen.queryByText(/БД недоступна/)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Повторить" }));

    expect(await screen.findByText("DOM-1F2B")).toBeInTheDocument();
    expect(calls).toBe(2);
  });
});
