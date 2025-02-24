class Shortcode:
    def __init__(self, Unprompted):
        self.Unprompted = Unprompted
        self.description = "Generates an AI art prompt format for a person with their name, age, emotion, and clothes."

    def run_atomic(self, pargs, kwargs, context):
        if not pargs:
            return ""

        # Get the name from the first argument
        _name = self.Unprompted.parse_advanced(pargs[0], context)
        _clothes = self.Unprompted.parse_advanced(pargs[1], context) if len(pargs) > 1 else None
        _emo = self.Unprompted.parse_advanced(pargs[2], context) if len(pargs) > 2 else None
        _age = self.Unprompted.parse_advanced(pargs[3], context) if len(pargs) > 3 else None

        # "." means the default (load the file)
        if _clothes is None or _clothes == ".":
            _clothes = f"[use clothes/{_name}]"
        if _emo is None or _emo == ".":
            _emo = f"[use emo/{_name}]"
        if _age is None or _age == ".":
            _age = f"[use age/{_name}]"

        # "-" means a global default
        if _clothes == "-":
            _clothes = "nude"
        if _emo == "-":
            _emo = "light smile"
        if _age == "-":
            _age = 21
        if str(_age).isnumeric():
            _age = f"{_age} years old"

        # "" means nothing, omit the field

        # Construct the prompt
        prompt = f"[use {_name}]"
        if _clothes:
            prompt += f", {_clothes}"
        if _emo:
            prompt += f", {_emo}"
        if _age:
            prompt += f", {_age}"

        # Process and return the constructed prompt
        return self.Unprompted.process_string(prompt, context)
