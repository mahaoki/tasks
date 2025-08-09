import * as React from "react";
import { cn } from "@/lib/utils";

const Form = React.forwardRef<HTMLFormElement, React.ComponentProps<"form">>(
  ({ className, ...props }, ref) => (
    <form ref={ref} className={cn("grid gap-4", className)} {...props} />
  )
);
Form.displayName = "Form";

export { Form };
