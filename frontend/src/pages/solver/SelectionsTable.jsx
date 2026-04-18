import '../../styles/selections-table.css';

export function SelectionsTable({ selections, paramNames }) {
  if (!selections || selections.length === 0) return null;

  return (
    <section className="selections-table">
      <h3 className="selections-table__heading">
        Optimized Selection
      </h3>
      <div className="selections-table__card">
        <div className="selections-table__scroll">
          <table className="selections-table__table">
            <thead>
              <tr>
                <th>#</th>
                {paramNames.map(name => (
                  <th key={name}>
                    {name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {selections.map((sel, i) => (
                <tr key={sel.item_id ?? i} className={i % 2 !== 0 ? 'selections-table__row--odd' : ''}>
                  <td>{i + 1}</td>
                  {paramNames.map(name => (
                    <td key={name}>
                      {typeof sel.data[name] === 'number'
                        ? sel.data[name].toLocaleString(undefined, { maximumFractionDigits: 2 })
                        : sel.data[name] ?? '\u2014'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {selections.length > 10 && (
          <div className="selections-table__footer">
            <span className="selections-table__footer-text">
              Showing {selections.length} selected items
            </span>
          </div>
        )}
      </div>
    </section>
  );
}
