import type { ReferralResponse } from "../api";
import { InviteeRow } from "./InviteeRow";

type InviteeListProps = {
  invitees: ReferralResponse["invitees"];
};

export function InviteeList({ invitees }: InviteeListProps) {
  return (
    <section className="flex shrink-0 flex-col divide-y divide-line rounded-card bg-surface shadow-card">
      <h3 className="p-4 pb-3 text-lead font-bold">
        Приглашённые{invitees.length > 0 ? ` · ${invitees.length}` : ""}
      </h3>
      {invitees.length === 0 ? (
        <p className="px-4 pb-4 text-body text-ink-500">Пока никого не пригласили</p>
      ) : (
        invitees.map((invitee) => <InviteeRow key={invitee.label} invitee={invitee} />)
      )}
    </section>
  );
}
