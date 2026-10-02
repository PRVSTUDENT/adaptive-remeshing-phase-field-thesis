$xmin = -0.5
$xmax = 0.5
$ymin = -0.5
$ymax = 0.5
$nx = 80
$ny = 80

$dx = ($xmax - $xmin) / $nx
$dy = ($ymax - $ymin) / $ny

$rp_node_id = 99999
$rp_coord = "0.00000000,     0.50000000"

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("*HEADING")
$lines.Add("M2_PURE_NONMATCHING_TARGET_BENCHMARK_NMA (80x80 Uniform Quads, h=0.0125mm)")
$lines.Add("*NODE")

$node_grid = @{}
$node_id = 1

for ($j = 0; $j -le $ny; $j++) {
    $y = $ymin + $j * $dy
    for ($i = 0; $i -le $nx; $i++) {
        $x = $xmin + $i * $dx
        $lines.Add(("{0,8:D}, {1,14:F8}, {2,14:F8}" -f $node_id, $x, $y))
        $node_grid["$i,$j"] = $node_id
        $node_id++
    }
}
$lines.Add(("{0,8:D}, {1}" -f $rp_node_id, $rp_coord))

$n_phys = $nx * $ny
$lines.Add("*ELEMENT, TYPE=U1, ELSET=PHASE_QUADS")
$elem_id = 1
for ($j = 0; $j -lt $ny; $j++) {
    for ($i = 0; $i -lt $nx; $i++) {
        $n1 = $node_grid["$i,$j"]
        $n2 = $node_grid["$($i+1),$j"]
        $n3 = $node_grid["$($i+1),$($j+1)"]
        $n4 = $node_grid["$i,$($j+1)"]
        $lines.Add(("{0,8:D}, {1,8:D}, {2,8:D}, {3,8:D}, {4,8:D}" -f $elem_id, $n1, $n2, $n3, $n4))
        $elem_id++
    }
}

$lines.Add("*ELEMENT, TYPE=U2, ELSET=MECH_QUADS")
$elem_id = 1
for ($j = 0; $j -lt $ny; $j++) {
    for ($i = 0; $i -lt $nx; $i++) {
        $n1 = $node_grid["$i,$j"]
        $n2 = $node_grid["$($i+1),$j"]
        $n3 = $node_grid["$($i+1),$($j+1)"]
        $n4 = $node_grid["$i,$($j+1)"]
        $eid2 = $elem_id + $n_phys
        $lines.Add(("{0,8:D}, {1,8:D}, {2,8:D}, {3,8:D}, {4,8:D}" -f $eid2, $n1, $n2, $n3, $n4))
        $elem_id++
    }
}

$lines.Add("*ELSET, ELSET=ALL_ELEMENTS")
$lines.Add("PHASE_QUADS, MECH_QUADS")

# Node sets
$bot_nodes = [System.Collections.Generic.List[int]]::new()
$top_nodes = [System.Collections.Generic.List[int]]::new()
$left_nodes = [System.Collections.Generic.List[int]]::new()
$right_nodes = [System.Collections.Generic.List[int]]::new()

for ($i = 0; $i -le $nx; $i++) {
    $bot_nodes.Add($node_grid["$i,0"])
    $top_nodes.Add($node_grid["$i,$ny"])
}
for ($j = 0; $j -le $ny; $j++) {
    $left_nodes.Add($node_grid["0,$j"])
    $right_nodes.Add($node_grid["$nx,$j"])
}

function Write-NSet($name, $nlist) {
    $lines.Add("*NSET, NSET=$name")
    for ($k = 0; $k -lt $nlist.Count; $k += 16) {
        $count = [Math]::Min(16, $nlist.Count - $k)
        $chunk = $nlist.GetRange($k, $count)
        $lines.Add(($chunk -join ", "))
    }
}

Write-NSet "BOT_NODES" $bot_nodes
Write-NSet "TOP_NODES" $top_nodes
Write-NSet "LEFT_NODES" $left_nodes
Write-NSet "RIGHT_NODES" $right_nodes
$lines.Add("*NSET, NSET=RP_NODE")
$lines.Add("$rp_node_id")

$lines.Add("*EQUATION")
foreach ($tn in $top_nodes) {
    $lines.Add("2")
    $lines.Add(("{0}, 1, 1.0, {1}, 1, -1.0" -f $tn, $rp_node_id))
}

$outPath = "D:\Master thesis\Adaptive remeshing\models\generated\mode_ii\benchmark_mesh_candidates\M2_PURE_NONMATCHING_TARGET_NMA_80x80.inp"
$parentDir = [System.IO.Path]::GetDirectoryName($outPath)
if (!(Test-Path $parentDir)) { New-Item -ItemType Directory -Path $parentDir -Force }

[System.IO.File]::WriteAllLines($outPath, $lines, [System.Text.Encoding]::ASCII)
$h = (Get-FileHash -Path $outPath -Algorithm SHA256).Hash.ToLower()
Write-Output "Generated: $outPath"
Write-Output "SHA256: $h"
