from odbAccess import openOdb
import csv

odb_path = "M1_CANDIDATE_DONOR_H0025.odb"
odb = openOdb(odb_path, readOnly=True)
step = odb.steps["Step-1"]

for frame_idx, inc_num in [(22, 110), (23, 115)]:
    f = step.frames[frame_idx]
    t = float(f.frameValue)
    u_top = t * 0.005
    u_field = f.fieldOutputs["U"]
    rf_field = f.fieldOutputs["RF"]
    
    rf_dict = {}
    for v in rf_field.values:
        rf_dict[v.nodeLabel] = (float(v.data[0]), float(v.data[1]))
        
    out_file = "donor_h0025_frame%d_inc%d.csv" % (frame_idx, inc_num)
    with open(out_file, "w") as out:
        out.write("node_id,ux_mm,uy_mm,rf_x_kN,rf_y_kN\n")
        for v in u_field.values:
            nid = v.nodeLabel
            ux = float(v.data[0])
            uy = float(v.data[1])
            rfx, rfy = rf_dict.get(nid, (0.0, 0.0))
            out.write("%d,%.10e,%.10e,%.10e,%.10e\n" % (nid, ux, uy, rfx, rfy))
    print("Exported %s: time=%.6f, u_top=%.6f mm" % (out_file, t, u_top))

odb.close()
