import { useState } from "react";

type ExplanationDisclosureProps = {
  explanation: string;
};

export function ExplanationDisclosure({ explanation }: ExplanationDisclosureProps) {
  const [open, setOpen] = useState(false);

  return (
    <div>
      <button
        type="button"
        aria-expanded={open}
        className="text-sm font-medium text-brand-600"
        onClick={() => setOpen((value) => !value)}
      >
        Почему это мне?
      </button>
      {open && <p className="mt-2 text-sm text-text-secondary">{explanation}</p>}
    </div>
  );
}
