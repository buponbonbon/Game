"""Walkable garden workyard: crop beds are scenery, never menu rectangles."""

PLOTS = [
    dict(
        id="bed-" + str(i),
        index=i,
        x=144 + (i % 3) * 75,
        y=128 + (i // 3) * 41,
        approach=dict(x=144 + (i % 3) * 75 + 32, y=128 + (i // 3) * 41 + 16),
    )
    for i in range(9)
]
GARDEN = dict(
    width=512,
    height=288,
    spawn=dict(x=368, y=225),
    cell=8,
    speed=42,
    zoom=1.3,
    bounds=dict(left=55, right=455, top=101, bottom=250),
    walkways=[[[58, 103], [451, 103], [451, 247], [58, 247]]],
    blockers=[dict(x=p["x"] - 27, y=p["y"] - 13, w=54, h=24) for p in PLOTS],
    facilities=[
        dict(id=p["id"], x=p["approach"]["x"], y=p["approach"]["y"], plot=p["index"])
        for p in PLOTS
    ],
    plots=PLOTS,
)
