function ConvertFrom-AgyEnvelope {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Text)
    # Read complete objects rather than feeding diagnostic suffixes to the JSON parser.
    $depth = 0; $start = -1; $inString = $false; $escaped = $false
    $found = $null
    for ($i = 0; $i -lt $Text.Length; $i++) {
        $c = $Text[$i]
        if ($depth -eq 0) {
            if ($c -eq '{') { $start = $i; $depth = 1; $inString = $false; $escaped = $false }
            continue
        }
        if ($inString) {
            if ($escaped) { $escaped = $false }
            elseif ($c -eq '\') { $escaped = $true }
            elseif ($c -eq '"') { $inString = $false }
            continue
        }
        if ($c -eq '"') { $inString = $true }
        elseif ($c -eq '{') { $depth++ }
        elseif ($c -eq '}') {
            $depth--
            if ($depth -eq 0) {
                try {
                    $candidate = $Text.Substring($start, $i - $start + 1) | ConvertFrom-Json -ErrorAction Stop
                    if ($candidate.PSObject.Properties['status'] -and
                        $candidate.PSObject.Properties['conversation_id'] -and
                        ($candidate.PSObject.Properties['response'] -or $candidate.PSObject.Properties['error'])) {
                        $found = $candidate
                    }
                } catch { } # Ignore unrelated complete diagnostic objects.
            }
        }
    }
    if ($null -eq $found) { throw 'No complete AGY result envelope found; preserve raw output for recovery.' }
    return $found
}
