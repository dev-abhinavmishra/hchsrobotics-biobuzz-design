#!/usr/bin/env bash
# CI gate runner: execute every scripts/freecad/selfcheck_overhaul*.py under
# freecadcmd, keep full console output in logs/ci/, and exit non-zero if any
# gate script fails. FreeCAD progress chatter is filtered from the console.
set -u
cd "$(dirname "$0")/../.."
mkdir -p logs/ci

fail=0
ran=0
failed_gates=()
for f in scripts/freecad/selfcheck_overhaul*.py; do
    [ -f "$f" ] || { echo "ERROR: no selfcheck_overhaul*.py scripts found"; exit 1; }
    ran=$((ran + 1))
    name="$(basename "$f" .py)"
    log="logs/ci/${name}.console.log"
    echo "=================== $f ==================="
    freecadcmd "$f" > "$log" 2>&1
    rc=$?
    # Surface the gate table (PASS/FAIL lines + SELFCHECK verdict) on stdout;
    # drop FreeCAD recompute/progress noise.
    grep -vE '^\s*$|\([0-9]+ %\)|go out of the allowed scope|no suitable edges for chamfer|Recompute\.\.\.|Statistics on Transfer|Transfer Mode|Transferring Shape|WorkSession|Step File Name|\*{3,}|Importing project files|Postprocessing' "$log"
    if [ "$rc" -eq 0 ]; then
        echo ">>> $name: PASS (log: $log)"
    else
        echo ">>> $name: FAIL (exit $rc, log: $log)"
        failed_gates+=("$name")
        fail=1
    fi
done
echo "=================== $ran gate script(s) run ==================="
if [ "$fail" -ne 0 ]; then
    echo "CI SELFCHECK: FAIL"
else
    echo "CI SELFCHECK: PASS"
fi

# Report results as job summary + error annotations, then exit non-zero so a
# failing gate fails the check.
if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
    {
        echo "### Selfcheck gates"
        echo
        if [ "${#failed_gates[@]}" -eq 0 ]; then
            echo "All $ran gate(s) PASS"
        else
            for g in "${failed_gates[@]}"; do echo "- \`$g\` FAIL"; done
        fi
        echo
        echo "Full console output: run artifact -> logs/ci/"
    } >> "$GITHUB_STEP_SUMMARY"
    for g in "${failed_gates[@]}"; do
        echo "::error title=selfcheck::$g gate reported FAIL"
    done
fi
exit "$fail"
