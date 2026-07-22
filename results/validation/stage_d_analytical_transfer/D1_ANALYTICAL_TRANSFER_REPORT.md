# Stage D1 analytical transfer results

Classification: `stage_d1_analytical_transfer_pass`

## Nodal phase field

- L2 error: `0.02703721036584061`
- Max abs error: `0.084997257868485`
- Bounded range: `0.20171412208939118..0.6915240592024321`

## Integration-point history field

- L2 error: `0.010797382113372963`
- Max abs error: `0.02339821172158782`
- Bounded range: `0.08867564690683752..0.23508477175745984`

## Energy

- Source exact: `0.32717045063020667`
- Target bounded transfer: `0.3219475731265888`
- Target exact: `0.329640902111744`
- Bounded minus exact: `-0.0076933289851552344`

## Gates

- `PASS` all_target_nodes_mapped
- `PASS` all_target_ips_mapped
- `PASS` finite_raw_d
- `PASS` finite_raw_H
- `PASS` bounded_d_in_unit_interval
- `PASS` H_no_healing
- `PASS` deterministic_transfer
- `PASS` element_ip_ordering_verified
- `PASS` errors_reported
- `PASS` energy_jump_reported
