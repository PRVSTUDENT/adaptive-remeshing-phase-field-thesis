#!/usr/bin/env bash
set -Eeuo pipefail

# Ensure ~/bin exists
mkdir -p "$HOME/bin"

# 1. Guarded grep wrapper
cat << 'EOF' > "$HOME/bin/grep"
#!/usr/bin/env bash
# Guarded grep wrapper on Freiberg cluster login node (mlogin01)
# Enforces 120s timeout and excludes heavy binary simulation outputs (.odb, .sim, etc.)
ARGS=()
HAS_R=0
for arg in "$@"; do
    if [[ "$arg" =~ ^-[a-zA-Z]*[rR] ]]; then
        HAS_R=1
    fi
    ARGS+=("$arg")
done
if [[ "$HAS_R" -eq 1 ]]; then
    exec /usr/bin/timeout --preserve-status 120s /usr/bin/grep \
        --binary-files=without-match \
        --exclude='*.odb' --exclude='*.sim' --exclude='*.res' \
        --exclude='*.pac' --exclude='*.abq' --exclude='*.sel' \
        --exclude='*.dat' --exclude='*.prt' --exclude='*.msg' \
        --exclude-dir='.git' --exclude-dir='runs' --exclude-dir='results' \
        "${ARGS[@]}"
else
    exec /usr/bin/timeout --preserve-status 120s /usr/bin/grep "${ARGS[@]}"
fi
EOF
chmod +x "$HOME/bin/grep"

# 2. Guarded find wrapper
cat << 'EOF' > "$HOME/bin/find"
#!/usr/bin/env bash
# Guarded find wrapper on Freiberg cluster login node (mlogin01)
# Enforces 120s timeout and warns/blocks whole-tree sha256sum
CMD_STR="$*"
if [[ "$CMD_STR" =~ -exec\ +sha256sum ]] && [[ "$CMD_STR" =~ (adaptive-remeshing|\.|~|\/home\/pr21vyci) ]]; then
    echo "GUARD_BLOCKED: Whole-tree find with sha256sum over cluster storage (1.3 TB) is prohibited." >&2
    exit 70
fi
exec /usr/bin/timeout --preserve-status 120s /usr/bin/find "$@"
EOF
chmod +x "$HOME/bin/find"

# 3. Guarded sha256sum wrapper
cat << 'EOF' > "$HOME/bin/sha256sum"
#!/usr/bin/env bash
# Guarded sha256sum wrapper on Freiberg cluster login node (mlogin01)
exec /usr/bin/timeout --preserve-status 120s /usr/bin/sha256sum "$@"
EOF
chmod +x "$HOME/bin/sha256sum"

echo "CLUSTER_LOGIN_GUARDS_INSTALLED_SUCCESSFULLY"
