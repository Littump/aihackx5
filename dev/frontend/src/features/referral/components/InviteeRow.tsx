import type { ReferralInvitee } from "../format";
import { formatInviteeBadge, statusIconShape, statusToneClasses } from "../format";
import { StatusIcon } from "./StatusIcon";

type InviteeRowProps = {
  invitee: ReferralInvitee;
};

export function InviteeRow({ invitee }: InviteeRowProps) {
  const tone = statusToneClasses(invitee.status);

  return (
    <div data-testid="referral-invitee-row" className="flex items-center gap-3 p-4">
      <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-tile ${tone}`}>
        <StatusIcon shapes={statusIconShape(invitee.status)} />
      </span>
      <span className="flex-1 text-body font-semibold">{invitee.label}</span>
      <span className={`rounded-tile px-3 py-1 text-caption font-semibold ${tone}`}>
        {formatInviteeBadge(invitee)}
      </span>
    </div>
  );
}
