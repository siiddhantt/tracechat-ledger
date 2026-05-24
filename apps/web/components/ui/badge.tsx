import * as React from "react";

import { cn } from "@/lib/utils";

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  tone?: "default" | "green" | "red" | "blue";
};

export function Badge({ className, tone = "default", ...props }: BadgeProps) {
  const tones = {
    default: "bg-marker",
    green: "bg-mint",
    red: "bg-coral",
    blue: "bg-sky",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center border-2 border-ink px-2 py-0.5 text-xs font-black uppercase tracking-normal text-ink",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}
