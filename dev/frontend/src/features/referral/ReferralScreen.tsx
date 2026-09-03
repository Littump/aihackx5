import { useUserContext } from "@/features/users/hooks";
import { NAV_ICON_PATHS } from "@/shared/ui/navIcons";
import { InviteeList } from "./components/InviteeList";
import { PaidLimitCard } from "./components/PaidLimitCard";
import { ReferralCodeCard } from "./components/ReferralCodeCard";
import { RewardCard } from "./components/RewardCard";
import { RulesList } from "./components/RulesList";
import { StatusLegend } from "./components/StatusLegend";
import { useReferral } from "./hooks";

export function ReferralScreen() {
  const { userId } = useUserContext();
  const referralQuery = useReferral(userId);

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center gap-3 border-b border-line bg-surface px-4 py-4">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          className="h-6 w-6"
          aria-hidden="true"
        >
          {NAV_ICON_PATHS.referral}
        </svg>
        <h1 className="text-lead font-bold">Позови соседа</h1>
      </div>

      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 py-4">
        {(userId === null || referralQuery.isPending) && (
          <p className="text-ink-500">Загружаем приглашения…</p>
        )}

        {referralQuery.isError && (
          <p className="text-accent-700">
            Не получилось загрузить приглашения: {referralQuery.error.message}
          </p>
        )}

        {referralQuery.data && (
          <>
            <ReferralCodeCard code={referralQuery.data.code} link={referralQuery.data.link} />
            <RewardCard
              referrerRewardPoints={referralQuery.data.referrer_reward_points}
              refereeRewardPointsNew={referralQuery.data.referee_reward_points_new}
              refereeRewardPointsDormant={referralQuery.data.referee_reward_points_dormant}
            />
            <RulesList rules={referralQuery.data.rules} />
            <PaidLimitCard
              paidThisMonth={referralQuery.data.paid_this_month}
              paidLimitMonth={referralQuery.data.paid_limit_month}
            />
            <InviteeList invitees={referralQuery.data.invitees} />
            <StatusLegend />
          </>
        )}
      </div>
    </div>
  );
}
