"""
Bozok Roket Takımı - OpenRocket (.ork / .ork.zip) Geometri Ayrıştırıcı
OpenRocket tasarım dosyasından burun konisi (Von Kármán/Haack, Ogive vb.),
gövde boruları, trapez/eliptik kanatçıklar, motor kundağı ve rail button
ölçülerini birebir okuyup 3D görselleştirici için JSON uyumlu yapıya çevirir.
"""

from __future__ import annotations

import math
import os
import xml.etree.ElementTree as ET
import zipfile
from typing import Any, Dict, List, Optional


def _float_text(el: Optional[ET.Element], tag: str, default: float = 0.0) -> float:
    if el is None:
        return default
    child = el.find(tag)
    if child is None or child.text is None:
        return default
    text = child.text.strip().lower()
    if text in ("", "auto", "nan"):
        return default
    try:
        return float(text)
    except ValueError:
        return default


def _int_text(el: Optional[ET.Element], tag: str, default: int = 0) -> int:
    return int(round(_float_text(el, tag, float(default))))


def _str_text(el: Optional[ET.Element], tag: str, default: str = "") -> str:
    if el is None:
        return default
    child = el.find(tag)
    if child is None or child.text is None:
        return default
    return child.text.strip()


def _resolve_axial_offset(
    el: ET.Element,
    parent_z_start: float,
    parent_length: float,
    component_length: float,
) -> float:
    """OpenRocket axialoffset/position metodlarını (top/bottom/middle/absolute) mutlak z'ye çevirir."""
    pos_el = el.find("position")
    ao_el = el.find("axialoffset")

    method = "top"
    val = 0.0

    if pos_el is not None and pos_el.text:
        method = pos_el.attrib.get("type", "top").strip().lower()
        try:
            val = float(pos_el.text.strip())
        except ValueError:
            val = 0.0
    elif ao_el is not None and ao_el.text:
        method = ao_el.attrib.get("method", "top").strip().lower()
        try:
            val = float(ao_el.text.strip())
        except ValueError:
            val = 0.0

    if method == "top":
        return parent_z_start + val
    if method == "bottom":
        return parent_z_start + parent_length - component_length + val
    if method == "middle":
        return parent_z_start + 0.5 * (parent_length - component_length) + val
    if method == "absolute":
        return val
    return parent_z_start + val


def _sample_nosecone_profile(
    length: float,
    aft_radius: float,
    shape: str = "haack",
    shape_param: float = 0.0,
    steps: int = 44,
) -> List[List[float]]:
    """
    OpenRocket burun konisi şekline göre [x, r] profil noktaları üretir.
    x=0 burun ucu, x=length gövde birleşim noktasıdır.
    """
    if length <= 0 or aft_radius <= 0:
        return [[0.0, 0.0], [max(length, 0.1), max(aft_radius, 0.02)]]

    shape = (shape or "haack").lower()
    pts: List[List[float]] = []

    for i in range(steps + 1):
        t = i / steps  # 0..1
        x = t * length

        if shape == "haack":
            # LD-Haack (Von Kármán, C=0) / LV-Haack (C=1/3)
            cos_theta = max(-1.0, min(1.0, 1.0 - 2.0 * t))
            theta = math.acos(cos_theta)
            val = theta - 0.5 * math.sin(2.0 * theta) + shape_param * (math.sin(theta) ** 3)
            r = (aft_radius / math.sqrt(math.pi)) * math.sqrt(max(0.0, val))
        elif shape == "ogive":
            # Tangent / Secant Ogive
            k = max(0.01, min(1.0, shape_param if shape_param > 0 else 1.0))
            rho = (aft_radius ** 2 + length ** 2) / (2.0 * aft_radius)
            # k=1 tangent ogive
            r = math.sqrt(max(0.0, rho ** 2 - (length - x) ** 2)) + aft_radius - rho
            if k < 1.0:
                r = (1.0 - k) * (aft_radius * t) + k * r
        elif shape == "ellipsoid":
            r = aft_radius * math.sqrt(max(0.0, 1.0 - (1.0 - t) ** 2))
        elif shape == "parabolic":
            k = max(0.0, min(1.0, shape_param if shape_param > 0 else 1.0))
            r = aft_radius * ((2.0 * t - k * (t ** 2)) / (2.0 - k))
        elif shape == "power":
            n = max(0.05, min(1.0, shape_param if shape_param > 0 else 0.5))
            r = aft_radius * (t ** n)
        else:
            # Conical fallback
            r = aft_radius * t

        pts.append([round(x, 6), round(max(0.0, r), 6)])

    # Uç ve taban noktalarını sabitle
    pts[0] = [0.0, 0.0]
    pts[-1] = [round(length, 6), round(aft_radius, 6)]
    return pts


def _read_ork_xml(file_path: str) -> bytes:
    """Hem sıkıştırılmış (.ork / .ork.zip) hem ham XML (.ork) dosyalarını okur."""
    with open(file_path, "rb") as f:
        header = f.read(4)

    if header[:2] == b"PK":
        with zipfile.ZipFile(file_path, "r") as zf:
            names = zf.namelist()
            # Öncelik: rocket.ork veya .ork / .xml dosyası
            for preferred in ("rocket.ork",):
                if preferred in names:
                    data = zf.read(preferred)
                    if data[:2] == b"PK":
                        # İç içe zip durumu
                        import io
                        with zipfile.ZipFile(io.BytesIO(data), "r") as inner:
                            for iname in inner.namelist():
                                if iname.endswith((".ork", ".xml")):
                                    return inner.read(iname)
                    return data
            for name in names:
                if name.lower().endswith((".ork", ".xml")):
                    return zf.read(name)
            if names:
                return zf.read(names[0])
        raise ValueError(f"ZIP arşivi içinde geçerli OpenRocket XML bulunamadı: {file_path}")

    with open(file_path, "rb") as f:
        return f.read()


def get_default_rocket_spec() -> Dict[str, Any]:
    """Bozok Orta İrtifa Roketi (başarılı 3) doğrulanmış yedek 3D geometri modeli."""
    nose_len = 0.45
    radius = 0.065
    return {
        "name": "başarılı 3",
        "source": "builtin_fallback",
        "total_length": 2.73,
        "max_radius": radius,
        "nosecone": {
            "name": "burun konisi",
            "z_start": 0.0,
            "z_end": nose_len,
            "length": nose_len,
            "aft_radius": radius,
            "shape": "haack",
            "shape_param": 0.0,
            "material": "Fiberglass",
            "profile": _sample_nosecone_profile(nose_len, radius, "haack", 0.0),
        },
        "body_tubes": [
            {
                "name": "ust govde",
                "z_start": 0.45,
                "z_end": 1.43,
                "length": 0.98,
                "radius": radius,
                "material": "Fiberglass",
            },
            {
                "name": "alt govde",
                "z_start": 1.43,
                "z_end": 2.73,
                "length": 1.30,
                "radius": radius,
                "material": "Fiberglass",
            },
        ],
        "transitions": [],
        "fin_sets": [
            {
                "name": "Trapezoidal Fin Set",
                "type": "trapezoid",
                "count": 3,
                "z_start": 2.48,
                "body_radius": radius,
                "root_chord": 0.19,
                "tip_chord": 0.07,
                "sweep_length": 0.11,
                "height": 0.10,
                "thickness": 0.004,
                "angle_offset_deg": 0.0,
                "material": "Aluminum",
            }
        ],
        "rail_buttons": [
            {
                "name": "on kaydırma ayagı",
                "z": 1.53,
                "body_radius": radius,
                "angle_deg": 180.0,
                "outer_diameter": 0.0097,
                "height": 0.0097,
            },
            {
                "name": "arka kaydırma ayagı",
                "z": 2.63,
                "body_radius": radius,
                "angle_deg": 180.0,
                "outer_diameter": 0.0097,
                "height": 0.0097,
            },
        ],
        "motor_mount": {
            "name": "motor kundagı",
            "z_start": 1.79,
            "z_end": 2.73,
            "radius": 0.04,
            "length": 0.94,
        },
        "seams": [0.45, 1.43],
    }


def parse_ork_file(file_path: str) -> Dict[str, Any]:
    """
    Verilen .ork veya .ork.zip dosyasını okuyarak 3D roket geometrisini çıkarır.
    Hata durumunda anlamlı bir istisna yükseltir.
    """
    xml_bytes = _read_ork_xml(file_path)
    root = ET.fromstring(xml_bytes)

    rocket_el = root.find("rocket")
    if rocket_el is None:
        raise ValueError("Geçersiz OpenRocket dosyası: <rocket> etiketi bulunamadı.")

    rocket_name = _str_text(rocket_el, "name", os.path.basename(file_path))

    spec: Dict[str, Any] = {
        "name": rocket_name,
        "source": os.path.basename(file_path),
        "total_length": 0.0,
        "max_radius": 0.065,
        "nosecone": None,
        "body_tubes": [],
        "transitions": [],
        "fin_sets": [],
        "rail_buttons": [],
        "motor_mount": None,
        "seams": [],
    }

    z_cursor = 0.0
    max_radius = 0.0

    stages = rocket_el.findall("./subcomponents/stage")
    for stage in stages:
        subc = stage.find("subcomponents")
        if subc is None:
            continue

        for comp in subc:
            tag = comp.tag.lower()

            if tag == "nosecone":
                length = _float_text(comp, "length", 0.45)
                aft_r = _float_text(comp, "aftradius", 0.065)
                shape = _str_text(comp, "shape", "haack")
                shape_param = _float_text(comp, "shapeparameter", 0.0)
                mat_el = comp.find("material")
                material = mat_el.text.strip() if (mat_el is not None and mat_el.text) else "Fiberglass"

                spec["nosecone"] = {
                    "name": _str_text(comp, "name", "Nose Cone"),
                    "z_start": round(z_cursor, 6),
                    "z_end": round(z_cursor + length, 6),
                    "length": round(length, 6),
                    "aft_radius": round(aft_r, 6),
                    "shape": shape,
                    "shape_param": shape_param,
                    "material": material,
                    "profile": _sample_nosecone_profile(length, aft_r, shape, shape_param),
                }
                z_cursor += length
                max_radius = max(max_radius, aft_r)
                spec["seams"].append(round(z_cursor, 6))

            elif tag == "bodytube":
                length = _float_text(comp, "length", 1.0)
                radius = _float_text(comp, "radius", max_radius or 0.065)
                mat_el = comp.find("material")
                material = mat_el.text.strip() if (mat_el is not None and mat_el.text) else "Fiberglass"

                z_start = z_cursor
                z_end = z_cursor + length

                spec["body_tubes"].append({
                    "name": _str_text(comp, "name", "Body Tube"),
                    "z_start": round(z_start, 6),
                    "z_end": round(z_end, 6),
                    "length": round(length, 6),
                    "radius": round(radius, 6),
                    "material": material,
                })

                # Alt bileşenleri tara (kanatçık, motor kundağı, rail button)
                bt_sub = comp.find("subcomponents")
                if bt_sub is not None:
                    for child in bt_sub:
                        ctag = child.tag.lower()

                        if ctag == "trapezoidfinset":
                            fincount = _int_text(child, "fincount", _int_text(child, "instancecount", 3))
                            root_chord = _float_text(child, "rootchord", 0.19)
                            tip_chord = _float_text(child, "tipchord", 0.07)
                            sweep = _float_text(child, "sweeplength", 0.11)
                            height = _float_text(child, "height", 0.10)
                            thickness = max(0.002, _float_text(child, "thickness", 0.004))
                            angle_off = _float_text(child, "angleoffset", _float_text(child, "rotation", 0.0))
                            fin_mat_el = child.find("material")
                            fin_mat = (
                                fin_mat_el.text.strip()
                                if (fin_mat_el is not None and fin_mat_el.text)
                                else "Aluminum"
                            )
                            fin_z = _resolve_axial_offset(child, z_start, length, root_chord)
                            spec["fin_sets"].append({
                                "name": _str_text(child, "name", "Fin Set"),
                                "type": "trapezoid",
                                "count": max(1, fincount),
                                "z_start": round(fin_z, 6),
                                "body_radius": round(radius, 6),
                                "root_chord": round(root_chord, 6),
                                "tip_chord": round(tip_chord, 6),
                                "sweep_length": round(sweep, 6),
                                "height": round(height, 6),
                                "thickness": round(thickness, 6),
                                "angle_offset_deg": round(angle_off, 3),
                                "material": fin_mat,
                            })

                        elif ctag == "ellipticalfinset":
                            fincount = _int_text(child, "fincount", 3)
                            root_chord = _float_text(child, "rootchord", 0.18)
                            height = _float_text(child, "height", 0.10)
                            thickness = max(0.002, _float_text(child, "thickness", 0.004))
                            angle_off = _float_text(child, "angleoffset", 0.0)
                            fin_z = _resolve_axial_offset(child, z_start, length, root_chord)
                            spec["fin_sets"].append({
                                "name": _str_text(child, "name", "Elliptical Fin Set"),
                                "type": "elliptical",
                                "count": max(1, fincount),
                                "z_start": round(fin_z, 6),
                                "body_radius": round(radius, 6),
                                "root_chord": round(root_chord, 6),
                                "tip_chord": round(root_chord * 0.4, 6),
                                "sweep_length": round(root_chord * 0.3, 6),
                                "height": round(height, 6),
                                "thickness": round(thickness, 6),
                                "angle_offset_deg": round(angle_off, 3),
                                "material": "Aluminum",
                            })

                        elif ctag == "railbutton":
                            outer_d = _float_text(child, "outerdiameter", 0.0097)
                            rb_h = _float_text(child, "height", 0.0097)
                            angle_deg = _float_text(child, "angleoffset", 180.0)
                            rb_z = _resolve_axial_offset(child, z_start, length, outer_d)
                            spec["rail_buttons"].append({
                                "name": _str_text(child, "name", "Rail Button"),
                                "z": round(rb_z, 6),
                                "body_radius": round(radius, 6),
                                "angle_deg": round(angle_deg, 3),
                                "outer_diameter": round(outer_d, 6),
                                "height": round(rb_h, 6),
                            })

                        elif ctag == "innertube":
                            if child.find("motormount") is not None:
                                m_len = _float_text(child, "length", 0.5)
                                m_rad = _float_text(child, "outerradius", radius * 0.6)
                                m_z = _resolve_axial_offset(child, z_start, length, m_len)
                                spec["motor_mount"] = {
                                    "name": _str_text(child, "name", "Motor Mount"),
                                    "z_start": round(m_z, 6),
                                    "z_end": round(m_z + m_len, 6),
                                    "radius": round(m_rad, 6),
                                    "length": round(m_len, 6),
                                }

                z_cursor = z_end
                max_radius = max(max_radius, radius)
                spec["seams"].append(round(z_cursor, 6))

            elif tag == "transition":
                length = _float_text(comp, "length", 0.1)
                fore_r = _float_text(comp, "foreradius", max_radius or 0.065)
                aft_r = _float_text(comp, "aftradius", fore_r)
                spec["transitions"].append({
                    "name": _str_text(comp, "name", "Transition"),
                    "z_start": round(z_cursor, 6),
                    "z_end": round(z_cursor + length, 6),
                    "length": round(length, 6),
                    "fore_radius": round(fore_r, 6),
                    "aft_radius": round(aft_r, 6),
                })
                z_cursor += length
                max_radius = max(max_radius, fore_r, aft_r)
                spec["seams"].append(round(z_cursor, 6))

    # Son seam (kuyruk ucu) haricindeki ara birleşim çizgilerini tut
    spec["seams"] = [s for s in spec["seams"] if 0.001 < s < z_cursor - 0.001]
    spec["total_length"] = round(z_cursor, 6) if z_cursor > 0 else 2.73
    spec["max_radius"] = round(max_radius, 6) if max_radius > 0 else 0.065

    return spec


def find_default_ork_path(base_dir: Optional[str] = None) -> Optional[str]:
    """Varsayılan OpenRocket tasarım dosyasını proje veya Tasarim klasöründe arar."""
    if base_dir is None:
        # 2_Ground_Control/telemetry/core/ork_parser.py -> 2_Ground_Control
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    candidates = [
        os.path.join(base_dir, "assets", "bozok_rocket.ork"),
        os.path.join(base_dir, "assets", "rocket.ork"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path

    # Üst klasörlerdeki Tasarim dizinini de kontrol et
    tasarim_dirs = [
        os.path.abspath(os.path.join(base_dir, "..", "..", "Tasarim")),
        os.path.abspath(os.path.join(base_dir, "..", "Tasarim")),
    ]
    for tdir in tasarim_dirs:
        if os.path.isdir(tdir):
            for fname in sorted(os.listdir(tdir)):
                if fname.lower().endswith((".ork", ".ork.zip")):
                    return os.path.join(tdir, fname)

    return None


def load_rocket_spec(file_path: Optional[str] = None) -> Dict[str, Any]:
    """Verilen veya varsayılan .ork dosyasını yükler; sorun çıkarsa yedek modeli döner."""
    target = file_path or find_default_ork_path()
    if target and os.path.isfile(target):
        try:
            return parse_ork_file(target)
        except Exception as err:
            print(f"[ORK Ayrıştırıcı Uyarısı] '{target}' okunamadı ({err}); varsayılan model kullanılıyor.")
    return get_default_rocket_spec()
