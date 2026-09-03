import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { API } from "@/test/handlers";
import { renderWithProviders } from "@/test/render";
import { server } from "@/test/setup";
import { ReferralScreen } from "../ReferralScreen";

describe("ReferralScreen", () => {
  it("показывает код, ссылку, QR и награду", async () => {
    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    expect(await screen.findByText("DOM-1F2B")).toBeInTheDocument();
    expect(screen.getByText("https://x5club.ru/i/DOM-1F2B")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "QR-код приглашения" })).toBeInTheDocument();

    const rewardCard = screen.getByText("Награда").closest("div");
    expect(rewardCard).not.toBeNull();
    expect(rewardCard!.textContent).toContain(
      "Вам — 150 баллов после выполнения условий приглашения",
    );
    expect(rewardCard!.textContent).toContain("Новому соседу — 200 баллов, спящему — 150 баллов");
    expect(rewardCard!.textContent).toContain("Лимит: 4 из 5 в этом месяце");
  });

  it("показывает правила приглашения списком", async () => {
    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    expect(await screen.findByText("Пригласите соседа по коду")).toBeInTheDocument();
    expect(screen.getByText("Награда после второй покупки приглашённого")).toBeInTheDocument();
  });

  it("клик «Скопировать» копирует ссылку в буфер обмена", async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });

    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    const copyButton = await screen.findByRole("button", { name: "Скопировать" });
    await user.click(copyButton);

    expect(writeText).toHaveBeenCalledWith("https://x5club.ru/i/DOM-1F2B");
    expect(await screen.findByRole("button", { name: "Скопировано" })).toBeInTheDocument();
  });

  it("показывает приглашённых с прогрессом покупок", async () => {
    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    expect(await screen.findByText("Сосед №1")).toBeInTheDocument();
    const row = screen.getByText("Сосед №2").closest('[data-testid="referral-invitee-row"]');
    expect(row).not.toBeNull();
    expect(row!.textContent).toContain("1 из 2 покупок");
  });

  it("статусы on_review и blocked показываются нейтрально «на проверке»", async () => {
    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    const onReviewRow = (await screen.findByText("Сосед №3")).closest(
      '[data-testid="referral-invitee-row"]',
    );
    const blockedRow = screen.getByText("Сосед №4").closest('[data-testid="referral-invitee-row"]');

    expect(onReviewRow!.textContent).toContain("на проверке");
    expect(blockedRow!.textContent).toContain("на проверке");
    expect(blockedRow!.textContent).not.toMatch(/заблокирован|отклонён|блок/i);

    const rows = screen.getAllByText("на проверке");
    expect(rows).toHaveLength(2);
  });

  it("показывает награду только у приглашённого со статусом «выполнен» (rewarded)", async () => {
    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    const rewardedRow = (await screen.findByText("Сосед №1")).closest(
      '[data-testid="referral-invitee-row"]',
    );
    expect(rewardedRow!.textContent).toContain("+200 баллов");

    const firstPurchaseRow = screen
      .getByText("Сосед №2")
      .closest('[data-testid="referral-invitee-row"]');
    expect(firstPurchaseRow!.textContent).not.toContain("баллов");
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
    expect(screen.getByText("Приглашённые · 0")).toBeInTheDocument();
    expect(screen.queryByTestId("referral-invitee-row")).not.toBeInTheDocument();
  });

  it("показывает состояние загрузки, пока данные не пришли", () => {
    renderWithProviders(<ReferralScreen />, ["/?user=1"]);
    expect(screen.getByText("Загружаем приглашения…")).toBeInTheDocument();
  });

  it("показывает ошибку, если приглашения не загрузились", async () => {
    server.use(
      http.get(`${API}/users/:user_id/referral`, () =>
        HttpResponse.json(
          { error: { code: "internal_error", message: "БД недоступна" } },
          { status: 500 },
        ),
      ),
    );

    renderWithProviders(<ReferralScreen />, ["/?user=1"]);

    expect(await screen.findByText(/Не получилось загрузить приглашения/)).toBeInTheDocument();
    expect(screen.getByText(/БД недоступна/)).toBeInTheDocument();
  });
});
