import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DomovoyMessageScreen } from "../DomovoyMessageScreen";

describe("DomovoyMessageScreen", () => {
  it("рендерит персонажа с нужным настроением, заголовок и текст", () => {
    render(
      <DomovoyMessageScreen mood="bored" heading="Не получилось загрузить" body="Текст ошибки" />,
    );

    expect(screen.getByRole("img", { name: /Скучающий/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Не получилось загрузить" })).toBeInTheDocument();
    expect(screen.getByText("Текст ошибки")).toBeInTheDocument();
  });

  it("по умолчанию персонаж крупный (160px)", () => {
    render(<DomovoyMessageScreen mood="sleepy" heading="Заголовок" body="Текст" />);
    const avatar = screen.getByRole("img");
    expect(avatar).toHaveAttribute("width", "160");
    expect(avatar).toHaveAttribute("height", "160");
  });

  it("принимает произвольный размер персонажа", () => {
    render(<DomovoyMessageScreen mood="sleepy" heading="Заголовок" body="Текст" avatarSize={80} />);
    const avatar = screen.getByRole("img");
    expect(avatar).toHaveAttribute("width", "80");
  });

  it("рендерит переданные действия", () => {
    render(
      <DomovoyMessageScreen mood="bored" heading="Заголовок" body="Текст">
        <button type="button">Повторить</button>
      </DomovoyMessageScreen>,
    );
    expect(screen.getByRole("button", { name: "Повторить" })).toBeInTheDocument();
  });
});
