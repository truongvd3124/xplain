import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar'
import BatchDetailPage from './pages/BatchDetailPage'
import DashboardPage from './pages/DashboardPage'
import ExplainabilityPage from './pages/ExplainabilityPage'
import ProfileBuilderPage from './pages/ProfileBuilderPage'
import VerifyPage from './pages/VerifyPage'

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/builder" element={<ProfileBuilderPage />} />
        <Route path="/verify" element={<VerifyPage />} />
        <Route path="/batches/:id" element={<BatchDetailPage />} />
        <Route path="/results/:id" element={<ExplainabilityPage />} />
      </Routes>
    </BrowserRouter>
  )
}
