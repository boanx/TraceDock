"""Packet interval operations; times are absolute seconds on the timeline."""
import math


def ripple_positions(intervals, selected, delta):
    """Move selected and every neighbor in the movement direction equally."""
    ordered = sorted(intervals, key=lambda item: (item[1], item[2]))
    index = next(i for i, item in enumerate(ordered) if item[0] == selected)
    affected = ordered[index:] if delta >= 0 else ordered[:index+1]
    if delta < 0:
        delta = max(delta, -min(start for uid, start, end in affected))
    keys = {uid for uid, start, end in affected}
    return {uid: start + (delta if uid in keys else 0.) for uid, start, end in ordered}, delta


def snap_packet_delta(intervals, selected, delta, targets, tolerance):
    """Snap either selected edge to a target, respecting ripple's zero bound."""
    _, start, end = next(item for item in intervals if item[0] == selected)
    choices = sorted((abs(edge+delta-target), target-edge, target, label)
                     for edge in (start, end) for target, label in targets)
    for distance, candidate, target, label in choices:
        if distance > tolerance:
            break
        positions, actual = ripple_positions(intervals, selected, candidate)
        if math.isclose(actual, candidate, rel_tol=1e-12, abs_tol=1e-10):
            return positions, actual, (target, label)
    positions, actual = ripple_positions(intervals, selected, delta)
    return positions, actual, None


def interval_conflicts(intervals, selected, start, end):
    conflicts = []
    for uid, other_start, other_end in intervals:
        if uid == selected:
            continue
        tolerance = max(1e-9, 4*max(math.ulp(value) for value in (start, end, other_start, other_end)))
        if min(end, other_end)-max(start, other_start) > tolerance:
            conflicts.append((uid, other_start, other_end))
    return conflicts
