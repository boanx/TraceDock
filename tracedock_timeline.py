"""Packet interval operations; times are absolute seconds on the timeline."""
import math


def ripple_positions(intervals, selected, delta):
    """Move only the touching chain in the drag direction; gaps break it."""
    ordered = sorted(intervals, key=lambda item: (item[1], item[2]))
    index = next(i for i, item in enumerate(ordered) if item[0] == selected)
    first = last = index

    def touching(left, right):
        end, start = left[2], right[1]
        tolerance = max(1e-9, 4*max(math.ulp(end), math.ulp(start)))
        return abs(start-end) <= tolerance

    if delta >= 0:
        while last+1 < len(ordered) and touching(ordered[last], ordered[last+1]):
            last += 1
        if last+1 < len(ordered):
            delta = min(delta, max(0., ordered[last+1][1]-ordered[last][2]))
    else:
        while first > 0 and touching(ordered[first-1], ordered[first]):
            first -= 1
        lower_bound = -ordered[first][1]
        if first > 0:
            lower_bound = max(lower_bound, min(0., ordered[first-1][2]-ordered[first][1]))
        delta = max(delta, lower_bound)
    affected = ordered[first:last+1]
    keys = {uid for uid, start, end in affected}
    return {uid: start + (delta if uid in keys else 0.) for uid, start, end in ordered}, delta


def snap_packet_delta(intervals, selected, delta, targets, tolerance):
    """Snap either selected edge, respecting zero and stationary neighbors."""
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
