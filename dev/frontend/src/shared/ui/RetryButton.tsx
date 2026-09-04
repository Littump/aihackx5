import { Button } from "./Button";

type RetryButtonProps = {
  onClick: () => void;
};

export function RetryButton({ onClick }: RetryButtonProps) {
  return (
    <Button onClick={onClick} className="flex w-full items-center justify-center gap-2">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        className="h-6 w-6"
        aria-hidden="true"
      >
        <path d="M20 12a8 8 0 1 1-2.3-5.6M20 4v5h-5" />
      </svg>
      Повторить
    </Button>
  );
}
