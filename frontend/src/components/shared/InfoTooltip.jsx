import { useState } from 'react';
import '../../styles/info-tooltip.css';

export function InfoTooltip({ text }) {
  const [show, setShow] = useState(false);

  return (
    <span
      className="info-tooltip"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      <span className="info-tooltip__icon material-symbols-outlined">info</span>
      {show && <span className="info-tooltip__bubble">{text}</span>}
    </span>
  );
}
