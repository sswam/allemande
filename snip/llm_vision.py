    # Calculate resize factor based on vendor
    if vendor == "openai":
        if detail == "low":
            factor = calculate_resize_factor(width, height, 512 * 512, 512, 512)
        else:  # high or auto
            factor = calculate_resize_factor(width, height, 768 * 2000, 768, 2000)
    elif vendor == "anthropic":
        factor = calculate_resize_factor(width, height, 1.15e6, 1568, 1568)
    else:
        return ResizeResult(processed_img, False, was_converted)
