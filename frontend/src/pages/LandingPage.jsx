import { Icon } from '../components/Icon.jsx'
import { Brand } from '../components/Brand.jsx'

const benefits = [
  { icon: 'target', title: 'Start with what matters', copy: 'Choose a goal that connects your skills with a cause you care about.' },
  { icon: 'plan', title: 'Make progress feel possible', copy: 'Turn big intentions into clear, manageable weekly actions.' },
  { icon: 'heart', title: 'See your impact grow', copy: 'Track your learning and the good you are working toward.' },
]

export function LandingPage({ onNavigate, isAuthenticated }) {
  return (
    <div className="landing">
      <header className="landing-header">
        <Brand onNavigate={onNavigate} />
        {isAuthenticated ? (
          <button className="button button-quiet" onClick={() => onNavigate('/dashboard')}>Open workspace <Icon name="arrow" size={16} /></button>
        ) : (
          <div className="landing-auth-actions">
            <button className="button button-quiet" onClick={() => onNavigate('/login')}>Log in</button>
            <button className="button button-primary" onClick={() => onNavigate('/signup')}>Sign up <Icon name="arrow" size={15} /></button>
          </div>
        )}
      </header>
      <main>
        <section className="landing-hero">
          <div className="hero-orb hero-orb-one" /><div className="hero-orb hero-orb-two" />
          <div className="hero-copy">
            <div className="hero-kicker"><span className="kicker-dot" /> YOUR NEXT CHAPTER STARTS HERE</div>
            <h1>Turn goals<br />into <span>growth.</span></h1>
            <p>Build meaningful skills, take thoughtful action, and make a difference on your own terms.</p>
            <button className="button button-primary button-large" onClick={() => onNavigate(isAuthenticated ? '/dashboard' : '/signup')}>{isAuthenticated ? 'Open workspace' : 'Get started'} <Icon name="arrow" size={17} /></button>
            <div className="hero-reassurance"><Icon name="check" size={15} /> A personal space to grow, at your pace</div>
          </div>
          <div className="hero-visual" aria-hidden="true">
            <div className="orbit orbit-outer" /><div className="orbit orbit-inner" />
            <div className="hero-visual-glow" />
            <div className="hero-card hero-card-main">
              <div className="mini-card-label">YOUR NEXT CHAPTER</div>
              <div className="hero-card-icon"><Icon name="leaf" size={20} /></div>
              <div className="hero-card-title">Learn to grow<br />a little more.</div>
              <div className="hero-card-progress"><span /><span /><span /><span /><span /></div>
              <div className="hero-card-footer"><span>One step at a time</span><span>✦</span></div>
            </div>
            <div className="float-tag tag-top"><span className="tag-dot purple-dot" /> Learn with purpose</div>
            <div className="float-tag tag-bottom"><span className="tag-dot green-dot" /> Make a difference</div>
            <div className="visual-star star-one">✦</div><div className="visual-star star-two">✧</div>
          </div>
        </section>
        <section className="landing-benefits">
          <div className="benefits-intro"><span className="eyebrow">A MORE HUMAN KIND OF PROGRESS</span><h2>Progress that feels<br />like yours.</h2><p>No pressure to have it all figured out. Just a good place to begin.</p></div>
          <div className="benefit-list">{benefits.map((benefit, index) => <article className="benefit" key={benefit.title}><div className={`benefit-number benefit-number-${index + 1}`}>0{index + 1}</div><div className="benefit-icon"><Icon name={benefit.icon} size={18} /></div><div><h3>{benefit.title}</h3><p>{benefit.copy}</p></div></article>)}</div>
        </section>
      </main>
      <footer className="landing-footer"><span>ASCEND</span><span>Turn Goals Into Growth.</span></footer>
    </div>
  )
}
