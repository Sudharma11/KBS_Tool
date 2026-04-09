import React from 'react'
import './Navbar.css'

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <a className="navbar-brand" href="/">
          <div className="navbar-logo">BA</div>
          <span className="navbar-name">BizzAnalyzer</span>
        </a>
        <span className="navbar-tag">Enterprise Intelligence Platform</span>
      </div>
    </nav>
  )
}
