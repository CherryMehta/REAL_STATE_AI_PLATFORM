import { useMemo, useState } from "react";
import {
  analyzeTriage,
  evaluateAnswer,
  generateQuiz,
  ingestListing,
} from "./api.js";
import { ListingPractice } from "./components/ListingPractice.jsx";
import { MessageReview } from "./components/MessageReview.jsx";
import { NavigationTabs } from "./components/NavigationTabs.jsx";
import { ProjectHeader } from "./components/ProjectHeader.jsx";

const sampleListing = `Property ID: RE-1029

Modern 3-bedroom apartment in a gated community near downtown.

- Asking price: $485,000
- Availability: 2026-05-15
- Address: 214 Maple Grove Avenue, Austin, TX 78704
- HOA: $320/month
- Annual taxes: $6,820
- Contact: listings@evergreenhomes.com
- Phone: (512) 555-0147

Highlights:
- Open-plan kitchen with quartz counters
- Two secure parking spaces
- Balcony facing the community garden
- Close to schools, transit, and retail`;

function App() {
  const [tab, setTab] = useState("triage");
  const [message, setMessage] = useState(
    "Hi, I need the listing ID and availability for RE-1029. Can the owner share a move-in date this week?",
  );
  const [triage, setTriage] = useState(null);
  const [triageError, setTriageError] = useState("");
  const [triageLoading, setTriageLoading] = useState(false);

  const [documentId, setDocumentId] = useState("re-1029-demo");
  const [listingText, setListingText] = useState(sampleListing);
  const [quizSet, setQuizSet] = useState(null);
  const [quizError, setQuizError] = useState("");
  const [quizNotice, setQuizNotice] = useState("");
  const [quizLoading, setQuizLoading] = useState(false);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [evaluations, setEvaluations] = useState({});

  const entitySummary = useMemo(() => triage?.analysis.entities ?? [], [triage]);

  async function runTriage() {
    setTriageLoading(true);
    setTriageError("");
    try {
      const result = await analyzeTriage(message);
      setTriage(result);
    } catch (error) {
      setTriageError(error instanceof Error ? error.message : "Unable to review the message.");
    } finally {
      setTriageLoading(false);
    }
  }

  async function loadQuizData() {
    setQuizLoading(true);
    setQuizError("");
    setQuizNotice("");
    try {
      const ingestResult = await ingestListing(documentId, listingText);
      setQuizNotice(`Saved ${ingestResult.chunks_indexed} study note(s) from this listing.`);
      const generated = await generateQuiz(documentId, 3);
      setQuizSet(generated);
      setEvaluations({});
      setSelectedAnswers({});
    } catch (error) {
      setQuizError(error instanceof Error ? error.message : "Unable to prepare the practice set.");
    } finally {
      setQuizLoading(false);
    }
  }

  async function gradeQuestion(question) {
    const answer = selectedAnswers[question.question_id] ?? "";
    if (!answer.trim()) {
      setQuizError("Please choose an answer before checking it.");
      return;
    }

    setQuizLoading(true);
    setQuizError("");
    try {
      const evaluation = await evaluateAnswer({
        document_id: documentId,
        question_id: question.question_id,
        question: question.question,
        answer,
      });
      setEvaluations((current) => ({ ...current, [question.question_id]: evaluation }));
    } catch (error) {
      setQuizError(error instanceof Error ? error.message : "Unable to check the answer.");
    } finally {
      setQuizLoading(false);
    }
  }

  function selectAnswer(questionId, option) {
    setSelectedAnswers((current) => ({
      ...current,
      [questionId]: option,
    }));
  }

  return (
    <div className="min-h-screen bg-[linear-gradient(135deg,#fff7ed_0%,#f0fdfa_48%,#eef2ff_100%)] text-slate-900">
      <main className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-5 sm:px-6 lg:px-8">
        <ProjectHeader />
        <NavigationTabs activeTab={tab} onChange={setTab} />

        {tab === "triage" ? (
          <MessageReview
            entitySummary={entitySummary}
            error={triageError}
            loading={triageLoading}
            message={message}
            onLoadSample={() => setMessage("Hi, I need the listing ID and availability for RE-1029.")}
            onMessageChange={setMessage}
            onReview={runTriage}
            triage={triage}
          />
        ) : (
          <ListingPractice
            documentId={documentId}
            error={quizError}
            evaluations={evaluations}
            listingText={listingText}
            loading={quizLoading}
            notice={quizNotice}
            onBuildPractice={loadQuizData}
            onCheckAnswer={gradeQuestion}
            onDocumentIdChange={setDocumentId}
            onListingTextChange={setListingText}
            onLoadSample={() => setListingText(sampleListing)}
            onSelectAnswer={selectAnswer}
            quizSet={quizSet}
            selectedAnswers={selectedAnswers}
          />
        )}
      </main>
    </div>
  );
}

export default App;
