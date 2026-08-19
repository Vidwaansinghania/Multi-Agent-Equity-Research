"""Brand palette and contrast checks for Method 2 exports.

Every export for a company is styled in that company's own colours, the same
rule Method 1 works to. This module holds the checks that decide where a brand
colour may be used, so no run has to re-derive them.

Where a colour may go, by contrast against its background:
    body text, headings, white-on-colour badges   4.5:1
    chart marks, thin rules, small fills          3:1
    large solid fills, thick keylines             no floor

Compute contrast, never eyeball it. When a brand colour fails, darken the step
and keep the hue.

The tritanopia check is deliberately absent. The Vienot 1999 LMS-to-RGB inverse
these palette scripts use is validated for protanopia and deuteranopia only;
pushing the tritan cone through the same inverse saturates every input to
magenta and returns a distance of zero between colours that are plainly
different. cvd_delta_e raises on kind='trit' rather than returning a misleading
number.
"""

import math

# Fallback chart palette, used for series beyond the brand hue. Slot 1 always
# belongs to the company's own colour.
NEUTRAL_SERIES = ["#4C6EF5", "#E8590C", "#2B8A3E", "#9C36B5", "#0B7285", "#A61E4D"]

INK = "#1A1A1A"
GREY = "#6B6B6B"
RULE = "#D8D8D8"
PALE = "#F4F4F4"
POS = "#2B8A3E"
NEG = "#C92A2A"


# ------------------------------------------------------------- colour space --

def to_rgb(hexstr):
    h = hexstr.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def to_hex(rgb):
    return "#" + "".join("%02X" % max(0, min(255, int(round(c * 255)))) for c in rgb)


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _delin(c):
    return c * 12.92 if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def luminance(hexstr):
    r, g, b = (_lin(c) for c in to_rgb(hexstr))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg):
    """WCAG contrast ratio. 4.5 for text, 3.0 for marks."""
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def darken(hexstr, step=0.08):
    r, g, b = to_rgb(hexstr)
    return to_hex(tuple(max(0.0, c - step) for c in (r, g, b)))


def fit_text(hexstr, bg="#FFFFFF", target=4.5, limit=12):
    """Darken a brand colour until it carries text, keeping the hue."""
    out = hexstr
    for _ in range(limit):
        if contrast(out, bg) >= target:
            return out
        out = darken(out)
    return INK


def readable_on(hexstr):
    """White or ink, whichever actually passes on this background."""
    return "#FFFFFF" if contrast("#FFFFFF", hexstr) >= 4.5 else INK


# ------------------------------------------------------------------ Lab, dE --

def _to_lab(hexstr):
    r, g, b = (_lin(c) for c in to_rgb(hexstr))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b)
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else (7.787 * t) + (16 / 116)

    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e(a, b):
    """CIE76. Adjacent chart series want 15 or more under normal vision."""
    la, aa, ba = _to_lab(a)
    lb, ab, bb = _to_lab(b)
    return math.sqrt((la - lb) ** 2 + (aa - ab) ** 2 + (ba - bb) ** 2)


# Vienot 1999, validated for protan and deutan only.
_LMS = ((17.8824, 43.5161, 4.11935),
        (3.45565, 27.1554, 3.86714),
        (0.0299566, 0.184309, 1.46709))
_LMS_INV = ((0.0809444479, -0.130504409, 0.116721066),
            (-0.0102485335, 0.0540193266, -0.113614708),
            (-0.000365296938, -0.00412161469, 0.693511405))
_SIM = {
    "prot": ((0.0, 2.02344, -2.52581), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    "deut": ((1.0, 0.0, 0.0), (0.494207, 0.0, 1.24827), (0.0, 0.0, 1.0)),
}


def _mul(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def simulate(hexstr, kind):
    if kind == "trit":
        raise ValueError(
            "The tritanopia simulation in this family of scripts is broken: the "
            "Vienot inverse is validated for protan and deutan only and returns "
            "a meaningless distance for tritan. Check prot and deut, and treat "
            "any tritanopia figure quoted in an older node as unverified.")
    if kind not in _SIM:
        raise ValueError("kind must be 'prot' or 'deut'")
    lin = tuple(_lin(c) for c in to_rgb(hexstr))
    lms = _mul(_LMS, lin)
    sim = _mul(_SIM[kind], lms)
    back = _mul(_LMS_INV, sim)
    return to_hex(tuple(_delin(max(0.0, min(1.0, c))) for c in back))


def cvd_delta_e(a, b, kind):
    """Separation between two colours under a colour-vision deficiency. Want 8+."""
    return delta_e(simulate(a, kind), simulate(b, kind))


# ------------------------------------------------------------------ palette --

class Palette(object):
    """One company's colours, with each use already checked.

    brand   the pure hue. Large fills and thick keylines only.
    chrome  the header bar. Pure brand where white passes on it, darkened where not.
    text    brand darkened until it carries body text on white.
    mark    brand darkened until it passes 3:1, for thin rules and small fills.
    """

    def __init__(self, brand, source="", accent=None):
        self.brand = brand.upper()
        self.source = source
        self.chrome = self.brand if contrast("#FFFFFF", self.brand) >= 4.5 \
            else fit_text(self.brand, "#FFFFFF", 4.5)
        self.on_chrome = readable_on(self.chrome)
        self.text = fit_text(self.brand, "#FFFFFF", 4.5)
        self.mark = fit_text(self.brand, "#FFFFFF", 3.0)
        self.accent = (accent or NEUTRAL_SERIES[0]).upper()
        self.ink, self.grey, self.rule, self.pale = INK, GREY, RULE, PALE
        self.pos, self.neg = POS, NEG

    def series(self, n):
        """n categorical chart colours. The brand hue takes slot one.

        A candidate has to clear every colour already chosen, at 15 under normal
        vision and 8 under both simulated deficiencies. A brand with too few
        chart-safe hues gets fewer series rather than borrowed colour, so this
        returns a short list rather than padding it with near-duplicates.
        """
        out = [self.mark]
        for c in NEUTRAL_SERIES:
            if len(out) >= n:
                break
            if all(delta_e(c, p) >= 15
                   and cvd_delta_e(c, p, "deut") >= 8
                   and cvd_delta_e(c, p, "prot") >= 8 for p in out):
                out.append(c)
        return out[:n]

    def report(self):
        """Every check, as rows for the run file. Print this, don't guess."""
        rows = [("brand", self.brand, "large fills and thick keylines only", ""),
                ("chrome", self.chrome, "header bar",
                 "white on it %.2f:1" % contrast("#FFFFFF", self.chrome)),
                ("text", self.text, "body text and headings",
                 "%.2f:1 on white" % contrast(self.text, "#FFFFFF")),
                ("mark", self.mark, "chart marks and thin rules",
                 "%.2f:1 on white" % contrast(self.mark, "#FFFFFF"))]
        pal = self.series(4)
        for i in range(len(pal) - 1):
            rows.append(("series %d vs %d" % (i + 1, i + 2),
                         "%s / %s" % (pal[i], pal[i + 1]), "adjacent separation",
                         "dE %.1f normal, %.1f deut, %.1f prot"
                         % (delta_e(pal[i], pal[i + 1]),
                            cvd_delta_e(pal[i], pal[i + 1], "deut"),
                            cvd_delta_e(pal[i], pal[i + 1], "prot"))))
        return rows


DEFAULT = Palette("#1F3A5F", source="Method 2 fallback, used when no brand "
                                   "palette was resolved for the company")
