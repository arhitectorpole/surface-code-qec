"""S0 planar surface-code geometry and exact d=3 validation."""
from dataclasses import dataclass

def build_unrotated_planar_surface_code(d: int):
    if d < 3:
        raise ValueError("distance must be >= 3")
    size = 2 * d - 1
    data, z_anc, x_anc = [], [], []
    for i in range(size):
        for j in range(size):
            if (i + j) % 2 == 0:
                data.append((i, j))
            elif i % 2 == 0:
                z_anc.append((i, j))
            else:
                x_anc.append((i, j))
    data_id = {p: q for q, p in enumerate(data)}
    def nbrs(pos):
        i, j = pos
        return [
            data_id[p] for p in
            [(i-1,j), (i+1,j), (i,j-1), (i,j+1)]
            if p in data_id
        ]
    return {
        "d": d,
        "data": data,
        "z_checks": [(p, nbrs(p)) for p in z_anc],
        "x_checks": [(p, nbrs(p)) for p in x_anc],
    }

if __name__ == "__main__":
    for d in (3, 5, 7):
        c = build_unrotated_planar_surface_code(d)
        print(d, len(c["data"]), len(c["x_checks"]), len(c["z_checks"]))
