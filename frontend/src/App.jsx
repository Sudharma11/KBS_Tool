import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import ComparisonPage from './pages/ComparisonPage'
import ResultsPage from './pages/ResultsPage'

export default function App() {
  return (
    <Router>
      <div className="page-wrapper">
        <Routes>
          <Route path="/" element={<ComparisonPage />} />
          <Route path="/results/:sessionId" element={<ResultsPage />} />
        </Routes>
      </div>
    </Router>
  )
}
