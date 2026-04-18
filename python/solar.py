"""
solar.py — Date-aware surface irradiance calculator.

Computes daily peak sun hours (PSH = kWh/m²/day) for a panel at a given
latitude, tilt, azimuth, and date.  Used by the solar_panel template and the
/api/solar/* endpoints.

Physics model
─────────────
  Declination   NOAA standard formula (accurate to ≈0.1°)
  I_sc          Spencer (1971) Earth-Sun distance correction (±3.3% variation)
  Surface irr.  Full cosine-of-incidence model on tilted + rotated surface,
                integrated over hour-angle using Simpson's rule (48 steps).
  Clear-sky      Broadband atmospheric transmittance τ = 0.75 (clear day)

Azimuth convention
──────────────────
  γ = 0°   → equator-facing (south in NH, north in SH) — optimal
  γ = +90° → west-facing
  γ = −90° → east-facing
  γ = ±180° → pole-facing (worst)

  The caller should flip the sign for southern-hemisphere "optimal" if desired;
  internally γ=0 is always treated as equator-facing regardless of hemisphere
  because the declination formula already encodes the hemisphere effect.
"""

import math
from datetime import date as _date


# ── Internal helpers ──────────────────────────────────────────────────────────

def _declination(doy: int) -> float:
    """Solar declination in degrees for day-of-year (1–365)."""
    return -23.45 * math.cos(math.radians(360 / 365 * (doy + 10)))


def _et_correction(doy: int) -> float:
    """Extraterrestrial irradiance correction for Earth-Sun distance.
    Spencer (1971): accounts for elliptical orbit (±3.3% variation).
    """
    B = math.radians(360 / 365 * (doy - 1))
    return 1.000110 + 0.034221 * math.cos(B) + 0.001280 * math.sin(B)


def _psh_surface(
    lat_rad:     float,
    decl_rad:    float,
    doy:         int,
    tilt_rad:    float,
    azimuth_rad: float,
    n_steps:     int = 49,          # odd → valid for Simpson's rule
) -> float:
    """
    Clear-sky PSH (kWh/m²/day) on a tilted surface at arbitrary azimuth.

    Integrates instantaneous surface irradiance G(ω) over all daylight hour
    angles using Simpson's composite rule.

    Irradiance formula (Liu-Jordan 1963 extended for azimuth):
        G(ω) = I_sc · E0 · max(0, cos θ)
        cos θ = sin δ sin φ cos β
              − sin δ cos φ sin β cos γ
              + cos δ cos ω cos φ cos β
              + cos δ cos ω sin φ sin β cos γ
              + cos δ sin ω      sin β sin γ

    where φ=lat, δ=decl, β=tilt, γ=azimuth, ω=hour angle.
    """
    # Sunset hour angle
    cos_omega_s = -math.tan(lat_rad) * math.tan(decl_rad)
    cos_omega_s = max(-1.0, min(1.0, cos_omega_s))   # clamp for polar conditions
    omega_s     = math.acos(cos_omega_s)

    if omega_s <= 0.0:
        return 0.0                                     # polar night

    I_sc = 1361.0 * _et_correction(doy)               # W/m² at top of atmosphere

    # Pre-compute trig factors
    sin_d  = math.sin(decl_rad)
    cos_d  = math.cos(decl_rad)
    sin_lat, cos_lat   = math.sin(lat_rad), math.cos(lat_rad)
    cos_tilt, sin_tilt = math.cos(tilt_rad), math.sin(tilt_rad)
    cos_az,   sin_az   = math.cos(azimuth_rad), math.sin(azimuth_rad)

    # Fixed terms (no ω dependence)
    fixed = sin_d * sin_lat * cos_tilt - sin_d * cos_lat * sin_tilt * cos_az

    def G(omega: float) -> float:
        cos_w, sin_w = math.cos(omega), math.sin(omega)
        cos_theta = (
            fixed
            + cos_d * cos_w * cos_lat * cos_tilt
            + cos_d * cos_w * sin_lat * sin_tilt * cos_az
            + cos_d * sin_w *            sin_tilt * sin_az
        )
        return max(0.0, I_sc * cos_theta)

    # Simpson's composite rule over [−ωs, +ωs]
    if n_steps % 2 == 0:
        n_steps += 1                                   # ensure odd
    h = 2.0 * omega_s / (n_steps - 1)

    s = G(-omega_s) + G(omega_s)
    for i in range(1, n_steps - 1):
        omega = -omega_s + i * h
        s += (4.0 if i % 2 == 1 else 2.0) * G(omega)
    integral = s * h / 3.0                             # ∫ G(ω) dω  [W/m² · rad]

    # Convert rad → hours: 1 hour = π/12 rad  →  × 12/π
    H0  = integral * 12.0 / math.pi                   # Wh/m²/day
    psh = H0 * 0.75 / 1000.0                          # PSH (kWh/m²/day), clear-sky
    return max(0.0, psh)


def _resolve_tilt(lat_deg: float, tilt_deg: float | None) -> float:
    """Optimal annual tilt ≈ abs(latitude)."""
    return abs(lat_deg) if tilt_deg is None else tilt_deg


def _resolve_azimuth(azimuth_deg: float | None) -> float:
    """Optimal azimuth: equator-facing = 0°."""
    return 0.0 if azimuth_deg is None else azimuth_deg


# ── Public API ────────────────────────────────────────────────────────────────

def peak_sun_hours(
    lat_deg:     float,
    tilt_deg:    float | None = None,
    azimuth_deg: float | None = None,
    on_date:     _date | None = None,
) -> float:
    """Daily peak sun hours for a given location, panel orientation, and date.

    Args:
        lat_deg     : Geographic latitude (−90 to +90). Positive = Northern Hemisphere.
        tilt_deg    : Panel tilt from horizontal (0° flat, 90° vertical).
                      None → optimal annual tilt = abs(latitude).
        azimuth_deg : Panel azimuth from equator-facing direction.
                      0 = south (NH) / north (SH), +90 = west, −90 = east.
                      None → optimal (0°, equator-facing).
        on_date     : Date to calculate for. None → today.

    Returns:
        PSH (kWh/m²/day) — equivalent full-sun hours.
        Typical: 2–3 (Nordic winter) · 4–5 (European avg) · 6–7 (Mediterranean) · 7–9 (desert).
    """
    d   = on_date or _date.today()
    doy = d.timetuple().tm_yday

    return round(_psh_surface(
        lat_rad     = math.radians(lat_deg),
        decl_rad    = math.radians(_declination(doy)),
        doy         = doy,
        tilt_rad    = math.radians(_resolve_tilt(lat_deg, tilt_deg)),
        azimuth_rad = math.radians(_resolve_azimuth(azimuth_deg)),
    ), 2)


def annual_avg_psh(
    lat_deg:     float,
    tilt_deg:    float | None = None,
    azimuth_deg: float | None = None,
) -> float:
    """Average daily PSH across all 365 days.

    Used to set the sunlight_hours constant in the solar_panel template when
    a location is provided.  Also used for financial calculations.
    """
    lat_rad     = math.radians(lat_deg)
    tilt_rad    = math.radians(_resolve_tilt(lat_deg, tilt_deg))
    azimuth_rad = math.radians(_resolve_azimuth(azimuth_deg))

    total = sum(
        _psh_surface(
            lat_rad, math.radians(_declination(doy)), doy,
            tilt_rad, azimuth_rad,
        )
        for doy in range(1, 366)
    )
    return round(total / 365.0, 2)


def sunlight_range_for_lat(
    lat_deg:     float,
    tilt_deg:    float | None = None,
    azimuth_deg: float | None = None,
) -> tuple[float, float]:
    """Seasonal (winter, summer) PSH extremes for a location.

    Returns (winter_psh, summer_psh) = practical min/max across the year.
    Useful as the sunlight_hours param range for the generic GenerationPage.
    """
    winter_date = _date(2024, 12, 21)   # NH winter solstice
    summer_date = _date(2024,  6, 21)   # NH summer solstice

    if lat_deg < 0:                      # SH: flip seasons
        winter_date, summer_date = summer_date, winter_date

    w = peak_sun_hours(lat_deg, tilt_deg, azimuth_deg, winter_date)
    s = peak_sun_hours(lat_deg, tilt_deg, azimuth_deg, summer_date)
    return round(w, 1), round(s, 1)


def azimuth_gain_pct(
    lat_deg:     float,
    tilt_deg:    float | None = None,
    azimuth_deg: float        = 0.0,
) -> float:
    """Annual PSH gain (%) achievable by rotating to optimal azimuth (0°).

    Returns 0.0 when azimuth_deg == 0 (already optimal).
    Positive value = you are losing this percentage vs. optimal orientation.

    Example: azimuth_gain_pct(51.5, tilt=35, azimuth_deg=45) → 4.2
    means rotating from 45° west-of-south to south would yield 4.2% more energy.
    """
    if azimuth_deg == 0.0:
        return 0.0
    optimal = annual_avg_psh(lat_deg, tilt_deg, azimuth_deg=0.0)
    current = annual_avg_psh(lat_deg, tilt_deg, azimuth_deg=azimuth_deg)
    if current <= 0:
        return 0.0
    return round((optimal / current - 1.0) * 100.0, 1)


def optimal_azimuth_label(lat_deg: float) -> str:
    """Human-readable label for the optimal panel direction."""
    return "South" if lat_deg >= 0 else "North"
