import { BrowserRouter, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import BuilderPage from "./pages/BuilderPage";
import VerifyPage from "./pages/VerifyPage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="relative min-h-screen overflow-x-hidden">
        {/* animated gradient backdrop */}
        <div className="aurora" aria-hidden>
          <i />
        </div>

        <div className="relative z-10">
          <Navbar />
          <Routes>
            <Route path="/" element={<BuilderPage />} />
            <Route path="/verify" element={<VerifyPage />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
