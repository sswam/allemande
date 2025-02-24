import random
import re

class Shortcode:
    def __init__(self, Unprompted):
        self.Unprompted = Unprompted
        self.description = "Returns the content if the number you passed is greater than or equal to a random number between 1 and 100, and weights the content with a random weight between the min and max values, to 2 decimal places."

    def preprocess_block(self, pargs, kwargs, context):
        return True

    def run_block(self, pargs, kwargs, context, content):
        _number = self.Unprompted.parse_advanced(pargs[0], context) if len(pargs) > 0 else 100
        _min = self.Unprompted.parse_advanced(pargs[1], context) if len(pargs) > 1 else 1.0
        _max = self.Unprompted.parse_advanced(pargs[2], context) if len(pargs) > 2 else _min
        _sides = (
            self.Unprompted.parse_advanced(kwargs["_sides"], context) if "_sides" in kwargs else 100
        )
        else_id = (
            kwargs["_else_id"] if "_else_id" in kwargs else str(self.Unprompted.conditional_depth)
        )

        if _max < _min or _number <= 0:
            return ""

        weight = random.uniform(float(_min), float(_max))
        weight = round(weight, 2)

        content = re.sub(r"\s*(\\n)?$", r"", content)
        if content and content[-1] == ",":
            content = content[:-1]
            comma = ","
        else:
            comma = ""

        to_return = ""
        if int(float(_number)) >= random.randint(1, int(_sides)):
            self.Unprompted.prevent_else(else_id)
            if "_raw" in pargs:
                to_return = self.Unprompted.process_string(content, context)
            else:
                to_return = self.Unprompted.process_string(
                    self.Unprompted.sanitize_pre(
                        content, self.Unprompted.Config.syntax.sanitize_block, True
                    ),
                    context,
                    False,
                )

            to_return = re.sub(r",?\s*(\\n)?$", r"", to_return)

            to_return = to_return.strip()

            if weight != 1 and to_return:
                to_return = f"({to_return}:{weight})"
            if to_return:
                to_return += comma
        else:
            self.Unprompted.shortcode_objects["else"].do_else[else_id] = True

        # self.Unprompted.conditional_depth = max(0, self.Unprompted.conditional_depth -1)

        return to_return
