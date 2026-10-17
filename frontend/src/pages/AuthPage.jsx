import { useState } from 'react'
import { Brand } from '../components/Brand.jsx'
import { Icon } from '../components/Icon.jsx'
import { login, signup } from '../services/api.js'

const passwordStrengthPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{12,128}$/

export function AuthPage({ mode, onNavigate, onAuthenticated, initializationError, onRetry }) {
  const isSignup = mode === 'signup'
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function submit(event) {
    event.preventDefault()
    setError('')
    const form = event.currentTarget
    if (!form.reportValidity()) return

    const values = new FormData(form)
    const fullName = String(values.get('full_name') ?? '').trim()
    const email = String(values.get('email') ?? '').trim()
    const password = String(values.get('password') ?? '')
    const confirmPassword = String(values.get('confirm_password') ?? '')

    if (isSignup && fullName.length < 2) {
      setError('Enter a name with at least two characters.')
      return
    }
    if (isSignup && !passwordStrengthPattern.test(password)) {
      setError('Use at least 12 characters, including an uppercase letter, lowercase letter, number, and symbol.')
      return
    }
    if (isSignup && password !== confirmPassword) {
      setError('Your passwords do not match.')
      return
    }

    setIsSubmitting(true)
    try {
      const result = isSignup
        ? await signup({ full_name: fullName, email, password, confirm_password: confirmPassword })
        : await login({ email, password })
      onAuthenticated(result.user)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'We could not complete your request.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="auth-page">
      <header className="auth-header">
        <Brand onNavigate={onNavigate} />
        <span className="auth-header-note">A personal space to grow, at your pace</span>
      </header>
      <section className="auth-content">
        <div className="auth-intro">
          <span className="eyebrow">YOUR NEXT CHAPTER STARTS HERE</span>
          <h1>{isSignup ? <>Make room for<br /><span>what's next.</span></> : <>Welcome<br /><span>back.</span></>}</h1>
          <p>{isSignup ? 'Create a private workspace for the goals and progress that matter to you.' : 'Pick up where you left off and keep moving toward what matters.'}</p>
        </div>
        <div className="panel auth-card">
          <div className="auth-card-heading">
            <div>
              <span className="eyebrow">{isSignup ? 'GET STARTED' : 'YOUR WORKSPACE'}</span>
              <h2>{isSignup ? 'Create your account' : 'Sign in to ASCEND'}</h2>
            </div>
            <span className="auth-card-icon"><Icon name={isSignup ? 'sparkles' : 'home'} size={19} /></span>
          </div>
          <form className="auth-form" onSubmit={submit} noValidate>
            {initializationError && (
              <div className="api-feedback api-feedback-error" role="alert">
                <span>{initializationError}</span>
                <button className="text-link" type="button" onClick={onRetry}>Retry connection</button>
              </div>
            )}
            {isSignup && (
              <label className="field">
                <span>Full name <b>*</b></span>
                <input name="full_name" type="text" autoComplete="name" minLength="2" maxLength="120" required />
              </label>
            )}
            <label className="field">
              <span>Email address <b>*</b></span>
              <input name="email" type="email" autoComplete="email" maxLength="320" required />
            </label>
            <label className="field">
              <span>Password <b>*</b></span>
              <input
                name="password"
                type="password"
                autoComplete={isSignup ? 'new-password' : 'current-password'}
                minLength={isSignup ? 12 : 1}
                maxLength="128"
                required
              />
              {isSignup && <small>At least 12 characters with uppercase, lowercase, number, and symbol.</small>}
            </label>
            {isSignup && (
              <label className="field">
                <span>Confirm password <b>*</b></span>
                <input name="confirm_password" type="password" autoComplete="new-password" minLength="12" maxLength="128" required />
              </label>
            )}
            {error && <div className="api-feedback api-feedback-error" role="alert">{error}</div>}
            <button className="button button-primary auth-submit" type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Please wait…' : isSignup ? 'Create account' : 'Log in'}
              {!isSubmitting && <Icon name="arrow" size={16} />}
            </button>
          </form>
          <p className="auth-switch">
            {isSignup ? 'Already have an account?' : 'New to ASCEND?'}{' '}
            <button className="text-link" type="button" onClick={() => onNavigate(isSignup ? '/login' : '/signup')}>
              {isSignup ? 'Log in' : 'Create an account'}
            </button>
          </p>
        </div>
      </section>
      <footer className="auth-footer"><span>ASCEND</span><span>Your growth workspace is private to your account.</span></footer>
    </main>
  )
}
