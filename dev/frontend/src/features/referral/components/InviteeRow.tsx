import { ProgressBar } from "@/shared/ui/ProgressBar";
import type { ReferralInvitee } from "../format";
import { purchasesProgressText, statusBadgeClass, statusLabel } from "../format";

type InviteeRowProps = {
  invitee: ReferralInvitee;
};

export function InviteeRow({ invitee }: InviteeRowProps) {
  return (
    <div
      data-testid="referral-invitee-row"
      className="flex flex-col gap-2 rounded-xl border border-border bg-surface px-3 py-2"
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-text">{invitee.label}</span>
        <span
          className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${statusBadgeClass(invitee.status)}`}
        >
          {statusLabel(invitee.status)}
        </span>
      </div>
      <ProgressBar value={invitee.purchases_done} max={invitee.purchases_required} />
      <div className="flex items-center justify-between text-xs text-text-secondary">
        <span>{purchasesProgressText(invitee.purchases_done, invitee.purchases_required)}</span>
        {invitee.status === "rewarded" && (
          <span className="font-medium text-brand-600">+{invitee.reward_points} баллов</span>
        )}
      </div>
    </div>
  );
}
