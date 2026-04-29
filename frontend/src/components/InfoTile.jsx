export function InfoTile({ label, value }) {
  return (
    <div className="rounded-xl border border-teal-100 bg-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">{label}</p>
      <p className="mt-1 text-base font-bold capitalize text-slate-950">{value || "Not sure"}</p>
    </div>
  );
}
