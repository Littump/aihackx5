import { useUserContext } from "@/features/users/hooks";
import { InviteeList } from "./components/InviteeList";
import { ReferralCodeCard } from "./components/ReferralCodeCard";
import { RewardCard } from "./components/RewardCard";
import { RulesList } from "./components/RulesList";
import { useReferral } from "./hooks";

export function ReferralScreen() {
  const { userId } = useUserContext();
  const referralQuery = useReferral(userId);

  if (userId === null || referralQuery.isPending) {
    return (
      <section className="flex flex-1 flex-col gap-4 p-5">
        <p className="text-text-secondary">Загружаем приглашения…</p>
      </section>
    );
  }

  if (referralQuery.isError) {
    return (
      <section className="flex flex-1 flex-col gap-4 p-5">
        <p className="text-legacy-accent-600">
          Не получилось загрузить приглашения: {referralQuery.error.message}
        </p>
      </section>
    );
  }

  const referral = referralQuery.data;

  return (
    <section className="flex flex-1 flex-col gap-4 p-5">
      <h1 className="text-2xl font-semibold text-text">Позови соседа</h1>
      <ReferralCodeCard code={referral.code} link={referral.link} />
      <RewardCard referral={referral} />
      <RulesList rules={referral.rules} />
      <InviteeList invitees={referral.invitees} />
    </section>
  );
}
