import React from 'react'
import useComparisonForm from '../hooks/useComparisonForm'
import { COMPANY_FIELDS } from '../constants'
import './ComparisonPage.css'

export default function ComparisonPage() {
  const {
    formData,
    loading,
    isSubmitting,
    terminalOutput,
    error,
    usePredefinedData,
    setUsePredefinedData,
    validationErrors,
    linkedinResolving,
    linkedinErrors,
    isKaniniCompany1,
    isFormReady,
    handleInputChange,
    handleSubmit,
  } = useComparisonForm()

  return (
    <div className="comparison-container">
      <div className="comparison-header">
        <h2>Compare Companies with <span>AI Intelligence</span></h2>
        <p>Enter two companies to generate a comprehensive side-by-side analysis across website, LinkedIn, and financial dimensions.</p>
      </div>

      <form onSubmit={handleSubmit} className="comparison-form">
        <div className="companies-row">
          {[1, 2].map(num => (
            <React.Fragment key={num}>
              {num === 2 && <div className="vs-separator">VS</div>}
              <div className="company-card">
                <h3>Company {num}</h3>
                {COMPANY_FIELDS.map(({ key, label, type, placeholder }) => {
                  const fieldName = `company${num}_${key}`
                  const isLinkedin = key === 'linkedin'
                  const resolving = isLinkedin && linkedinResolving[`company${num}`]
                  const liError   = isLinkedin && linkedinErrors[`company${num}`]
                  return (
                    <div className="input-group" key={fieldName}>
                      <label>{label}</label>
                      <input
                        type={type}
                        name={fieldName}
                        value={formData[fieldName]}
                        onChange={handleInputChange}
                        required={num === 2}
                        className={`editable-input${validationErrors[fieldName] ? ' error' : ''}`}
                        placeholder={placeholder}
                      />
                      {resolving && <span className="resolving-indicator">Resolving LinkedIn URL...</span>}
                      {liError    && <span className="validation-error">{liError}</span>}
                      {validationErrors[fieldName] && <span className="validation-error">{validationErrors[fieldName]}</span>}
                    </div>
                  )
                })}
              </div>
            </React.Fragment>
          ))}
        </div>

        {isKaniniCompany1 && (
          <div className="predefined-data-toggle">
            <div className="toggle-header">
              <h3>Kanini Data Source</h3>
              <span className="toggle-info">Choose data source for Kanini analysis</span>
            </div>
            <div className="toggle-options">
              <button
                type="button"
                onClick={() => setUsePredefinedData(!usePredefinedData)}
                className={`toggle-button${usePredefinedData ? ' active' : ''}`}
              >
                <span className="toggle-indicator">{usePredefinedData ? '✓' : ''}</span>
                Use PreScraped Kanini Data
              </button>
              <div className="toggle-description">
                <p><strong>{usePredefinedData ? 'Faster analysis with consistent data' : 'Slower but uses latest available data'}</strong></p>
              </div>
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={loading || isSubmitting || !isFormReady()}
          className="compare-button"
        >
          {loading || isSubmitting ? 'Running Analysis...' : 'Run Comprehensive Comparison'}
        </button>

        {loading && (
          <div className="terminal-output">
            <h4>Analysis Progress</h4>
            <div className="terminal-lines">
              {terminalOutput.length === 0
                ? <div className="terminal-line">Starting analysis... Please wait...</div>
                : terminalOutput.map((line, i) => <div key={i} className="terminal-line">{line}</div>)
              }
            </div>
          </div>
        )}
      </form>

      {error && (
        <div className="error-message">
          <h3>Error</h3>
          <p>{error}</p>
        </div>
      )}
    </div>
  )
}
