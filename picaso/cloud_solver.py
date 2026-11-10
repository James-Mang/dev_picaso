"""Opt-in controls for the outer equilibrium-cloud iteration.

These inexpensive operations never evaluate radiative transfer or microphysics.
Relaxation mixes additive optical moments, preserving physical bounds when the
input cloud fields are physical. Raw closure defects, not small relaxed steps,
are used to assess cloud consistency.
"""
import numpy as np


def optical_moments(tau, omega, asymmetry):
    tau, omega, asymmetry = np.broadcast_arrays(tau, omega, asymmetry)
    return np.stack((tau, tau*omega, tau*omega*asymmetry))


def optical_properties(moments):
    extinction, scattering, moment = moments
    omega = np.divide(scattering, extinction, out=np.zeros_like(scattering), where=extinction > 0)
    asymmetry = np.divide(moment, scattering, out=np.zeros_like(moment), where=scattering > 0)
    return extinction.copy(), omega, asymmetry


def scaled_cloud_defect(raw, used, atol=1e-5, rtol=.05):
    """Maximum componentwise defect; <=1 meets absolute+relative tolerance."""
    if raw.shape != used.shape or not np.all(np.isfinite(raw)) or not np.all(np.isfinite(used)):
        return np.inf
    return float(np.max(np.abs(raw-used)/(atol+rtol*np.maximum(np.abs(raw), np.abs(used)))))


def adaptive_cloud_step(raw, used, state, method='adaptive'):
    """Reduce relaxation on alternating/growing defects; cautiously release it.

    State is owned by one climate run. Reset history on convection changes.
    This is a bounded relaxation heuristic, not a line-search guarantee.
    """
    if raw.shape != used.shape or not np.all(np.isfinite(raw)) or not np.all(np.isfinite(used)):
        raise ValueError('Cloud optical moments must be finite with matching shapes')
    residual = raw-used
    alpha = state.get('alpha', .25)
    previous = state.get('residual')
    correlation = 0.
    if previous is not None and previous.shape == residual.shape:
        # Use the same scales for both vectors so a changing scale cannot
        # create a spurious direction reversal or norm increase.
        scale = 1e-5+.05*np.maximum(np.abs(raw), np.abs(used))
        now, before = residual/scale, previous/scale
        norm, old_norm = np.linalg.norm(now), np.linalg.norm(before)
        if norm*old_norm > 1e-30:
            correlation = float(np.sum(now*before)/(norm*old_norm))
        if method == 'aitken':
            # Vector Aitken relaxation, using a common optical-moment scale.
            # Bounds retain a convex mixture and limit noisy secant estimates.
            change = now-before
            denominator = float(np.sum(change*change))
            if denominator > 1e-20:
                estimate = -alpha*float(np.sum(before*change))/denominator
                if np.isfinite(estimate) and estimate > 0:
                    alpha = float(np.clip(estimate, .01, .8))
                else:
                    alpha = max(.01, .5*alpha)
        elif correlation < -.25 or norm > 1.25*old_norm:
            alpha = max(.05, .5*alpha)
        elif correlation > .5 and norm < .8*old_norm:
            alpha = min(.5, 1.2*alpha)
    mixed = used+alpha*residual
    state.update(alpha=alpha, residual=residual.copy())
    return mixed, dict(alpha=float(alpha), correlation=correlation,
                       defect=scaled_cloud_defect(raw, mixed),
                       proposal_defect=scaled_cloud_defect(raw, used))


def cloud_inner_tolerance(defect):
    """Inexact fixed-opacity forcing tolerance, normalized by internal flux.

    Cloud defect is measured in units of the cloud closure tolerance. Relax
    the thermal target while clouds are inconsistent, then recover the legacy
    early-root threshold (5e-5). Final refreshed flux must still be checked.
    """
    if not np.isfinite(defect):
        return .02
    return float(np.clip(.002*max(0., defect), 5e-5, .02))


def cloud_iteration_limit(normal_limit, defect, cap):
    """Limit work before the next cloud refresh, not the final accuracy target."""
    if cap is not None and (not np.isfinite(defect) or defect >= 1.):
        return min(normal_limit, cap)
    return normal_limit


def optical_change(current, reference):
    """Largest local relative change, including previously clear cells."""
    if (current.shape != reference.shape or not np.all(np.isfinite(current)) or
            not np.all(np.isfinite(reference))):
        return np.inf
    return float(np.max(abs(current-reference)/(1e-6+np.maximum(abs(current), abs(reference)))))


def radiation_can_skip(solved, age, temperature, reference_t, optics, reference_optics):
    return bool(solved and age < 2 and reference_optics is not None and
        np.max(abs(temperature-reference_t)/np.maximum(abs(reference_t), 1.)) < .001 and
        optical_change(optics, reference_optics) < .01)


def joint_relaxation(old_t, new_t, old_cloud, new_cloud, state, scaled=False):
    """Block-scaled joint Aitken step; convex bounds preserve cloud moments."""
    if scaled:
        # Freeze scales for this profile mapping so secants share coordinates.
        if 'thermal_scale' not in state:
            state['thermal_scale'] = 1.+.001*np.abs(old_t)
            state['cloud_scale'] = 1e-5+.05*np.maximum(abs(new_cloud), abs(old_cloud))
        thermal = (new_t-old_t)/state['thermal_scale']
        cloud = (new_cloud-old_cloud)/state['cloud_scale']
    else:
        thermal = (new_t-old_t)/np.maximum(abs(old_t), 1.)
        cloud = (new_cloud-old_cloud)/(1e-5+np.maximum(abs(new_cloud), abs(old_cloud)))
    residual = np.concatenate((thermal.ravel()/np.sqrt(thermal.size),
                               cloud.ravel()/np.sqrt(cloud.size)))
    alpha = state.get('alpha', .25)
    previous = state.get('residual')
    if previous is not None and previous.shape == residual.shape:
        delta = residual-previous
        denominator = float(delta@delta)
        if denominator > 1e-20:
            estimate = -alpha*float(previous@delta)/denominator
            alpha = float(np.clip(estimate, .02, .8)) if np.isfinite(estimate) and estimate > 0 else max(.02, alpha*.5)
    state.update(alpha=alpha, residual=residual.copy())
    return old_t+alpha*(new_t-old_t), old_cloud+alpha*(new_cloud-old_cloud), alpha
