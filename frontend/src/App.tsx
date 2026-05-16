import { BrowserRouter, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import BuilderPage from "./pages/BuilderPage";
import VerifyPage from "./pages/VerifyPage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <Routes>
          <Route path="/" element={<BuilderPage />} />
          <Route path="/verify" element={<VerifyPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
