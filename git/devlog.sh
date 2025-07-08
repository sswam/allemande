#!/usr/bin/env bash

# [n] [reference files ...]
# Generate retrospective devlog from git history

devlog() {
    local weeks=1 w=1          # number of weeks to process
    local model= m=flasho      # LLM model for summaries
    local refs=() r=()         # reference files for style/context
    local patches= p=1         # include patch details
    local default_ref= d=1     # use the previous devlog as a reference
    local max_patches=20000    # max size of all patches to send to AI
    local max_patch=5000       # max size of one patch to send to AI

    eval "$(ally)"

    set +o pipefail

    # Find most recent existing log
    local last_log_date=
    local newest_log
    newest_log=$(find . -maxdepth 1 -type f -name "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md" -printf "%f\n" 2>/dev/null | sort -r | head -1)
    if [ -n "$newest_log" ]; then
        last_log_date=$(date -d "${newest_log%.md}" +%Y-%m-%d)
        if [ "$default_ref" -eq 1 ]; then
            refs+=("$newest_log")
        fi
    fi

    # Get start date for processing (monday after last log, or earliest commits)
    local start_date
    if [ -n "$last_log_date" ]; then
        start_date=$(date -d "$last_log_date + 1 week" "+%Y-%m-%d")
    else
        start_date=$(git log --reverse --format=%cd --date=short | head -1)
        start_date=$(date -d "$start_date -$(date -d "$start_date" +%u) days + 1 day" +%Y-%m-%d)
    fi

    # End date is last sunday
    local end_date
    end_date=$(date -d "last sunday" +%Y-%m-%d)

    # Process each week
    local week_start="$start_date"
    local week_count=0

    while [ "$week_start" \< "$end_date" ] && [ "$week_count" -lt "$weeks" ]; do
        local week_end
        week_end=$(date -d "$week_start + 6 days" +%Y-%m-%d)

        # Get commits for this week
        local commits
        commits=$(git log --reverse --since="$week_start" --until="$week_end 23:59:59" --format="%h %s")

        if [ -n "$commits" ]; then
            generate_log "$week_start" "$week_end" "$commits" "$model" "$patches" "${refs[@]}"
            week_count=$((week_count + 1))
        fi

        week_start=$(date -d "$week_start + 7 days" +%Y-%m-%d)
    done

    if [ "$week_count" == 0 ]; then
        exit 1
    fi
}

generate_log() {
    local week_start=$1
    local week_end=$2
    local commits=$3
    local model=$4
    local patches=$5
    shift 5
    local refs=("$@")

    local outfile="${week_start}.md"
    local ref_content=""
    local patch_content=""
    local git_root=$(git rev-parse --show-toplevel)

    # Load reference content if provided
    if [ "${#refs[@]}" -gt 0 ]; then
        for ref in "${refs[@]}"; do
            ref_content+=$'\n'"$(cat "$ref")"
        done
    fi

    time_off_prompt=""
    if [ "$default_ref" = 1 ]; then
        time_off_prompt="If the dev took some time off since the previous working week, like one or more whole weeks, note that and approx. how much! "
    fi

    prompt="Please generate a devlog entry for week of $week_start to $week_end.
${time_off_prompt}

Commits:
$commits

Reference content:
$ref_content

Start with bullet point summary of main achievements, then elaborate on each point. Use a natural voice. For the love of Cthulhu, do NOT invent anything that isn't evident in the code and commit logs! The other references are only for style and background information.

** Do NOT refer to individual commits, especially NO COMMIT HASHES! :)"

    # Generate summary and details using AI
    {
        if [ "$patches" = 1 ]; then
            printf "Patches:\n"
            # Get list of files changed in the date range
            files=$(git log --reverse --since="$week_start" --until="$week_end 23:59:59" --name-only --pretty=format: | sort -u)

            while IFS= read -r file; do
                [ -z "$file" ] && continue

                # Get patches for this file
                patch_content=$(i "$git_root" git log --reverse --since="$week_start" --until="$week_end 23:59:59" --patch -- "$file")

                if [ -n "$patch_content" ]; then
                    printf "\nFile: %s\n" "$file"
                    if [ ${#patch_content} -le "$max_patch" ]; then
                        printf "%s\n" "$patch_content"
                    else
                        # Take first max_patch bytes and remove incomplete last line
                        truncated=$(printf "%s" "$patch_content" | head -c "$max_patch")
                        printf "%s\n" "$(printf "%s" "$truncated" | sed '$d')"
                        printf "... (truncated)\n"
                    fi
                fi
            done <<< "$files"
        fi
    } | tr -dc ' \t\n -~' | tee /dev/stderr |
    process -m="$model" "$prompt" | tee /dev/stderr > "$outfile"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    devlog "$@"
fi

# version: 0.1.3

# <think>
# Key requirements:
# 1. Process git log by weeks (Mon-Sun)
# 2. Generate markdown devlog for n earliest weeks (default 1)
# 3. Skip partial current week
# 4. Look from after last existing log
# 5. Include commit details and summary
# 6. Save as YYYY-MM-DD.md (Monday's date)
#
# Design approach:
# 1. Find last log date
# 2. Get git log since then
# 3. Group by week
# 4. Generate markdown with summary and details
# 5. Save to dated file
# </think>

# This script:
# 1. Finds the most recent existing log file
# 2. Determines the start date (Monday after last log or first commit)
# 3. Processes weeks until last Sunday or requested number reached
# 4. For each week with commits:
#             - Collects commit messages and optionally patches
#             - Uses reference files for style/context if provided
#             - Generates markdown log using AI
#             - Saves to YYYY-MM-DD.md
#
# The AI prompt asks for a natural voice summary followed by details, maintaining readability while being comprehensive.
