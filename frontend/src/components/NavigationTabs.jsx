const tabStyles = {
  active: "border-teal-600 bg-teal-700 text-white shadow-lg shadow-teal-900/10",
  inactive: "border-white bg-white/80 text-slate-700 shadow-sm hover:border-teal-200 hover:bg-teal-50",
};

export function NavigationTabs({ activeTab, onChange }) {
  return (
    <section className="flex flex-wrap gap-3">
      <button
        className={`rounded-full border px-5 py-3 text-sm font-semibold transition ${activeTab === "triage" ? tabStyles.active : tabStyles.inactive}`}
        onClick={() => onChange("triage")}
      >
        Sort Message
      </button>
      <button
        className={`rounded-full border px-5 py-3 text-sm font-semibold transition ${activeTab === "quiz" ? tabStyles.active : tabStyles.inactive}`}
        onClick={() => onChange("quiz")}
      >
        Practice Listing
      </button>
    </section>
  );
}
