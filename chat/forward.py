import logging

import chat
import bb_lib
import conductor

logger = logging.getLogger(__name__)

async def handle_forwarding(run_agent, response, agent, agents, file, args, history,
                        history_start, mission, summary, config, responsible_human, room):
    """Handle forwarding logic for agent responses."""
    if not agent.get("forward"):
        return response

    logger.info("handle_forwarding: initial response: %s", response)

    response = apply_forward_triggers(response, agent)

    if not response:
        return None

    forward_target = determine_forward_target(response, agent, agents, config, room)

    if not forward_target:
        return response

    return await execute_forward(run_agent, forward_target, agent, agents, file, args, history, history_start, mission, summary, config, responsible_human)


def apply_forward_triggers(response, agent):
    """Apply automatic forwarding based on response content."""
    forward_if_blank = agent.get("forward_if_blank")
    if forward_if_blank and (not response or response == f"{agent.name}:"):
        logger.info("Forward: blank, Using forward_if_blank")
        return f"@{forward_if_blank}"

    has_forward = chat.has_at_mention(response)

    forward_if_code = agent.get("forward_if_code")
    if not has_forward and forward_if_code and "```" in response:
        logger.info("Forward: code, Using forward_if_code")
        return f"@{forward_if_code}"

    forward_if_image = agent.get("forward_if_image")
    if not has_forward and forward_if_image and "![" in response:
        logger.info("Forward: image, Using forward_if_image")
        return f"@{forward_if_image}"

    return response


def determine_forward_target(response, agent, agents, config, room):
    """Determine which agent to forward to."""
    # logger.info("Forward response: %r", response)
    response_message = list(bb_lib.lines_to_messages([response]))[-1]
    # logger.info("response_message: %r", response_message)

    _responsible_human, bots2 = conductor.who_should_respond(
        response_message, agents=agents, history=[response_message], default=[],
        include_humans_for_ai_message=False, include_humans_for_human_message=False,
        may_use_mediator=False, config=config, room=room, include_self=False,
        at_only=True, use_aggregates=False,
    )

    bots2 = [b for b in bots2 if b is not None]

    if chat.has_at_mention(response):
        bots2 = list(reversed(bots2)) + [a for a in agent.get("forward_if_denied", []) if room.check_access(a.lower()).value & chat.Access.READ_WRITE.value == chat.Access.READ_WRITE.value]

    logger.info("Forward: who should respond: %r", bots2)
    return get_allowed_forward_target(bots2, agent)


def get_allowed_forward_target(bots2, agent):
    """Get the first allowed forward target from candidates."""
    forward_allow = agent.get("forward_allow")
    forward_deny = agent.get("forward_deny")

    for bot2 in bots2:
        if is_forward_denied(bot2, forward_allow, forward_deny):
            continue

        if bot2 == agent.name:
            logger.info("Skipping forwarding to self: %s", bot2)
            continue

        return bot2

    return None


def is_forward_denied(bot, forward_allow, forward_deny):
    """Check if forwarding to bot is denied."""
    if isinstance(forward_allow, list) and bot not in forward_allow:
        logger.info("Forward: %s not allowed, using forward_if_denied", bot)
        logger.info("  forward_allow: %r", forward_allow)
        return True

    if isinstance(forward_deny, list) and bot in forward_deny:
        logger.info("Forward: %s denied, using forward_if_denied", bot)
        logger.info("  forward_deny: %r", forward_deny)
        return True

    return False


async def execute_forward(run_agent, bot2, agent, agents, file, args, history,
                        history_start, mission, summary, config, responsible_human):
    """Execute forwarding to another agent."""
    logger.info("Forwarding from %s to %s", agent.name, bot2)
    forward_keep_prompts = agent.get("forward_keep_prompts")
    agent2 = agents.get(bot2).apply_identity(agent, keep_prompts=forward_keep_prompts, no_over=True)
    # logger.info("Forward agent: %r", agent2)

    query = history[-1] if history else ""
    response = await run_agent(
        agent2, query, file, args, history, history_start=history_start,
        mission=mission, summary=summary, config=config,
        agents=agents, responsible_human=responsible_human
    )

    if response is None:
        return None

    return response.lstrip().rstrip("\n ")
