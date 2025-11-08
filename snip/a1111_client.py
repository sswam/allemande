def perturbed_attention_guidance_add_params_a1111(params: dict[str, Any], pag_scale: float):
    """Add perturbed attention guidance parameters to the params."""
    if not "alwayson_scripts" in params:
        params["alwayson_scripts"] = {}

    # This is a bit unintelligible as the extension does not name its parameters.
    # I just copied them from the API payload extension.
    params["alwayson_scripts"]["Incantations"] = {
        "args": [
            False,
            11,
            0,
            150,
            False,
            1,
            0.8,
            3,
            0,
            0,
            150,
            4,
            True,
            pag_scale,
            0,
            150,
            False,
            "Constant",
            0,
            100,
            True,
            False,
            False,
            2,
            0.1,
            0.5,
            0,
            "",
            0,
            25,
            1,
            False,
            False,
            False,
            "BREAK",
            "-",
            0.2,
            10,
        ]
    }
