export default function Header() {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <div className="site-header__brand">
          <span className="site-header__mark" aria-hidden="true" />
          <div>
            <span className="site-header__name">Darukaa</span>
            <span className="site-header__subtitle">Environmental Intelligence</span>
          </div>
        </div>
        <nav className="site-header__nav">
          <a href="#analysis" className="site-header__link site-header__link--active">
            Analysis
          </a>
          <a href="#evidence" className="site-header__link">
            Evidence
          </a>
        </nav>
      </div>
    </header>
  )
}
