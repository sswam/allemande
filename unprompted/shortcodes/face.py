class Shortcode:
    def __init__(self, Unprompted):
        self.Unprompted = Unprompted
        self.description = "Generates an AI art prompt format for a person's face with their name, age, emotion, and clothes."

    def run_atomic(self, pargs, kwargs, context):
        if not pargs:
            return ""

        # Get the name from the first argument
        _name = self.Unprompted.parse_advanced(pargs[0], context)
        _clothes = self.Unprompted.parse_advanced(pargs[1], context) if len(pargs) > 1 else None
        _emo = self.Unprompted.parse_advanced(pargs[2], context) if len(pargs) > 2 else None
        _age = self.Unprompted.parse_advanced(pargs[3], context) if len(pargs) > 3 else None

        # "." means the default (load the file)
        # "-" means a global default
        # "" means nothing (of course)

        # clothes
        if _clothes is None or _clothes == ".":
            _clothes = f"""[use "clothes_upper/{_name},"]"""
        elif _clothes == "-":
            _clothes = "topless,"
        elif _clothes:
            _clothes += ","

        # expression / emotion
        if _emo is None or _emo == ".":
            _emo = f"""[use "emo/{_name},"]"""
        elif _emo == "-":
            _emo = "light smile,"
        elif _emo:
            _emo += ","

        # age
        if _age is None or _age == ".":
            _age = f"""[use "age/{_name}," 100 1.6]"""
        elif _age == "-":
            _age = f"(20 years old:1.6),"
        elif str(_age).isnumeric():
            _age = f"({_age} years old:1.6),"
        elif _age:
            _age = f"({_age}:1.6),"

        # "" means nothing

        name = _name
        if name.lower() == "barbie":
            name = "Barbarella"

        # Construct the prompt: name, age, person, emotion, clothes
        prompt = f"""
        (solo, portrait:1.5), (centered headshot, face close-up:1.8), (head and shoulders:1.5),
        raw, ultra realistic photograph, studio lighting, 85mm lens, (clean white background:1.5), professional headshot
        BREAK
        {name}, {_age} [use "{_name},"] {_emo} {_clothes}
        (face close-up:1.8)
        [set negative_prompt _append]
        (cropped:2), (full body:1.5), wide shot, tilted angle, low angle, high angle
        [/set]
        """

        # Process and return the constructed prompt
        return self.Unprompted.process_string(prompt, context)
