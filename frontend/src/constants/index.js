export const API_BASE = 'http://localhost:8000'

export const COMPANY_FIELDS = [
  { key: 'name',     label: 'Company Name',              type: 'text', placeholder: 'Enter company name' },
  { key: 'website',  label: 'Website URL',               type: 'url',  placeholder: 'https://company.com' },
  { key: 'linkedin', label: 'LinkedIn URL / Name',       type: 'text', placeholder: 'https://linkedin.com/company/... or name' },
]

export const REPORT_CARDS = [
  { type: 'full',      title: 'Unified Report',     description: 'Complete analysis with all data sources combined' },
  { type: 'website',   title: 'Website Analysis',   description: 'Detailed website content and structure analysis' },
  { type: 'linkedin',  title: 'LinkedIn Analysis',  description: 'Company profile and social presence analysis' },
  { type: 'financial', title: 'Financial Analysis', description: 'Financial metrics and performance comparison' },
]

export const REPORT_FILENAMES = {
  full:      'unified_comparison_report.docx',
  website:   'website_analysis.docx',
  linkedin:  'linkedin_analysis.docx',
  financial: 'financial_analysis.docx',
}
