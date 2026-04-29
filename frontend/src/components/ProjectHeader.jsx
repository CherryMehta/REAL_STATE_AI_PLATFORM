export function ProjectHeader() {
  return (
    <section className="overflow-hidden rounded-2xl border border-white/80 bg-white/85 shadow-xl shadow-emerald-900/5 backdrop-blur">
      <div className="grid gap-6 p-5 lg:grid-cols-[1.2fr_0.8fr] lg:p-8">
        <div className="space-y-4">
          <div>
            <h1 className="max-w-3xl text-3xl font-bold tracking-tight text-slate-950 sm:text-3xl">
             REAL ESTATE AI PLATFORM
            </h1>
            <p className="mt-3 max-w-3xl text-base leading-7 text-slate-700 sm:text-lg">
              A friendly workspace that helps a real estate team understand messages, pick the next step, and revise listing details.
            </p>
          </div>
        </div>
        <div className="grid gap-3 rounded-xl border border-orange-100 bg-orange-50/80 p-4 text-sm text-slate-700">
          <div className="rounded-lg bg-white/80 p-3">
            <p className="font-semibold text-slate-900">Sort a message</p>
            <p className="mt-1">See how urgent it is, what the person needs, and what to reply.</p>
          </div>
          <div className="rounded-lg bg-white/80 p-3">
            <p className="font-semibold text-slate-900">Practice a listing</p>
            <p className="mt-1">Turn property notes into quick questions for easy revision.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
