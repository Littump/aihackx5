import { useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
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

  return (
    <Card className="flex flex-col items-center gap-3 text-center">
      <QRCodeSVG value={link} size={160} role="img" aria-label="QR-код приглашения" />
      <div>
        <p className="text-xs uppercase text-text-secondary">Ваш код</p>
        <p className="text-2xl font-semibold tracking-wide text-text">{code}</p>
      </div>
      <p className="break-all text-xs text-text-secondary">{link}</p>
      <Button onClick={handleCopy} className="w-full">
        {copied ? "Скопировано" : "Скопировать"}
      </Button>
    </Card>
  );
}
