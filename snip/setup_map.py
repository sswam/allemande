    def set_up(self, services: dict[str, Any]) -> bool:
        """Set up an agent"""

        agent_type = self.get("type")
        if agent_type in ["human", "visual"]:
            return False

        service = services.get(agent_type)

        if service is None:
            raise ValueError(f'Unknown service for agent: {self["name"]}, {agent_type}')

        self.update(service)

        if SAFE and not self.get("safe", True):
            return False

        if not ADULT and self.get("adult"):
            return False

        self.data = safety.apply_or_remove_adult_options(self.data, ADULT)

#        self.setup_maps()

        return True

    def setup_maps(self):
        """Setup maps for an agent"""
        data = self.data
        for k in "input_map", "output_map", "map", "map_cs", "input_map_cs", "output_map_cs":
            if k not in data:
                data[k] = {}
        for k, v in data["input_map"].items():
            k_lc = k.lower()
            if k == k_lc:
                continue
            del data["input_map"][k]
            data["input_map"][k_lc] = v
        for k, v in data["output_map"].items():
            k_lc = k.lower()
            if k == k_lc:
                continue
            del data["output_map"][k]
            data["output_map"][k_lc] = v
        for k, v in data["map"].items():
            k_lc = k.lower()
            v_lc = v.lower()
            if k_lc not in data["input_map"]:
                data["input_map"][k_lc] = v
            if v_lc not in data["output_map"]:
                data["output_map"][v_lc] = k
        for k, v in data["map_cs"].items():
            if k not in data["input_map_cs"]:
                data["input_map_cs"][k] = v
            if v not in data["output_map_cs"]:
                data["output_map_cs"][v] = k


def apply_maps(mapping, mapping_cs, context):
    """for each word in the mapping, replace it with the value"""

    logger.debug("apply_maps: %r %r", mapping, mapping_cs)

    if not (mapping or mapping_cs):
        return

    def map_word(match):
        """Map a word."""
        word = match.group(1)
        word_lc = word.lower()
        out = mapping_cs.get(word)
        if out is None:
            out = mapping.get(word_lc)
        if out is None:
            out = word
        return out

    for i, msg in enumerate(context):
        old = msg
        context[i] = re.sub(r"\b(.+?)\b", map_word, msg)
        if context[i] != old:
            logger.debug("map: %r -> %r", old, context[i])


    # put remote_messages[-1] through the input_maps
    # chat.apply_maps(agent["input_map"], agent["input_map_cs"], context2)

    # chat.apply_maps(agent["output_map"], agent["output_map_cs"], box)

    # put remote_messages[-1] through the input_maps
    # chat.apply_maps(agent["input_map"], agent["input_map_cs"], context)

    # chat.apply_maps(agent["output_map"], agent["output_map_cs"], [response])
