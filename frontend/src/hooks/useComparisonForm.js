import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { API_BASE } from '../constants'
import {
  validateURL,
  validateLinkedInURL,
  isLinkedinName,
  resolveLinkedinUrl,
} from './useLinkedinResolver'

const INITIAL_FORM = {
  company1_name:     'KANINI',
  company2_name:     '',
  company1_website:  'https://kanini.com/',
  company2_website:  '',
  company1_linkedin: 'https://www.linkedin.com/company/kanini/',
  company2_linkedin: '',
}

export default function useComparisonForm() {
  const navigate = useNavigate()

  const [formData,          setFormData]          = useState(INITIAL_FORM)
  const [loading,           setLoading]           = useState(false)
  const [isSubmitting,      setIsSubmitting]      = useState(false)
  const [terminalOutput,    setTerminalOutput]    = useState([])
  const [sessionId,         setSessionId]         = useState(null)
  const [error,             setError]             = useState('')
  const [usePredefinedData, setUsePredefinedData] = useState(false)
  const [validationErrors,  setValidationErrors]  = useState({})
  const [linkedinResolving, setLinkedinResolving] = useState({ company1: false, company2: false })
  const [linkedinErrors,    setLinkedinErrors]    = useState({ company1: '', company2: '' })

  const isKaniniCompany1 = formData.company1_name.toUpperCase() === 'KANINI'

  const handleLinkedinResolve = async (name, value, field) => {
    const website = field === 'company1' ? formData.company1_website : formData.company2_website
    setLinkedinResolving(prev => ({ ...prev, [field]: true }))
    setLinkedinErrors(prev => ({ ...prev, [field]: '' }))
    try {
      const resolved = await resolveLinkedinUrl(value, website)
      if (resolved) setFormData(prev => ({ ...prev, [name]: resolved }))
    } catch (err) {
      setLinkedinErrors(prev => ({ ...prev, [field]: err.message || 'Failed to resolve LinkedIn URL' }))
    } finally {
      setLinkedinResolving(prev => ({ ...prev, [field]: false }))
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    if (validationErrors[name]) setValidationErrors(prev => ({ ...prev, [name]: '' }))
    if (name === 'company1_linkedin' && linkedinErrors.company1) setLinkedinErrors(prev => ({ ...prev, company1: '' }))
    if (name === 'company2_linkedin' && linkedinErrors.company2) setLinkedinErrors(prev => ({ ...prev, company2: '' }))

    if ((name === 'company1_linkedin' || name === 'company2_linkedin') && value.trim() && isLinkedinName(value)) {
      const field = name === 'company1_linkedin' ? 'company1' : 'company2'
      const timeoutId = setTimeout(() => handleLinkedinResolve(name, value.trim(), field), 1500)
      return () => clearTimeout(timeoutId)
    }
  }

  const validateForm = () => {
    const errors = {}
    if (!formData.company1_name?.trim() || formData.company1_name.trim().length < 2) errors.company1_name = 'Company name must be at least 2 characters'
    const c1web = validateURL(formData.company1_website, 'Website URL')
    if (c1web) errors.company1_website = c1web
    const c1li = validateLinkedInURL(formData.company1_linkedin)
    if (c1li) errors.company1_linkedin = c1li
    if (!formData.company2_name?.trim() || formData.company2_name.trim().length < 2) errors.company2_name = 'Company name must be at least 2 characters'
    const c2web = validateURL(formData.company2_website, 'Website URL')
    if (c2web) errors.company2_website = c2web
    const c2li = validateLinkedInURL(formData.company2_linkedin)
    if (c2li) errors.company2_linkedin = c2li
    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const isFormReady = () =>
    !linkedinResolving.company1 &&
    !linkedinResolving.company2 &&
    !linkedinErrors.company1 &&
    !linkedinErrors.company2 &&
    !isLinkedinName(formData.company1_linkedin) &&
    !isLinkedinName(formData.company2_linkedin)

  // Poll for analysis progress
  useEffect(() => {
    if (!sessionId || !loading) return
    let pollInterval
    const poll = async () => {
      try {
        const [termRes, statusRes] = await Promise.all([
          fetch(`${API_BASE}/terminal-output/${sessionId}?last_index=${terminalOutput.length}`),
          fetch(`${API_BASE}/analysis-status/${sessionId}`),
        ])
        const termData = await termRes.json()
        if (termData.lines.length > 0) setTerminalOutput(prev => [...prev, ...termData.lines])
        if (!statusRes.ok) {
          setLoading(false)
          setIsSubmitting(false)
          setError('Session not found. The server may have restarted. Please submit again.')
          clearInterval(pollInterval)
          return
        }
        const statusData = await statusRes.json()
        if (statusData.status === 'completed' || statusData.status === 'demo_mode') {
          setLoading(false)
          setIsSubmitting(false)
          clearInterval(pollInterval)
          navigate(`/results/${sessionId}`)
        } else if (statusData.status === 'error') {
          setLoading(false)
          setIsSubmitting(false)
          setError(statusData.error || 'Analysis failed')
          clearInterval(pollInterval)
        }
      } catch (err) {
        console.error('Polling error:', err)
      }
    }
    poll()
    pollInterval = setInterval(poll, 1000)
    return () => clearInterval(pollInterval)
  }, [sessionId, loading, terminalOutput.length, navigate])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (isSubmitting || loading) return
    if (!validateForm()) { setError('Please fix the validation errors before submitting'); return }
    setIsSubmitting(true)
    setLoading(true)
    setError('')
    setTerminalOutput([])
    try {
      const res = await fetch(`${API_BASE}/run-comparison`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...formData, use_predefined_data: usePredefinedData }),
      })
      if (!res.ok) throw new Error('Failed to start analysis')
      const data = await res.json()
      setSessionId(data.session_id)
      setTerminalOutput([`[${new Date().toLocaleTimeString()}] Analysis started: ${data.session_id}`])
    } catch (err) {
      setError(err.message)
      setLoading(false)
      setIsSubmitting(false)
    }
  }

  return {
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
  }
}
