import { useState } from 'react'
import { PageHeading } from '../components/PageHeading.jsx'
import { Icon } from '../components/Icon.jsx'

export function ContributionsPage() {
  const [message, setMessage] = useState('')
  const [contributions, setContributions] = useState([])

  function submitContribution(event) {
    event.preventDefault()
    const form = event.currentTarget
    if (!form.reportValidity()) return
    const values = new FormData(form)
    const contribution = {
      id: crypto.randomUUID(),
      title: String(values.get('title')).trim(),
      kind: String(values.get('kind')),
      evidence: String(values.get('evidence')).trim(),
    }
    setContributions((current) => [contribution, ...current])
    setMessage('Added to this session on this device. This demo does not submit to a backend.')
    form.reset()
  }

  return (
    <>
      <PageHeading eyebrow="MAKE YOUR WORK VISIBLE" title="Contributions" description="Capture a moment when you put a skill to work for something you care about." />
      <div className="contributions-layout">
        <section className="panel contribution-form-panel"><div className="form-heading"><div><span className="eyebrow">A MOMENT THAT MATTERED</span><h2>Share a contribution</h2><p>There is no minimum size for making a difference.</p></div><span className="form-heading-icon"><Icon name="heart" size={19} /></span></div>
          <form className="contribution-form" onSubmit={submitContribution}>
            <label className="field"><span>What did you contribute? <b>*</b></span><input name="title" type="text" placeholder="e.g. Helped organize a neighborhood clean-up" required minLength="3" maxLength="100" /></label>
            <label className="field"><span>Contribution type <b>*</b></span><select name="kind" defaultValue="" required><option value="" disabled>Choose a type</option><option>Time and volunteering</option><option>Skills and expertise</option><option>Learning and sharing</option><option>Community building</option><option>Other</option></select></label>
            <label className="field"><span>Evidence link <small>Optional</small></span><input name="evidence" type="url" placeholder="https://example.com/your-work" /></label>
            {message && <div className="local-message" role="status"><Icon name="check" size={15} /> {message}</div>}
            <div className="form-actions"><span>Only displayed here for this session.</span><button className="button button-primary" type="submit">Add contribution <Icon name="arrow" size={15} /></button></div>
          </form>
        </section>
        <aside className="contribution-aside"><div className="aside-symbol"><Icon name="sparkles" size={22} /></div><span className="eyebrow">REMEMBER</span><h2>Impact has many shapes.</h2><p>A conversation, an hour, a new idea shared. Count what feels meaningful to you.</p><div className="aside-rule" /><span className="aside-small">Your contributions are not shared publicly.</span></aside>
      </div>
      {contributions.length > 0 && <section className="panel contribution-history"><div className="panel-heading"><div><span className="eyebrow">THIS SESSION</span><h2>Your contributions</h2></div><span className="session-only-label">NOT SAVED</span></div>{contributions.map((item) => <article className="contribution-item" key={item.id}><span className="contribution-bullet"><Icon name="heart" size={15} /></span><div><h3>{item.title}</h3><p>{item.kind}{item.evidence && <> · <a href={item.evidence} target="_blank" rel="noreferrer">View evidence <Icon name="arrow" size={12} /></a></>}</p></div></article>)}</section>}
    </>
  )
}
