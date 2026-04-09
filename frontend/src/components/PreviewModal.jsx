import React from 'react'
import './PreviewModal.css'

function classifyLine(line) {
  const t = line.trim()
  if (!t) return 'empty'
  if (/^={5,}/.test(t) || /^-{5,}/.test(t)) return 'separator'
  if (t.toUpperCase() === t && t.length > 4 && !/^\d/.test(t)) return 'heading-main'
  if (/^\d+\.0\s/.test(t)) return 'heading-section'
  if (/^\d+\.\d+\s/.test(t)) return 'heading-sub'
  if (/^[•\-\*]\s/.test(t)) return 'bullet'
  return 'body'
}

function ReportLine({ line, index }) {
  const type = classifyLine(line)
  const clean = line.replace(/\*\*([^*]+)\*\*/g, '$1').trim()

  if (type === 'empty') return <div key={index} className="preview-line preview-line--empty" />
  if (type === 'separator') return null
  if (type === 'heading-main') return <div key={index} className="preview-line preview-line--h1">{clean}</div>
  if (type === 'heading-section') return <div key={index} className="preview-line preview-line--h2">{clean}</div>
  if (type === 'heading-sub') return <div key={index} className="preview-line preview-line--h3">{clean}</div>
  if (type === 'bullet') return <div key={index} className="preview-line preview-line--bullet">{clean.replace(/^[•\-\*]\s*/, '')}</div>
  return <div key={index} className="preview-line preview-line--body">{clean}</div>
}

export default function PreviewModal({ previewType, previewContent, onDownload, onClose }) {
  return (
    <div className="preview-modal">
      <div className="preview-modal-content large-preview">
        <div className="preview-header">
          <h3>Preview: {previewType?.charAt(0).toUpperCase() + previewType?.slice(1)} Report</h3>
          <button onClick={onClose} className="close-preview">×</button>
        </div>
        <div className="preview-body large-preview-body">
          <div className="preview-text raw-content">
            {previewContent.split('\n').map((line, i) => (
              <ReportLine key={i} line={line} index={i} />
            ))}
          </div>
        </div>
        <div className="preview-footer">
          <button onClick={() => onDownload(previewType)} className="download-btn primary">
            Download This Report
          </button>
          <button onClick={onClose} className="close-btn">Close Preview</button>
        </div>
      </div>
    </div>
  )
}
