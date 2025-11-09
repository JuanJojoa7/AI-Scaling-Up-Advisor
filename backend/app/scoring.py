from typing import Dict, Any, List

# Scores per module are computed from question weights and normalized to 0-10

def compute_scores(answers: List[Dict[str, Any]], question_bank: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    totals = {"people": 0.0, "strategy": 0.0, "execution": 0.0, "cash": 0.0}
    max_totals = {"people": 0.0, "strategy": 0.0, "execution": 0.0, "cash": 0.0}

    for a in answers:
        qid = a["question_id"]
        q = question_bank.get(qid)
        if not q:
            continue
        module = q["module"]
        weight = float(q.get("weight", 1.0))
        # Normalize input value to [0,1]
        v = a.get("value")
        score01 = normalize_answer_value(v, q)
        totals[module] += score01 * weight
        max_totals[module] += 1.0 * weight

    result = {}
    for m in totals:
        if max_totals[m] == 0:
            result[m] = 0.0
        else:
            result[m] = round(10.0 * (totals[m] / max_totals[m]), 2)
    return result


def normalize_answer_value(value: Any, q: Dict[str, Any]) -> float:
    t = q.get("type")
    if t == "number":
        # Map to range with optional min/max; assume 0..10 by default
        v = float(value)
        min_v = float(q.get("min", 0))
        max_v = float(q.get("max", 10))
        if max_v == min_v:
            return 0.0
        v = max(min_v, min(max_v, v))
        return (v - min_v) / (max_v - min_v)
    if t == "multi":
        options = q.get("options", [])
        best = q.get("best", options[0] if options else None)
        if value == best:
            return 1.0
        # If options with ordinal property, use index-based mapping
        if value in options and best in options:
            idx = options.index(value)
            best_idx = options.index(best)
            if len(options) > 1:
                return max(0.0, 1.0 - abs(idx - best_idx) / (len(options) - 1))
        return 0.0
    # text: heuristic—presence of non-trivial length implies partial score
    if isinstance(value, str) and len(value.strip()) >= int(q.get("min_chars", 30)):
        return 1.0
    if isinstance(value, str) and len(value.strip()) > 0:
        return 0.5
    return 0.0
