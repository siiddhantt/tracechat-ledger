import * as React from "react";

import { cn } from "@/lib/utils";

export const Select = React.forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        "h-10 w-full border-2 border-ink bg-white px-3 text-sm font-black text-ink shadow-sketchSoft outline-none focus:bg-marker/30",
        className,
      )}
      {...props}
    />
  ),
);
Select.displayName = "Select";
