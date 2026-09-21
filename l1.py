"""Course-defined L1 counts; Methods Guide pp. 3-5 (not a general carrier model)."""
import numpy as np

KB = 8.617333e-5  # eV/K
NA = 3.816e15  # atoms/cm^2; converts the course per-atom DoS
E_CHARGE = 1.602176634e-19  # C
EMAX = 2.5  # eV
POINTS = 20001


def validate(ef, temperature, c, points=POINTS):
    if not all(np.isfinite(v) for v in (ef, temperature, c)):
        raise ValueError("Non-finite model parameter")
    if not 0 <= ef < EMAX or temperature <= 0 or c <= 0 or points < 3:
        raise ValueError("L1 requires 0 <= EF < 2.5 eV, positive T and c, points >= 3")


def fermi(energy, ef, temperature):
    return 1 / (np.exp(np.clip((energy - ef) / (KB * temperature), -60, 60)) + 1)


def count(ef, temperature, c, *, fermi_referenced, points=POINTS):
    validate(ef, temperature, c, points)
    energy = np.linspace(ef if fermi_referenced else 0, EMAX, points)
    return float(NA * np.trapezoid(c * energy * fermi(energy, ef, temperature), energy))


def closed_count(ef, temperature, c):
    """Infinite-upper-limit expression; check its adequacy at the finite course cutoff."""
    validate(ef, temperature, c)
    kt = KB * temperature
    return float(NA * c * kt * (ef * np.log(2) + np.pi**2 * kt / 12))


def correction(ef, temperature, c, points=POINTS):
    return count(ef, temperature, c, fermi_referenced=False, points=points) / count(
        ef, temperature, c, fermi_referenced=True, points=points)


def mobility(n_cm2, rho_ohm_sq):
    if not all(np.isfinite(v) and v > 0 for v in (n_cm2, rho_ohm_sq)):
        raise ValueError("Density and sheet resistance must be finite and positive")
    return float(1 / (E_CHARGE * n_cm2 * rho_ohm_sq))


def crossing(target, temperature, c, low, high):
    if not correction(low, temperature, c) <= target <= correction(high, temperature, c):
        raise ValueError("Requested crossing is outside the supplied sweep interval")
    for _ in range(45):
        mid = (low + high) / 2
        if correction(mid, temperature, c) < target:
            low = mid
        else:
            high = mid
    return (low + high) / 2
