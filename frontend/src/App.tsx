import { Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { AppHeader } from "@/components/AppHeader";
import { LandingPage } from "@/pages/LandingPage";
import { GeneratePage } from "@/pages/GeneratePage";
import { HistoryPage } from "@/pages/HistoryPage";
import { AuthPage } from "@/pages/AuthPage";

function Contained({ children }: { children: React.ReactNode }) {
  return <div className="w-full max-w-5xl mx-auto px-4 py-8">{children}</div>;
}

export default function App() {
  return (
    <div className="min-h-full flex flex-col">
      <AppHeader />
      <main className="flex-1 w-full">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/create" element={<Contained><GeneratePage /></Contained>} />
          <Route path="/history" element={<Contained><HistoryPage /></Contained>} />
          <Route path="/login" element={<AuthPage />} />
        </Routes>
      </main>
      <Toaster
        theme="dark"
        position="bottom-right"
        toastOptions={{
          style: {
            background: "#1F1F2A",
            border: "1px solid #2A2A36",
            color: "#EDEDF2",
          },
        }}
      />
    </div>
  );
}
