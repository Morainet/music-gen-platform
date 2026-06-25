import * as React from "react";
import { cn } from "@/lib/utils";

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "w-full h-10 rounded-lg border border-border bg-base px-3 text-sm text-text-primary placeholder:text-text-muted transition-colors focus-visible:outline-none focus-visible:border-violet/70 focus-visible:ring-1 focus-visible:ring-violet/40",
      className
    )}
    {...props}
  />
));
Input.displayName = "Input";
