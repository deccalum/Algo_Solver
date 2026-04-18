import '../../styles/how-it-works.css';

export function HowItWorks() {
  const steps = [
    { num: '01', title: 'Configure', desc: 'Select a template or define parameter axes with distribution types.' },
    { num: '02', title: 'Generate', desc: 'Enumerate parameter combinations. Runs are persisted to PostgreSQL.' },
    { num: '03', title: 'Optimize', desc: 'SCIP solver applies constraints (budget, capacity) and returns optimal selections.' },
  ];

  return (
    <section className="how-it-works">
      <h2 className="how-it-works__title">
        HOW IT WORKS
      </h2>
      <div className="how-it-works__steps">
        {steps.map((s, i) => (
          <div key={s.num} className="how-it-works__step-group">
            <div className="how-it-works__step">
              <div className="how-it-works__num">{s.num}</div>
              <h3 className="how-it-works__step-title">{s.title}</h3>
              <p className="how-it-works__step-desc">{s.desc}</p>
            </div>
            {i < steps.length - 1 && (
              <div className="how-it-works__arrow">&rarr;</div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
