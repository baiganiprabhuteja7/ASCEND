import { useState } from 'react'
import { PageHeading } from '../components/PageHeading.jsx'
import { Icon } from '../components/Icon.jsx'

const challenges = [
  { category: 'LEARN', title: 'A week of curious observation', copy: 'Spend a little time noticing the nature, people, and needs around you. Capture one thing you learned each day.', duration: '7 days', level: 'Gentle start', icon: 'leaf', accent: 'challenge-green' },
  { category: 'MAKE', title: 'Share one useful skill', copy: 'Choose something you know and find a small, thoughtful way to share it with someone or a community you care about.', duration: '2 weeks', level: 'Make it yours', icon: 'heart', accent: 'challenge-purple' },
  { category: 'CONNECT', title: 'Meet your local changemakers', copy: 'Explore an issue that matters to you and learn about the people already doing good work in your community.', duration: '3 weeks', level: 'Explore at your pace', icon: 'sparkles', accent: 'challenge-blue' },
]

export function ChallengesPage() {
  const [joined, setJoined] = useState([])
  return (
    <>
      <PageHeading eyebrow="GROW TOGETHER" title="Community challenges" description="A few gentle invitations to learn, make, and connect. Choose what feels right for you." />
      <div className="demo-notice"><span className="demo-tag">DEMO CONTENT</span><span>These example challenges are for exploration only; no live community or backend is connected.</span></div>
      <section className="challenge-grid">{challenges.map((challenge) => {
        const isJoined = joined.includes(challenge.title)
        return <article className="panel challenge-card" key={challenge.title}><div className={`challenge-art ${challenge.accent}`}><div className="challenge-art-circle"><Icon name={challenge.icon} size={27} /></div><span className="challenge-category">{challenge.category}</span><span className="challenge-art-spark">✦</span></div><div className="challenge-body"><div className="challenge-meta"><span><Icon name="clock" size={13} /> {challenge.duration}</span><span>{challenge.level}</span></div><h2>{challenge.title}</h2><p>{challenge.copy}</p><button className={`button ${isJoined ? 'button-joined' : 'button-secondary'} button-full`} onClick={() => setJoined((current) => isJoined ? current.filter((title) => title !== challenge.title) : [...current, challenge.title])}>{isJoined ? <><Icon name="check" size={16} /> Added to your list</> : <>Explore this challenge <Icon name="arrow" size={15} /></>}</button></div></article>
      })}</section>
      <div className="challenge-footnote"><Icon name="sparkles" size={15} /> These prompts are starting points. Adapt them to your interests, energy, and community.</div>
    </>
  )
}
