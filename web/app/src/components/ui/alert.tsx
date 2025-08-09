import * as React from "react";
import { cn } from "@/lib/utils";

function Alert({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      role="alert"
      className={cn(
        "rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive",
        className
      )}
      {...props}
    />
  );
}

export { Alert };
