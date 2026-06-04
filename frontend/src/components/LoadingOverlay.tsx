import { useEffect, useState } from "react";

interface Props {
  message?: string;
}

export default function LoadingOverlay({ message = "Working..." }: Props) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm animate-fade-in">
      <div className="glass rounded-2xl px-10 py-9 text-center animate-pop">
        <div className="relative mx-auto w-14 h-14">
          <div className="absolute inset-0 rounded-full border-2 border-black/10" />
          <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-[var(--brand-2)] border-r-[var(--brand-3)] animate-spin" />
          <div className="absolute inset-2 rounded-full brand-gradient opacity-20 blur-md" />
        </div>
        <p className="mt-5 font-semibold text-[var(--ink)]">{message}</p>
        <p className="mt-1 text-sm mono text-[var(--ink-soft)]">{elapsed}s elapsed</p>
      </div>
    </div>
  );
}
