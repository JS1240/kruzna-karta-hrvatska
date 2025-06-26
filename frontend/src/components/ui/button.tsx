import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-brand-primary text-brand-white hover:bg-brand-primary-dark active:bg-brand-secondary active:text-brand-white",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90 active:bg-brand-secondary active:text-brand-white",
        outline:
          "border border-input bg-background hover:bg-brand-accent-cream hover:text-brand-black active:bg-brand-secondary active:text-brand-white",
        secondary:
          "bg-brand-secondary text-brand-black hover:bg-brand-secondary-dark hover:text-brand-white active:bg-brand-primary active:text-brand-white",
        ghost:
          "hover:bg-brand-accent-cream hover:text-brand-black active:bg-brand-secondary active:text-brand-white",
        link: "text-brand-primary underline-offset-4 hover:underline active:text-brand-primary-dark",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
