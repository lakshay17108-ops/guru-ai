/**
 * App — Root layout component.
 *
 * Wraps everything in LearningPathProvider for state management.
 * Layout: Header → centered content area with InputForm + conditional
 * display (LoadingState | ErrorState | CurriculumDisplay).
 */

import { LearningPathProvider } from './context/LearningPathContext';
import Header from './components/Header';
import InputForm from './components/InputForm';
import LoadingState from './components/LoadingState';
import ErrorState from './components/ErrorState';
import CurriculumDisplay from './components/CurriculumDisplay';
import { useLearningPath } from './context/LearningPathContext';

function AppContent() {
  const { isLoading, error, learningPath } = useLearningPath();

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        <InputForm />

        {isLoading && <LoadingState />}
        {error && !isLoading && <ErrorState />}
        {learningPath && !isLoading && <CurriculumDisplay />}
      </main>
    </div>
  );
}

function App() {
  return (
    <LearningPathProvider>
      <AppContent />
    </LearningPathProvider>
  );
}

export default App;
