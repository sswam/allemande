const getZoom = () => {
    const basePixelRatio = window.devicePixelRatio;
    const rawZoom = ((window.outerWidth - 10) / window.innerWidth);

    if (basePixelRatio === 1) {
        return rawZoom;
    }

    const retinaFactor = Math.round(basePixelRatio);
    return rawZoom / retinaFactor;
}
