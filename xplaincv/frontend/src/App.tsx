import { BrowserRouter, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import ClassifyPage from "./pages/ClassifyPage";
import DetailPage from "./pages/DetailPage";
import HistoryPage from "./pages/HistoryPage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <Routes>
          <Route path="/" element={<ClassifyPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/history/:id" element={<DetailPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
