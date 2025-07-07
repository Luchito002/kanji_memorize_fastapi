from .models import MatchResponse, MatchResult, StrokeInput, StrokeValidationResult
from .lib import Direction, Location, kanji_data, matches

def check_single_stroke(user_line, expected_line):
    user_dir = Direction.of_line(user_line)
    expected_dir = Direction.of_line(expected_line)
    direction_ok = (user_dir == expected_dir) or user_dir.isclose(expected_dir)

    user_start = Location.of_point(*user_line[:2])
    expected_start = Location.of_point(*expected_line[:2])
    start_ok = (user_start == expected_start) or user_start.isclose(expected_start)

    user_end = Location.of_point(*user_line[2:])
    expected_end = Location.of_point(*expected_line[2:])
    end_ok = (user_end == expected_end) or user_end.isclose(expected_end)

    if direction_ok and start_ok and end_ok:
        return True, "Trazo correcto", expected_line
    else:
        issues = []
        if not direction_ok:
            issues.append("dirección")
        if not start_ok:
            issues.append("inicio")
        if not end_ok:
            issues.append("final")
        msg = "Error en " + " / ".join(issues)
        # Autocorrección: si inicio y final están bien, devuelve trazo corregido
        if start_ok and end_ok:
            return False, msg + " — autocorregido", expected_line
        else:
            return False, msg, user_line

def load_expected_kanji(char):
    data = kanji_data()
    for stroke_count, kanji_group in data.items():
        if char in kanji_group:
            return kanji_group[char]
    raise ValueError(f"Kanji '{char}' no encontrado en la base de datos.")



def match_kanji(strokes: list[list[float]]) -> MatchResponse:
    top_matches = matches(strokes)
    results = [MatchResult(score=int(score), kanji=kanji) for score, kanji in top_matches]
    return MatchResponse(matches=results)


def validate_stroke_logic(input: StrokeInput) -> StrokeValidationResult:
    expected_kanji = load_expected_kanji(input.kanji)

    if input.stroke_index >= len(expected_kanji):
        return StrokeValidationResult(
            ok=False,
            message="Ya se completaron todos los trazos.",
            corrected=[int(v) for v in input.user_line],
            done=True
        )

    expected_line = expected_kanji[input.stroke_index]
    is_ok, message, corrected = check_single_stroke(input.user_line, expected_line)
    done = (input.stroke_index + 1 == len(expected_kanji)) if is_ok or "autocorregido" in message else False

    return StrokeValidationResult(
        ok=is_ok,
        message=message,
        corrected=corrected,
        done=done
    )
