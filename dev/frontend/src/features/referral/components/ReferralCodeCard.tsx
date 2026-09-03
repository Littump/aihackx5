import { useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { Button } from "@/shared/ui/Button";
import { copyReferralLink } from "../clipboard";

type ReferralCodeCardProps = {
  code: string;
  link: string;
};

const COPIED_LABEL_MS = 2000;

export function ReferralCodeCard({ code, link }: ReferralCodeCardProps) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    copyReferralLink(link);
    setCopied(true);
    setTimeout(() => setCopied(false), COPIED_LABEL_MS);
  }

  async function handleShare() {
    if (typeof navigator !== "undefined" && typeof navigator.share === "function") {
      try {
        await navigator.share({ title: "Домовой", text: `Мой код: ${code}`, url: link });
      } catch {
        return;
      }
      return;
    }
    copyReferralLink(link);
  }

  return (
    <section className="flex shrink-0 flex-col gap-4 rounded-card bg-surface p-4 shadow-card">
      <div className="flex items-center gap-4">
        <QRCodeSVG
          value={link}
          size={96}
          role="img"
          aria-label="QR-код приглашения"
          className="h-24 w-24 shrink-0 rounded-tile"
        />
        <div className="flex min-w-0 flex-col gap-1">
          <span className="text-caption text-ink-500">Ваш код</span>
          <span className="text-title font-bold tracking-wide">{code}</span>
          <span className="text-caption text-ink-500">Покажите QR или продиктуйте код</span>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Button onClick={handleCopy} className="flex items-center justify-center gap-2">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            className="h-6 w-6"
            aria-hidden="true"
          >
            <rect x="9" y="9" width="11" height="11" rx="2" />
            <path d="M15 5H6a1 1 0 0 0-1 1v9" />
          </svg>
          {copied ? "Скопировано" : "Скопировать"}
        </Button>
        <Button
          variant="secondary"
          onClick={handleShare}
          className="flex items-center justify-center gap-2"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            className="h-6 w-6"
            aria-hidden="true"
          >
            <path d="M12 16V4M8 8l4-4 4 4M5 14v5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-5" />
          </svg>
          Поделиться
        </Button>
      </div>
    </section>
  );
}
