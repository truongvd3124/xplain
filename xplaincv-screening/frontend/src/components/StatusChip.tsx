const styles: Record<string, string> = {
  ACCEPTED: 'bg-green-100 text-green-800',
  REJECTED: 'bg-red-100 text-red-800',
  pending: 'bg-amber-100 text-amber-800',
  processing: 'bg-blue-100 text-blue-800 animate-pulse',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
}

export default function StatusChip({ value }: { value: string }) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${
        styles[value] ?? 'bg-slate-100 text-slate-700'
      }`}
    >
      {value}
    </span>
  )
}
