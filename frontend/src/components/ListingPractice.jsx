export function ListingPractice({
  documentId,
  listingText,
  quizSet,
  selectedAnswers,
  evaluations,
  notice,
  error,
  loading,
  onDocumentIdChange,
  onListingTextChange,
  onBuildPractice,
  onLoadSample,
  onSelectAnswer,
  onCheckAnswer,
}) {
  return (
    <section className="grid gap-5 lg:grid-cols-[1fr_1fr]">
      <div className="rounded-2xl border border-white/80 bg-white/90 p-5 shadow-xl shadow-slate-900/5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-bold">Make a study card</h2>
            <p className="mt-1 text-sm text-slate-600">Paste a property listing and turn it into quick revision questions.</p>
          </div>
          <span className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-800">
            Practice mode
          </span>
        </div>
        <div className="mt-4 grid gap-4">
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-700">Property label</label>
            <input
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-teal-500 focus:ring-4 focus:ring-teal-100"
              value={documentId}
              onChange={(event) => onDocumentIdChange(event.target.value)}
            />
          </div>
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-700">Property notes</label>
            <textarea
              className="min-h-64 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-6 outline-none focus:border-teal-500 focus:ring-4 focus:ring-teal-100"
              value={listingText}
              onChange={(event) => onListingTextChange(event.target.value)}
            />
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            className="rounded-full bg-teal-700 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-teal-900/10 transition hover:bg-teal-800 disabled:opacity-60"
            onClick={onBuildPractice}
            disabled={loading}
          >
            {loading ? "Making..." : "Create questions"}
          </button>
          <button
            className="rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-indigo-50"
            onClick={onLoadSample}
          >
            Use example
          </button>
        </div>
        {notice ? <p className="mt-4 text-sm font-medium text-emerald-700">{notice}</p> : null}
        {error ? <p className="mt-4 text-sm font-medium text-rose-600">{error}</p> : null}
      </div>

      <div className="rounded-2xl border border-white/80 bg-white/90 p-5 shadow-xl shadow-slate-900/5">
        <h3 className="text-xl font-bold">Your practice round</h3>
        {quizSet?.questions?.length ? (
          <div className="mt-4 space-y-4">
            {quizSet.questions.map((question, index) => (
              <PracticeQuestion
                key={question.question_id}
                evaluation={evaluations[question.question_id]}
                index={index}
                loading={loading}
                question={question}
                selectedAnswer={selectedAnswers[question.question_id]}
                onCheckAnswer={onCheckAnswer}
                onSelectAnswer={onSelectAnswer}
              />
            ))}
          </div>
        ) : (
          <p className="mt-4 text-sm leading-6 text-slate-600">
            Add property notes, then create a few questions to test what you remember.
          </p>
        )}
      </div>
    </section>
  );
}

function PracticeQuestion({
  evaluation,
  index,
  loading,
  question,
  selectedAnswer,
  onCheckAnswer,
  onSelectAnswer,
}) {
  return (
    <div className="rounded-xl border border-indigo-100 bg-indigo-50/60 p-4">
      <p className="font-semibold text-slate-900">
        {index + 1}. {question.question}
      </p>
      <div className="mt-3 grid gap-2">
        {(question.options?.length ? question.options : []).map((option, optionIndex) => {
          const isSelected = selectedAnswer === option;
          return (
            <button
              key={`${question.question_id}-${optionIndex}`}
              type="button"
              className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-left text-sm transition ${
                isSelected
                  ? "border-teal-600 bg-teal-50 text-teal-950"
                  : "border-slate-200 bg-white text-slate-700 hover:border-teal-300"
              }`}
              onClick={() => onSelectAnswer(question.question_id, option)}
            >
              <span
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px] font-bold ${
                  isSelected ? "border-teal-600 bg-teal-600 text-white" : "border-slate-300 bg-white text-transparent"
                }`}
              >
                OK
              </span>
              <span>{option}</span>
            </button>
          );
        })}
      </div>
      {!question.options?.length ? (
        <p className="mt-3 text-sm text-slate-500">No choices were created for this question.</p>
      ) : null}
      <button
        className="mt-3 rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:opacity-60"
        onClick={() => onCheckAnswer(question)}
        disabled={loading}
      >
        Check answer
      </button>
      {evaluation ? (
        <div className="mt-4 rounded-xl border border-teal-200 bg-teal-50 p-4 text-sm leading-6 text-slate-700">
          <p className="font-semibold text-teal-800">
            Score: {Math.round(evaluation.score)} | {evaluation.verdict}
          </p>
          <p className="mt-2 text-slate-700">
            Your answer: {selectedAnswer ?? "Not selected"}
          </p>
          <p className="mt-2">{evaluation.explanation}</p>
          <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Best answer</p>
          <p className="mt-1">{evaluation.ideal_answer}</p>
        </div>
      ) : null}
    </div>
  );
}
