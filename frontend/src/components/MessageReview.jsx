import { InfoTile } from "./InfoTile.jsx";

export function MessageReview({
  message,
  onMessageChange,
  onReview,
  onLoadSample,
  triage,
  entitySummary,
  error,
  loading,
}) {
  return (
    <section className="grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
      <div className="rounded-2xl border border-white/80 bg-white/90 p-5 shadow-xl shadow-slate-900/5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-bold">Understand a message</h2>
            <p className="mt-1 text-sm text-slate-600">Paste any client message and get the next step in a clear format.</p>
          </div>
          <span className="rounded-full border border-orange-200 bg-orange-50 px-3 py-1 text-xs font-semibold text-orange-800">
            Reply ready
          </span>
        </div>
        <label className="mb-2 block text-sm font-semibold text-slate-700">Client message</label>
        <textarea
          className="min-h-48 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-6 outline-none transition focus:border-teal-500 focus:ring-4 focus:ring-teal-100"
          value={message}
          onChange={(event) => onMessageChange(event.target.value)}
        />
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            className="rounded-full bg-teal-700 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-teal-900/10 transition hover:bg-teal-800 disabled:opacity-60"
            onClick={onReview}
            disabled={loading}
          >
            {loading ? "Reading..." : "Help me respond"}
          </button>
          <button
            className="rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-orange-50"
            onClick={onLoadSample}
          >
            Use example
          </button>
        </div>
        {error ? <p className="mt-4 text-sm font-medium text-rose-600">{error}</p> : null}
      </div>

      <div className="rounded-2xl border border-white/80 bg-white/90 p-5 shadow-xl shadow-slate-900/5">
        <h3 className="text-xl font-bold">What to do next</h3>
        {triage ? (
          <div className="mt-4 space-y-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <InfoTile label="How urgent?" value={triage.analysis.urgency} />
              <InfoTile label="They need" value={triage.analysis.intent} />
              <InfoTile label="Give this to" value={triage.analysis.route} />
            </div>
            <div className="rounded-xl border border-orange-100 bg-orange-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-orange-700">Ready reply</p>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">
                {triage.draft_response}
              </p>
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-700">Useful details found</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {entitySummary.length ? (
                  entitySummary.map((entity) => (
                    <span key={`${entity.label}-${entity.value}`} className="rounded-full border border-teal-100 bg-teal-50 px-3 py-2 text-xs font-semibold text-teal-900">
                      {entity.label}: {entity.value}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-slate-500">No details found yet.</span>
                )}
              </div>
            </div>
          </div>
        ) : (
          <p className="mt-4 text-sm leading-6 text-slate-600">
            The answer will appear here with the urgency, reason for contact, useful details, and a reply draft.
          </p>
        )}
      </div>
    </section>
  );
}
