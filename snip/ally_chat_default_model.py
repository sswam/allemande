# TODO can't select model from here now

models = {
    "default": {
        "abbrev": "llama3",
        "description": "Meta-Llama-3.1-8B-Instruct",
        "cost": 0,
    },
}

first_model = next(iter(models.keys()))
default_model = os.environ.get("BB_MODEL", first_model)
