ac -k -o ~/rooms/ally_chat_cli/summary.yml -d sam -a Ally "can you summarize what you'd like to remember from this please, including all the main people and things, but not including your self-talk or any pictures or @mentions? Just give the summary only with no prelude, in one paragraph of first person prose, from your point of view." ~/rooms/sam/ally.bb

# also check old tool "remember":
# grep -R -l '^Claude:' sam/ | xa remember -p=8 -u=Claude
