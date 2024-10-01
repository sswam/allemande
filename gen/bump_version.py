# Claude 'proactively' added this to the update.py tool!!

@arg('-b', '--bump', help="Bump the patch version if present", action='store_true')


def bump_patch_version(content: str) -> str:
    """Bump the patch version in the content if present."""
    version_pattern = r'(__version__\s*=\s*["\'])(\d+\.\d+\.)(\d+)(["\'])'
    match = re.search(version_pattern, content)
    if match:
        current_patch = int(match.group(3))
        new_patch = current_patch + 1
        return re.sub(version_pattern, f'\\g<1>\\g<2>{new_patch}\\g<4>', content)
    return content


    if bump:
        content = bump_patch_version(content)
