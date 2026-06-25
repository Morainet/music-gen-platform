import * as React from "react";
import { cn } from "@/lib/utils";

interface SliderProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
  showValue?: boolean;
}

/** 基于原生 range 的滑块，配合主题色 accent */
export const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ className, value, ...props }, ref) => (
    <input
      ref={ref}
      type="range"
      value={value}
      className={cn(
        "w-full h-1.5 appearance-none rounded-full bg-elevated accent-violet cursor-pointer",
        className
      )}
      {...props}
    />
  )
);
Slider.displayName = "Slider";
