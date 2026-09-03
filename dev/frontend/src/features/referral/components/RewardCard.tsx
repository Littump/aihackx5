type RewardCardProps = {
  referrerRewardPoints: number;
  refereeRewardPointsNew: number;
  refereeRewardPointsDormant: number;
};

export function RewardCard({
  referrerRewardPoints,
  refereeRewardPointsNew,
  refereeRewardPointsDormant,
}: RewardCardProps) {
  return (
    <section className="flex shrink-0 flex-col gap-3 rounded-card bg-brand-50 p-4">
      <h3 className="text-lead font-bold">Награды</h3>
      <dl className="m-0 flex flex-col gap-2">
        <div className="flex justify-between text-body">
          <dt className="text-ink-700">Вам</dt>
          <dd className="m-0 font-semibold">{referrerRewardPoints} баллов</dd>
        </div>
        <div className="flex justify-between text-body">
          <dt className="text-ink-700">Новому соседу</dt>
          <dd className="m-0 font-semibold">{refereeRewardPointsNew} баллов</dd>
        </div>
        <div className="flex justify-between text-body">
          <dt className="text-ink-700">Вернувшемуся</dt>
          <dd className="m-0 font-semibold">{refereeRewardPointsDormant} баллов</dd>
        </div>
      </dl>
    </section>
  );
}
