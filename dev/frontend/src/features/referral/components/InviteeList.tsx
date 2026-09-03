import { Card } from "@/shared/ui/Card";
import type { ReferralResponse } from "../api";
import { InviteeRow } from "./InviteeRow";

type InviteeListProps = {
  invitees: ReferralResponse["invitees"];
};

export function InviteeList({ invitees }: InviteeListProps) {
  return (
    <Card className="flex flex-col gap-2">
      <h2 className="text-sm font-semibold text-text">Приглашённые · {invitees.length}</h2>
      {invitees.length === 0 ? (
        <p className="text-sm text-text-secondary">Пока никого не пригласили</p>
      ) : (
        <div className="flex flex-col gap-2">
          {invitees.map((invitee) => (
            <InviteeRow key={invitee.label} invitee={invitee} />
          ))}
        </div>
      )}
    </Card>
  );
}
