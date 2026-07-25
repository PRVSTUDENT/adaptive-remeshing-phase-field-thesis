# Mode-II H0 benchmark definition freeze (F0.1)

## Geometry

- Domain: 1.0 mm x 1.0 mm rectangle.
- Left-edge notch length 0.5 mm at y = 0 (mid-height).
- Plane strain, thickness 1.0 mm.
- Mesh: Mode-I H0 supplementary structured mesh, ~0.005 mm local size,
  3930 physical UEL elements / 11790 layered elements / 3999 nodes.

## Material and fracture (Molnar)

- E = 210 kN/mm^2
- nu = 0.3
- Gc = 0.0027 kN/mm
- lc = 0.015 mm
- residual k = 1e-7 (U2); UMAT visualization constant 1e-11
- Phase-field convention: d = 0 intact, d = 1 fully broken

## Boundary conditions (pure shear, alpha = 0 deg)

- Bottom edge: U1 = U2 = 0
- Top edge: U2 = 0; U1 prescribed through equation coupling to RP
- RP DOF 1 amplitude schedule retained from Mode-I H0 technical envelope:
  0 -> 0.005 mm (Step-1), then to 0.010 mm (Step-2)
- Reaction evidence component: RF1; displacement component: U1

## Reference data

- RF-U: `reference_data_insufficient` for pure shear (Fig. 7 is tension).
- Crack path: qualitative curved/diagonal shear path (Fig. 6c).
- Path extraction threshold: provisional SDV15 >= 0.5

## Formulation boundary

Do not mix Msekh or Pandey formulations. Pandey is relevant only later for
MISESERI pre-refinement methodology after F1 baseline passes.
