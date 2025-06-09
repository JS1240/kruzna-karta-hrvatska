import * as React from "react";
import * as SliderPrimitive from "@radix-ui/react-slider";
import { Input } from "./input";
import { cn } from "../../lib/utils";

interface SliderProps
  extends React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root> {
  showInput?: boolean;
  onInputChange?: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  inputClassName?: string;
}

const Slider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  SliderProps
>(
  (
    {
      className,
      showInput = false,
      onInputChange,
      min = 0,
      max = 100,
      step = 1,
      value,
      inputClassName,
      ...props
    },
    ref,
  ) => {
    const [inputValue, setInputValue] = React.useState<string>(() =>
      Array.isArray(value) ? String(value[0]) : "0",
    );

    // Update input value when slider value changes
    React.useEffect(() => {
      if (value !== undefined) {
        const valueToUse = Array.isArray(value) ? value[0] : value;
        setInputValue(String(valueToUse));
      }
    }, [value]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setInputValue(newValue);

      const numValue = Number(newValue);
      if (!isNaN(numValue) && onInputChange) {
        const boundedValue = Math.min(Math.max(numValue, min), max);
        onInputChange(boundedValue);
      }
    };

    const handleInputBlur = () => {
      const numValue = Number(inputValue);
      if (isNaN(numValue)) {
        // Reset to current slider value
        const currentValue = Array.isArray(value)
          ? value[0]
          : (value as number) || min;
        setInputValue(String(currentValue));
      } else {
        // Ensure value is within bounds
        const boundedValue = Math.min(Math.max(numValue, min), max);
        setInputValue(String(boundedValue));
        if (onInputChange) {
          onInputChange(boundedValue);
        }
      }
    };

    return (
      <div className={cn("w-full", showInput && "flex items-center gap-4")}>
        <SliderPrimitive.Root
          ref={ref}
          className={cn(
            "relative flex w-full touch-none select-none items-center",
            className,
          )}
          min={min}
          max={max}
          step={step}
          value={value}
          {...props}
        >
          <SliderPrimitive.Track className="relative h-2 w-full grow overflow-hidden rounded-full bg-secondary">
            <SliderPrimitive.Range className="absolute h-full bg-primary" />
          </SliderPrimitive.Track>
          {/* Render a thumb for each value (for range support) */}
          {Array.isArray(value) ? (
            value.map((_, i) => (
              <SliderPrimitive.Thumb
                key={i}
                className="block h-5 w-5 rounded-full border-2 border-primary bg-background ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
              />
            ))
          ) : (
            <SliderPrimitive.Thumb className="block h-5 w-5 rounded-full border-2 border-primary bg-background ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50" />
          )}
        </SliderPrimitive.Root>

        {showInput && (
          <Input
            type="number"
            value={inputValue}
            onChange={handleInputChange}
            onBlur={handleInputBlur}
            className={cn("w-20 text-center", inputClassName)}
            min={min}
            max={max}
            step={step}
          />
        )}
      </div>
    );
  },
);
Slider.displayName = SliderPrimitive.Root.displayName;

export { Slider };
