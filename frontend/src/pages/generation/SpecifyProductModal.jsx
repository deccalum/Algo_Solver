import { useState } from 'react';
import { Icon } from '../../components/shared/Icon';
import '../../styles/specify-product-modal.css';

const EMPTY = { name: '', price: '', amount: 1, volume: '', weight: '' };

export function SpecifyProductModal({ products, onClose, onChange }) {
  const [draft, setDraft] = useState(EMPTY);
  const [error, setError] = useState('');

  function set(field, value) {
    setDraft(prev => ({ ...prev, [field]: value }));
    setError('');
  }

  function add() {
    if (!draft.price || Number(draft.price) <= 0) { setError('Price is required and must be > 0'); return; }
    if (!draft.amount || Number(draft.amount) < 1) { setError('Amount must be at least 1'); return; }
    if (!draft.volume || Number(draft.volume) <= 0) { setError('Volume is required and must be > 0'); return; }
    onChange([...products, {
      name: draft.name || `Product ${products.length + 1}`,
      price: Number(draft.price),
      amount: Math.max(1, Math.round(Number(draft.amount))),
      volume: Number(draft.volume),
      weight: draft.weight !== '' ? Number(draft.weight) : null,
    }]);
    setDraft(EMPTY);
  }

  function remove(idx) {
    onChange(products.filter((_, i) => i !== idx));
  }

  const totalCost = products.reduce((s, p) => s + p.price * p.amount, 0);
  const totalVol  = products.reduce((s, p) => s + p.volume * p.amount, 0);

  return (
    <div className="spm-overlay">
      <div className="spm-backdrop" onClick={onClose} />

      <div className="spm-modal">
        {/* Header */}
        <div className="spm-header">
          <div>
            <h3 className="spm-header__title">Specify Product</h3>
            <p className="spm-header__subtitle">
              Force-commit products before solving — consumed budget &amp; space are deducted from constraint bounds.
            </p>
          </div>
          <button className="spm-header__close-btn" onClick={onClose}>
            <Icon name="close" className="spm-header__close-icon" />
          </button>
        </div>

        <div className="spm-body">
          {/* Add form */}
          <div className="spm-form">
            <span className="spm-form__section-label">ADD PRODUCT</span>

            <div>
              <label className="spm-form__label">
                Name <span className="spm-form__label-optional">(optional)</span>
              </label>
              <input
                type="text"
                className="spm-form__input"
                placeholder="e.g. Pallet rack"
                value={draft.name}
                onChange={e => set('name', e.target.value)}
                onKeyDown={e => e.key === 'Enter' && add()}
              />
            </div>

            <div className="spm-form__grid">
              <div>
                <label className="spm-form__label">
                  Price ($) <span className="spm-form__label-required">*</span>
                </label>
                <input
                  type="number" min="0" step="0.01"
                  className="spm-form__input"
                  placeholder="0.00"
                  value={draft.price}
                  onChange={e => set('price', e.target.value)}
                />
              </div>
              <div>
                <label className="spm-form__label">
                  Amount (units) <span className="spm-form__label-required">*</span>
                </label>
                <input
                  type="number" min="1" step="1"
                  className="spm-form__input"
                  value={draft.amount}
                  onChange={e => set('amount', e.target.value)}
                />
              </div>
            </div>

            <div className="spm-form__grid">
              <div>
                <label className="spm-form__label">
                  Volume (m³) <span className="spm-form__label-required">*</span>
                </label>
                <input
                  type="number" min="0" step="0.001"
                  className="spm-form__input"
                  placeholder="0.001"
                  value={draft.volume}
                  onChange={e => set('volume', e.target.value)}
                />
              </div>
              <div>
                <label className="spm-form__label">
                  Weight (kg) <span className="spm-form__label-optional">(optional)</span>
                </label>
                <input
                  type="number" min="0" step="0.01"
                  className="spm-form__input"
                  placeholder="—"
                  value={draft.weight}
                  onChange={e => set('weight', e.target.value)}
                />
              </div>
            </div>

            {error && <p className="spm-form__error">{error}</p>}

            <button className="spm-form__add-btn" onClick={add}>
              + ADD
            </button>
          </div>

          {/* Product list */}
          {products.length > 0 ? (
            <div className="spm-list">
              <div className="spm-list__header">
                <span className="spm-list__label">COMMITTED ({products.length})</span>
                <div className="spm-list__totals">
                  <span className="spm-list__total-cost">
                    ${totalCost.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                  <span className="spm-list__total-dot">&middot;</span>
                  <span className="spm-list__total-vol">{totalVol.toFixed(3)} m³</span>
                </div>
              </div>
              {products.map((p, i) => (
                <div key={i} className="spm-item">
                  <div className="spm-item__info">
                    <span className="spm-item__name">{p.name}</span>
                    <div className="spm-item__meta">
                      <span className="spm-item__cost">
                        ${(p.price * p.amount).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </span>
                      <span>&times;{p.amount} @ ${p.price.toLocaleString()}/unit</span>
                      <span className="spm-item__dot">&middot;</span>
                      <span>{(p.volume * p.amount).toFixed(3)} m³ total</span>
                      {p.weight != null && (
                        <><span className="spm-item__dot">&middot;</span><span>{(p.weight * p.amount).toFixed(1)} kg</span></>
                      )}
                    </div>
                  </div>
                  <button className="spm-item__remove-btn" onClick={() => remove(i)}>
                    <Icon name="close" className="spm-item__remove-icon" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="spm-empty">No products committed yet.</p>
          )}
        </div>

        {/* Footer */}
        <div className="spm-footer">
          <p className="spm-footer__info">
            {products.length === 0
              ? 'No committed products — solver uses full bounds'
              : `${products.length} product${products.length !== 1 ? 's' : ''} · reduces solver budget & space bounds`}
          </p>
          <button className="spm-footer__done-btn" onClick={onClose}>
            DONE
          </button>
        </div>
      </div>
    </div>
  );
}
