import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import PreviewModal from '../components/PreviewModal'
import { API_BASE, REPORT_CARDS, REPORT_FILENAMES } from '../constants'
import './ResultsPage.css'

function LeaderSection({ leaders, companyName }) {
  if (!leaders?.length) {
    return (
      <div className="leaders-section">
        <h2>{companyName} Leaders</h2>
        <p>No leadership data available. Scraping may have failed or is still in progress.</p>
      </div>
    )
  }
  const [showAll, setShowAll] = useState(false)
  const visible = leaders.slice(0, showAll ? leaders.length : 4)
  return (
    <div className="leaders-section">
      <div className="leaders-header">
        <h2>{companyName} Leaders</h2>
        {leaders.length > 4 && (
          <button className="show-more-btn" onClick={() => setShowAll(!showAll)}>
            {showAll ? 'Show Less' : 'Show All'}
          </button>
        )}
      </div>
      {visible.map((leader, i) => (
        <a key={i} href={leader.LinkedinURL} target="_blank" rel="noopener noreferrer" className="leader-card-link">
          <div className="leader-card">
            <div className="leader-profile">
              <div className="profile-circle">{leader.Name.split(' ').map(n => n[0]).join('')}</div>
              <div className="leader-info">
                <h3>{leader.Name}</h3>
                <p>{leader.Role}</p>
              </div>
            </div>
          </div>
        </a>
      ))}
    </div>
  )
}

export default function ResultsPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [result,        setResult]        = useState(null)
  const [loading,       setLoading]       = useState(true)
  const [previewType,   setPreviewType]   = useState(null)
  const [previewContent, setPreviewContent] = useState(null)

  useEffect(() => {
    fetch(`${API_BASE}/analysis-status/${sessionId}`)
      .then(r => r.json())
      .then(data => setResult(data))
      .catch(err => console.error('Error fetching results:', err))
      .finally(() => setLoading(false))
  }, [sessionId])

  const downloadReport = async (reportType) => {
    try {
      const res = await fetch(`${API_BASE}/download-report/${sessionId}/${reportType}`)
      if (!res.ok) throw new Error(`HTTP error: ${res.status}`)
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      a.download = REPORT_FILENAMES[reportType] || 'report.docx'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      console.error('Download failed:', err)
      alert('Download failed. Please try again.')
    }
  }

  const openPreview = (reportType) => {
    if (!result) return
    const contentMap = {
      full:      result.full_report,
      website:   result.website_report,
      linkedin:  result.linkedin_report,
      financial: result.financial_report,
    }
    setPreviewContent(contentMap[reportType] || 'No content available')
    setPreviewType(reportType)
  }

  const closePreview = () => { setPreviewContent(null); setPreviewType(null) }

  if (loading) return <div className="loading">Loading results...</div>
  if (!result)  return <div className="loading">No results found for this session.</div>

  const executiveOverview = result.executive_overview || ''
  const overviewLines = executiveOverview
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0)

  const keyPoints = overviewLines.filter(line => line.startsWith('•') || line.startsWith('-'))
  const topOverview = overviewLines.slice(0, 3).join(' ')

  const getSnippet = (text) => {
    if (!text) return 'No report content available.'
    const lines = text
      .split('\n')
      .map(line => line.trim())
      .filter(line =>
        line.length > 20 &&
        !/^=+$/.test(line) &&
        !/^-+$/.test(line) &&
        !/^[A-Z\s]{10,}$/.test(line) &&
        !line.toLowerCase().includes('table of contents') &&
        !line.toLowerCase().includes('analysis date') &&
        !line.toLowerCase().includes('analysis report') &&
        !/^\d+\.\d+/.test(line)
      )
    const sentences = lines.join(' ').split(/(?<=[.!?])\s+/).filter(s => s.trim().length > 10)
    return sentences.slice(0, 2).join(' ')
  }

  const websiteSnippet1 = getSnippet(result.website_company1_report)
  const websiteSnippet2 = getSnippet(result.website_company2_report)
  const linkedinSnippet1 = getSnippet(result.linkedin_company1_report)
  const linkedinSnippet2 = getSnippet(result.linkedin_company2_report)
  const financialSnippet1 = getSnippet(result.financial_company1_report)
  const financialSnippet2 = getSnippet(result.financial_company2_report)

  return (
    <div className="results-container">
      <div className="results-header-section">
        <button onClick={() => navigate(-1)} className="back-button">← Back to Comparison</button>
        <div className="company-header"><h1>{result ? `${result.company1_name || 'Company 1'} vs ${result.company2_name || 'Company 2'}` : 'Analysis Overview'}</h1></div>
      </div>

      <div className="comparison-summary-section">
        <h2>Key Metrics Snapshot</h2>
        <div className="comparison-table">
          <div className="comparison-row header-row">
            <div>Category</div>
            <div>{result.company1_name || 'Company 1'}</div>
            <div>{result.company2_name || 'Company 2'}</div>
          </div>
          <div className="comparison-row">
            <div>Website</div>
            <div>{websiteSnippet1}</div>
            <div>{websiteSnippet2}</div>
          </div>
          <div className="comparison-row">
            <div>LinkedIn</div>
            <div>{linkedinSnippet1}</div>
            <div>{linkedinSnippet2}</div>
          </div>
          <div className="comparison-row">
            <div>Financial</div>
            <div>{financialSnippet1}</div>
            <div>{financialSnippet2}</div>
          </div>
        </div>
      </div>

      {executiveOverview ? (
        <div className="analysis-summary-section">
          <h2>Executive Summary</h2>
          <p>{topOverview || 'Executive overview is present but could not be summarized.'}</p>
          {keyPoints.length > 0 && (
            <ul className="analysis-keypoints">
              {keyPoints.map((point, idx) => (
                <li key={idx}>{point.replace(/^•\s*/, '').replace(/^\-\s*/, '')}</li>
              ))}
            </ul>
          )}
        </div>
      ) : null}

      <LeaderSection leaders={result.company1_leaders} companyName={result.company1_name} />
      <LeaderSection leaders={result.company2_leaders} companyName={result.company2_name} />

      <div className="download-section-modern">
        <div className="download-header">
          <h3>Export Reports</h3>
          <p>Download the available reports from below</p>
        </div>
        <div className="download-grid">
          {REPORT_CARDS.map(({ type, title, description }) => (
            <div className="download-card" key={type}>
              <div className="download-card-header">
                <h4>{title}</h4>
                <span className="card-description">{description}</span>
              </div>
              <div className="download-options">
                <button onClick={() => openPreview(type)} className="preview-btn">Preview {title}</button>
                <button onClick={() => downloadReport(type)} className="download-btn">Download {title}</button>
              </div>
            </div>
          ))}

          <div className="download-card">
            <div className="download-card-header">
              <h4>Analysis Summary</h4>
              <span className="card-description">Quick overview of analysis results</span>
            </div>
            <div className="download-info">
              <div className="info-item"><strong>Data Sources:</strong> Website + LinkedIn + Financial</div>
              <div className="info-item"><strong>Report Format:</strong> Microsoft Word (.docx)</div>
              <div className="info-item"><strong>Analysis Status:</strong> <span className="status-completed">Completed</span></div>
              <div className="info-item"><strong>Generated:</strong> {new Date().toLocaleDateString()}</div>
            </div>
          </div>
        </div>
      </div>

      {previewContent && (
        <PreviewModal
          previewType={previewType}
          previewContent={previewContent}
          onDownload={downloadReport}
          onClose={closePreview}
        />
      )}
    </div>
  )
}
