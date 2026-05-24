import * as React from "react";

import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "min-h-24 w-full resize-none border-2 border-ink bg-white px-3 py-3 text-sm font-semibold text-ink shadow-sketchSoft outline-none placeholder:text-neutral-500 focus:bg-marker/30",
      className,
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";
