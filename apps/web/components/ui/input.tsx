import * as React from "react";

import { cn } from "@/lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "h-10 w-full border-2 border-ink bg-white px-3 text-sm font-semibold text-ink shadow-sketchSoft outline-none placeholder:text-neutral-500 focus:bg-marker/30",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";
