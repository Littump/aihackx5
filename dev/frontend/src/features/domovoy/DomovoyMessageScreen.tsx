import type { ReactNode } from "react";
import { DomovoyAvatar, type DomovoyAvatarSize } from "./DomovoyAvatar";
import type { DomovoyMood } from "./moodLabels";

type DomovoyMessageScreenProps = {
  mood: DomovoyMood;
  heading: string;
  body: string;
  avatarSize?: DomovoyAvatarSize;
  className?: string;
  children?: ReactNode;
};

const DEFAULT_AVATAR_SIZE = 160;

export function DomovoyMessageScreen({
  mood,
  heading,
  body,
  avatarSize = DEFAULT_AVATAR_SIZE,
  className = "",
  children,
}: DomovoyMessageScreenProps) {
  return (
    <div className={`flex flex-col items-center justify-center gap-4 text-center ${className}`}>
      <DomovoyAvatar mood={mood} size={avatarSize} />
      <h3 className="text-title font-bold leading-tight">{heading}</h3>
      <p className="text-body text-pretty text-ink-700">{body}</p>
      {children}
    </div>
  );
}
