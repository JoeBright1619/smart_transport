import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  message?: string;
}

export function LoadingSpinner({ message }: LoadingSpinnerProps) {
  return (
    <div className="flex min-h-[360px] items-center justify-center">
      <div className="flex items-center gap-2 text-slate-600">
        <Loader2 className="size-5 animate-spin" />
        {message && <span>{message}</span>}
      </div>
    </div>
  );
}
