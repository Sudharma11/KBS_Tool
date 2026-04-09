import { API_BASE } from '../constants'

export function validateURL(url, fieldName) {
  if (!url?.trim()) return `${fieldName} is required`
  try {
    const u = new URL(url)
    if (!['http:', 'https:'].includes(u.protocol)) return 'URL must start with http:// or https://'
    if (!u.hostname || u.hostname.split('.').length < 2) return 'Please enter a valid domain name'
    const validTLDs = ['.com', '.org', '.net', '.io', '.co', '.in', '.us', '.uk', '.edu', '.gov', '.biz', '.info', '.tech', '.ai', '.app']
    if (!validTLDs.some(tld => u.hostname.toLowerCase().endsWith(tld))) return 'Please enter a URL with a valid domain extension'
  } catch {
    return 'Please enter a valid URL'
  }
  return null
}

export function validateLinkedInURL(url) {
  if (!url?.trim()) return 'LinkedIn URL is required'
  const urlError = validateURL(url, 'LinkedIn URL')
  if (urlError) return urlError
  try {
    const u = new URL(url)
    if (!u.hostname.includes('linkedin.com')) return 'Please enter a valid LinkedIn company URL'
    if (!u.pathname.includes('/company/')) return 'LinkedIn URL should be a company page'
    const parts = u.pathname.split('/')
    const idx = parts.indexOf('company')
    if (idx === -1 || idx >= parts.length - 1 || !parts[idx + 1]) return 'LinkedIn URL must include company identifier'
  } catch {
    return 'Please enter a valid LinkedIn URL'
  }
  return null
}

export function isLinkedinName(input) {
  if (!input?.trim()) return false
  const t = input.trim()
  return !t.startsWith('http') && !t.includes('linkedin.com/company/')
}

export async function resolveLinkedinUrl(linkedinName, website) {
  const res = await fetch(`${API_BASE}/resolve-linkedin-url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ linkedin_name: linkedinName.trim(), website: website || '' }),
  })
  if (!res.ok) throw new Error('Failed to resolve LinkedIn URL')
  const data = await res.json()
  if (data.resolved_url) return data.resolved_url
  throw new Error(data.error || 'Could not find LinkedIn URL')
}
