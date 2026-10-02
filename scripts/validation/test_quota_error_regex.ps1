$sampleError = '{"conversation_id":"597756d7-e19b-4179-9cb1-ebe53a638d02","status":"ERROR","response":"","error":"Individual quota reached. Please upgrade your subscription to increase your limits. Resets in 50h17m57s.","duration_seconds":23.0394386,"num_turns":1,"usage":{"input_tokens":18692,"output_tokens":560,"thinking_tokens":455,"cache_read_tokens":0,"total_tokens":19252}}'

function Test-IsAgyQuotaLimitError {
    param([string]$Message)
    if ([string]::IsNullOrWhiteSpace($Message)) { return $false }
    return (
        $Message -match '(?i)HTTP\s*429' -or
        $Message -match '(?i)status\s*429' -or
        $Message -match '(?i)RESOURCE_EXHAUSTED' -or
        $Message -match '(?i)quota\s+(?:exceeded|exhausted|reached)' -or
        $Message -match '(?i)individual\s+quota' -or
        $Message -match '(?i)quota\s+limit' -or
        $Message -match '(?i)upgrade your subscription' -or
        $Message -match '(?i)rate.?limit(?:ed| exceeded)?' -or
        $Message -match '(?i)too many requests' -or
        $Message -match '(?i)usage\s+limit' -or
        $Message -match '(?i)plan.?limit'
    )
}

$matched = Test-IsAgyQuotaLimitError -Message $sampleError
Write-Host "Matched quota error: $matched"
if (-not $matched) {
    throw "Failed to match quota error string!"
}
