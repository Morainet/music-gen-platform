import * as React from "react";
import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "w-full rounded-lg border border-border bg-base px-3 py-2.5 text-sm text-text-primary placeholder:text-text-muted resize-none transition-colors focus-visible:outline-none focus-visible:border-violet/70 focus-visible:ring-1 focus-visible:ring-violet/40",
      className
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";
