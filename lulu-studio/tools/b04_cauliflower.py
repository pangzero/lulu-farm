"""B04 cauliflower: a fused curd with broad florets and upright clasping leaves.

Only geometry authoring lives here.  The batch driver owns saving, exporting,
review cameras and revision protection.  No B01 code is imported or executed.
"""
from math import sin, cos, pi, sqrt, exp, acos
from mathutils import Vector
from b04_common import mesh, leaf, sphere, tube, mat, linear, mix


def _direction(polar, azimuth):
    return Vector((sin(polar) * cos(azimuth),
                   sin(polar) * sin(azimuth), cos(polar)))


def _curd_surface(material):
    """One watertight surface, with unequal fused florets rather than balls.

    Two scales of smooth, local displacement produce large readable crowns and
    round, clearly raised lobules on each crown.  All lobes share the shoulder
    and underside; there are no detached sphere seams or dark interstices.
    """
    major_specs = [
        # polar, azimuth, angular width, relief: deliberately unequal crowns.
        (.10, .45, .38, .059),
        (.68, -.55, .34, .053),
        (.76, .75, .37, .049),
        (.70, 2.10, .33, .061),
        (.82, 3.40, .38, .050),
        (.72, 4.75, .34, .056),
        (1.35, .10, .34, .044),
        (1.40, 1.94, .38, .047),
        (1.34, 3.47, .35, .049),
        (1.43, 4.92, .35, .043),
    ]
    crowns = [(_direction(p, a), w, h) for p, a, w, h in major_specs]
    # Local lobules cover each large floret, with visibly round 0.05-0.09-unit
    # flower clusters.  Tangent-space placement avoids collapsing every lobule
    # together at the pole.  Different counts/radii prevent a regular bead grid.
    small = []
    for k, (p, a, w, h) in enumerate(major_specs):
        normal = _direction(p, a)
        ref = Vector((1, 0, 0)) if normal.z > .88 else Vector((0, 0, 1))
        tangent = ref.cross(normal).normalized()
        bitangent = normal.cross(tangent).normalized()
        count = 3 + (k % 3)
        for q in range(count):
            if q == 0:
                normal_q = normal
                height = .022 + .003 * sin(k * 1.3)
            else:
                around = 2 * pi * (q - 1) / (count - 1) + k * 1.941
                offset = .196 + .026 * sin(k * 4.2 + q * 2.4)
                normal_q = (normal * cos(offset)
                            + (tangent * cos(around) + bitangent * sin(around))
                            * sin(offset))
                height = .027 + .006 * (1 + sin(k * 2.1 + q)) / 2
            small.append((normal_q,
                          .126 + .031 * (1 + sin(k * 2.3 + q * 1.7)) / 2,
                          height))

    # A smaller fused foundation leaves room for actual relief while keeping
    # the original approximate 0.62 height and the surrounding leaf silhouette.
    center = Vector((-.010, .006, .353))
    scales = Vector((.281, .273, .178))
    cream = linear('#EFE9CD')
    light = linear('#FFF7DF')
    shade = linear('#DAD6B5')

    def sample(polar, azimuth):
        d = _direction(polar, azimuth)
        relief = 0.0
        broad = 0.0
        for normal, width, height in crowns:
            angular = acos(max(-1.0, min(1.0, d.dot(normal))))
            bump = exp(-1.8 * (angular / width) ** 2)
            broad += height * bump
        for normal, width, height in small:
            angular = acos(max(-1.0, min(1.0, d.dot(normal))))
            relief += height * exp(-1.8 * (angular / width) ** 2)
        # The underside is a calm tapered shoulder into the plant's short core.
        # It is intentionally the same closed mesh as the upper florets.
        lower_taper = 1.0 - .10 * max(0.0, -d.z) ** 2
        p = center + Vector((d.x * scales.x * lower_taper,
                             d.y * scales.y * lower_taper,
                             d.z * scales.z))
        p += d * (broad + relief)
        t = max(0.0, min(1.0, .43 + .20 * d.z
                         + .16 * min(1.0, broad / .065)
                         + .12 * min(1.0, relief / .035)))
        c = mix(shade, mix(cream, light, .58), t)
        return p, c

    n, rings = 160, 88
    vs, colors, fs = [], [], []
    p, c = sample(0.0, 0.0)
    vs.append(p)
    colors.append(c)
    for i in range(1, rings):
        polar = pi * i / rings
        for j in range(n):
            p, c = sample(polar, 2 * pi * j / n)
            vs.append(p)
            colors.append(c)
    bottom = len(vs)
    p, c = sample(pi, 0.0)
    vs.append(p)
    colors.append(c)
    for j in range(n):
        nj = (j + 1) % n
        fs.append((0, 1 + j, 1 + nj))
        base = 1 + (rings - 2) * n
        fs.append((bottom, base + nj, base + j))
    for i in range(rings - 2):
        for j in range(n):
            a = 1 + i * n + j
            b = 1 + i * n + (j + 1) % n
            fs.append((a, a + n, b + n, b))
    return mesh('Cauliflower fused curd - unequal broad florets', vs, fs,
                material, colors)


def build_cauliflower():
    curd = mat('Cauliflower warm ivory curd', '#F0EBD1', .86, paint=True)
    stalk = mat('Cauliflower short green core', '#70A34A', .83)
    _curd_surface(curd)
    sphere('Cauliflower grounded short core', (0, 0, .065),
           (.061, .057, .065), stalk, 28, 18)

    # The few broad, upright clasp leaves cradle the curd.  Unlike cabbage,
    # these do not form a closed leafy ball or cross over its crown.
    # Front leaves are low so the yellow-white flower structure stays readable.
    leaf_specs = [
        # angle, outer reach, rise, late inward turn, blade half width
        (-1.61, .47, .275, .025, .184),
        (-.72, .46, .335, .036, .198),
        (.21, .455, .425, .065, .187),
        (1.13, .45, .475, .092, .192),
        (2.04, .45, .465, .086, .182),
        (2.95, .465, .395, .056, .200),
        (3.85, .465, .315, .030, .184),
    ]
    for index, (angle, reach, rise, turn, width) in enumerate(leaf_specs):
        d = Vector((cos(angle), sin(angle), 0))
        side = Vector((-sin(angle), cos(angle), 0))

        def point(t, u, d=d, side=side, reach=reach, rise=rise,
                  turn=turn, width=width, index=index):
            env = sin(pi * t) ** .66
            # A broad spoon shoulder, then a slight return toward the curd.
            r = .029 + reach * (1.0 - exp(-3.1 * t)) - turn * t ** 4
            # Small off-axis drift makes seven individual leaves, not a rosette
            # of mechanically repeated petals.
            drift = .014 * sin(pi * t) * sin(index * 1.8)
            # Three very broad margin waves, not the frill of lettuce.
            margin = 1.0 + .043 * sin(3.0 * pi * t + index * .8) * abs(u) ** 4
            p = d * (r - .070 * u * u * env)
            p += side * (u * width * env * margin + drift)
            ridge = .013 * exp(-(u / .17) ** 2) * sin(pi * t)
            p.z = (.032 + rise * t + .043 * sin(pi * t)
                   + .047 * u * u * env + ridge
                   + .0065 * sin(t * 8.0 + index + u * 2.1)
                   * abs(u) ** 4 * env)
            return p

        leaf('Cauliflower clasping broad ribbed leaf %02d' % (index + 1),
             point, ('#327D3B', '#76AD51', '#BAD18B'),
             thick=.018, nu=30, nv=22, veins=True)

