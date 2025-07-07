from .models import MatchResponse, MatchResult, StrokeInput, StrokeValidationResult
from .lib import Direction, Location, kanji_data, matches
import json
import xml.etree.ElementTree as ET
import re
from pathlib import Path

# Ruta local al índice
index_path = Path(__file__).resolve().parent / "kvg-index.json"
with open(index_path, encoding="utf-8") as f:
    kanji_svg_map = json.load(f)

# Carpeta local con los SVGs
KANJI_FOLDER = Path(__file__).resolve().parent / "kanji"

# Expresiones regulares para parsear el atributo d del path SVG
PATH_RX = re.compile(r"([MmLlCcSsQqTtAaZz])([^MmLlCcSsQqTtAaZz]*)")
ARGS_RX = re.compile(r"-?\d*\.?\d+")


def get_stroke_points(kanji: str, stroke_index: int) -> list[list[float]]:
    if kanji not in kanji_svg_map:
        raise ValueError(f"Kanji '{kanji}' no está en el mapa.")

    svg_files = kanji_svg_map[kanji]
    local_svg_path = KANJI_FOLDER / svg_files[0]

    if not local_svg_path.exists():
        raise FileNotFoundError(f"SVG para '{kanji}' no encontrado en {local_svg_path}")

    with open(local_svg_path, encoding="utf-8") as f:
        svg_content = f.read()

    root = ET.fromstring(svg_content)
    paths = root.findall(".//{http://www.w3.org/2000/svg}path")

    if stroke_index >= len(paths):
        raise IndexError(f"El kanji '{kanji}' tiene solo {len(paths)} trazos.")

    d = paths[stroke_index].attrib.get("d")
    if d is None:
        raise ValueError("El atributo 'd' no está presente en el path del SVG.")

    return parse_svg_path(d)


def parse_svg_path(d: str) -> list[list[float]]:
    commands = PATH_RX.findall(d)
    points = []
    cursor = [0.0, 0.0]

    for cmd, args_str in commands:
        args = list(map(float, ARGS_RX.findall(args_str)))
        cmd_upper = cmd.upper()

        if cmd_upper == "M" or cmd_upper == "L":
            for i in range(0, len(args), 2):
                x, y = args[i], args[i + 1]
                if cmd.islower():  # comando relativo
                    x += cursor[0]
                    y += cursor[1]
                cursor = [x, y]
                points.append(cursor[:])

        elif cmd_upper == "C":
            for i in range(0, len(args), 6):
                x, y = args[i + 4], args[i + 5]
                if cmd.islower():
                    x += cursor[0]
                    y += cursor[1]
                cursor = [x, y]
                points.append(cursor[:])

        elif cmd_upper == "S":
            for i in range(0, len(args), 4):
                x, y = args[i + 2], args[i + 3]
                if cmd.islower():
                    x += cursor[0]
                    y += cursor[1]
                cursor = [x, y]
                points.append(cursor[:])

        elif cmd_upper == "Z":
            continue

    return points

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
        return True, "Trazo correcto", user_line
    else:
        issues = []
        if not direction_ok:
            issues.append("dirección")
        if not start_ok:
            issues.append("inicio")
        if not end_ok:
            issues.append("final")
        msg = "Error en " + " / ".join(issues)
        return False, msg + (" — autocorregido" if start_ok and end_ok else ""), None


def load_expected_kanji(char):
    data = kanji_data()
    for stroke_index, kanji_group in data.items():
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
            corrected=[[int(input.user_line[0]), int(input.user_line[1])],
                       [int(input.user_line[2]), int(input.user_line[3])]],
            done=True
        )

    expected_line = expected_kanji[input.stroke_index]
    is_ok, message, corrected = check_single_stroke(input.user_line, expected_line)
    done = (input.stroke_index + 1 == len(expected_kanji)) if is_ok or "autocorregido" in message else False

    corrected_points = get_stroke_points(input.kanji, input.stroke_index)
    corrected_points_int = [[int(x), int(y)] for x, y in corrected_points]

    return StrokeValidationResult(
        ok=is_ok,
        message=message,
        corrected=corrected_points_int,
        done=done
    )
