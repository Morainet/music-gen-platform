import * as React from "react";
import { cn } from "@/lib/utils";

export const Select = React.forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement>
>(({ className, children, ...props }, ref) => (
  <select
    ref={ref}
    className={cn(
      "w-full h-10 rounded-lg border border-border bg-base px-3 text-sm text-text-primary transition-colors focus-visible:outline-none focus-visible:border-violet/70 focus-visible:ring-1 focus-visible:ring-violet/40",
      className
    )}
    {...props}
  >
    {children}
  </select>
));
Select.displayName = "Select";
