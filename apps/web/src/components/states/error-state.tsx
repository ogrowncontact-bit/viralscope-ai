import { AlertTriangle } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ title = "Algo deu errado", message, onRetry }: ErrorStateProps) {
  return (
    <div className="border-destructive/30 bg-destructive/5 flex flex-col items-center gap-2 rounded-lg border py-10 text-center">
      <AlertTriangle className="text-destructive size-5" />
      <p className="text-sm font-medium">{title}</p>
      <p className="text-muted-foreground max-w-xs text-sm">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="text-primary text-sm font-medium underline-offset-4 hover:underline"
        >
          Tentar de novo
        </button>
      )}
    </div>
  );
}
