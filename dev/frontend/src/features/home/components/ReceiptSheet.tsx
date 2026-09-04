import { Button } from "@/shared/ui/Button";
import { useSimulateDraft } from "../hooks";
import type { SimulateItemInput } from "../api";
import { ReceiptDraftForm } from "./ReceiptDraftForm";

type ReceiptSheetProps = {
  userId: number | null;
  open: boolean;
  submitting: boolean;
  onClose: () => void;
  onConfirm: (items: SimulateItemInput[]) => void;
};

export function ReceiptSheet({ userId, open, submitting, onClose, onConfirm }: ReceiptSheetProps) {
  const draftQuery = useSimulateDraft(userId, open);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-30 flex items-end justify-center bg-ink-900/40 p-2">
      <section
        role="dialog"
        aria-modal="true"
        aria-label="Чек покупки"
        className="animate-popin flex max-h-full w-full max-w-[414px] flex-col gap-3 overflow-y-auto rounded-card bg-surface p-4 shadow-lift"
      >
        <header className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-title font-bold leading-tight">Чек покупки</h2>
            <p className="text-caption text-ink-500">
              {draftQuery.data ? draftQuery.data.store_name : "Собираем корзину…"}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Закрыть чек"
            className="rounded-tile px-3 py-2 text-body font-semibold text-ink-500 hover:bg-canvas"
          >
            ✕
          </button>
        </header>
        {draftQuery.isPending && <p className="text-body text-ink-500">Загружаем корзину…</p>}
        {draftQuery.isError && (
          <div className="flex flex-col gap-3">
            <p role="alert" className="text-body text-accent-700">
              Не получилось собрать чек. Попробуйте ещё раз.
            </p>
            <Button variant="secondary" onClick={() => draftQuery.refetch()}>
              Повторить
            </Button>
          </div>
        )}
        {draftQuery.data && (
          <ReceiptDraftForm
            key={draftQuery.dataUpdatedAt}
            draft={draftQuery.data}
            submitting={submitting}
            onCancel={onClose}
            onConfirm={onConfirm}
          />
        )}
      </section>
    </div>
  );
}
