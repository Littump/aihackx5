import { Card } from "@/shared/ui/Card";
import type { ReferralResponse } from "../api";
import { limitText } from "../format";

type RewardCardProps = {
  referral: ReferralResponse;
};

export function RewardCard({ referral }: RewardCardProps) {
  return (
    <Card className="flex flex-col gap-2">
      <h2 className="text-sm font-semibold text-text">Награда</h2>
      <p className="text-sm text-text">
        Вам — <span className="font-semibold">{referral.referrer_reward_points} баллов</span> после
        выполнения условий приглашения
      </p>
      <p className="text-sm text-text-secondary">
        Новому соседу — {referral.referee_reward_points_new} баллов, спящему —{" "}
        {referral.referee_reward_points_dormant} баллов
      </p>
      <p className="text-xs text-text-secondary">
        Лимит: {limitText(referral.paid_this_month, referral.paid_limit_month)}
      </p>
    </Card>
  );
}
