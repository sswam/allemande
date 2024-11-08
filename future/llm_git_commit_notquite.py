#!/usr/bin/env python3-allemande

"""
llm_git_commit.py: Git commit wrapper that generates commit messages using Language Models (LLMs).

Usage:
    llm_git_commit.py [options] [file ...]

Options:
    -4, --gpt4               Use GPT-4 model
    -n, --no-generate        Start at menu without generating a commit message
    -3, --gpt4-mini          Use GPT-4 Mini model
    -c, --claude             Use Claude model
    -i, --claude-instant     Use Claude Instant model
    -o, --openai-o1          Use OpenAI o1 model
    -M, --openai-o1-mini     Use OpenAI o1-mini model
    -m MESSAGE, --message MESSAGE
                             Use the given message instead of generating one
    -e, --editor             Normal git commit using the editor
    -x, --cleanup            Clean up commit-message.*.txt files
    -d, --diff               Show the diff of staged changes
    -v, --vimdiff            Show the vimdiff of staged changes
    -b, --bug-check          Check for bugs using the selected LLM
    -h, --help               Show this help message
"""

import argparse
import subprocess
import sys
import os
import shutil
from datetime import datetime
import tempfile
import logging

logger = logging.getLogger(__name__)

# Set up basic configuration
logging.basicConfig(
    level=logging.DEBUG,  # Set the debug level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configuration for LLM models
MODEL_CONFIGS = {
    '4': {
        'name': 'GPT-4',
        'process': '4',
    },
    '4m': {
        'name': 'GPT-4o-mini',
        'process': '4m',
    },
    'c': {
        'name': 'Claude',
        'process': 'c',
    },
    'i': {
        'name': 'Claude Instant',
        'process': 'i',
    },
    'op': {
        'name': 'OpenAI o1',
        'process': 'op',
    },
    'om': {
        'name': 'OpenAI o1-mini',
        'process': 'om',
    },
}

DEFAULT_MODEL_KEY = os.getenv("ALLEMANDE_LLM_DEFAULT", "c")  # Default to Claude

# Define global variables for cleanup
TEMP_FILES = []

def run_command(cmd, capture_output=True, text=True, check=True):
    """Run a shell command and return the result."""
    logger.debug(f"Running command: {cmd}")
    result = subprocess.run(cmd, capture_output=capture_output, text=text, check=check)
    return result

def get_git_root():
    """Get the top level directory of the git repository."""
    result = run_command(['git', 'rev-parse', '--show-toplevel'])
    return result.stdout.strip()

def realpath(path):
    """Return the absolute path."""
    return os.path.abspath(path)

def relative_path(path, start):
    """Return the relative path from start to path."""
    return os.path.relpath(path, start)

def cleanup():
    """Cleanup temporary files."""
    for file in TEMP_FILES:
        try:
            os.remove(file)
            print(f"Removed temporary file: {file}")
        except OSError:
            pass

def generate_timestamp():
    """Generate a timestamp string."""
    return datetime.now().strftime('%Y%m%d%H%M%S')

def get_staged_files():
    """Get a list of staged files."""
    result = run_command(['git', 'diff', '--name-only', '--cached'])
    return result.stdout.strip().split('\n') if result.stdout else []

def unstage_files(files):
    """Unstage the specified files."""
    if files:
        run_command(['git', 'restore', '--staged'] + files)

def stage_files(files):
    """Stage the specified files."""
    if files:
        run_command(['git', 'add'] + files)

def get_git_diff(files, context=10, color=False):
    """Get the git diff for the specified files."""
    cmd = ['git', 'diff', f'-U{context}']
    if color:
        cmd.append('--color')
    cmd.append('--')

    cmd.extend(files)
    result = run_command(cmd)
    return result.stdout

def model_name(key):
    """Get the model name from the key."""
    return MODEL_CONFIGS.get(key, {}).get('name', 'Unknown Model')

def process_llm(prompt, model_key):
    """Process the prompt using the specified LLM model."""
    model_process = MODEL_CONFIGS.get(model_key, {}).get('process')
    if not model_process:
        print(f"Unknown model key: {model_key}")
        sys.exit(1)

    try:
        result = subprocess.run(['llm', 'query', '-m', model_process, prompt],
                                capture_output=True,
                                text=True,
                                check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error processing LLM: {e.stderr}")
        sys.exit(1)

def generate_commit_message(diff_text, model_key):
    """Generate a commit message using the LLM."""
    print(f"Generating commit message using {model_name(model_key)} ...")
    prompt = (
        "Please describe this entire patch, for a git commit message, following the Conventional Commits spec.\n"
        "Do not invent anything that is not in the patch!\n"
        "Only describe the actual changes, lines starting with +, do not describe the surrounding patch context.\n"
        "The required format is as follows. Return only the commit message like this without any prelude or concluding statement!\n\n"
        "For a feature patch, focus on describing high-level features, without implementation details. For fixes and some other types, it makes sense to mention some details of the bug and fix.\n\n"
        "feat|fix|docs|style|refactor|test|chore|perf(short-module-name): a short summary line, preferably around 50 chars, not more than 70 chars\n\n"
        "- concise info about first change, if needed. If the line wraps\n"
        "  the second line must be indented like this.\n"
        "- concise info about second change, if any.\n"
        "- and so on ... but sometimes we do not need details, in which case just the header line is okay. *LESS IS MORE!*\n\n"
        "There can be only one feat or fix line per commit, then a blank line, then the list.\n"
        "If a commit is simple, you can omit the list. Do not add a list item that just repeats the main line.\n"
        "The (short-module-name) part is optional. Commit type can be feat|fix|chore etc.\n"
        "Do not belabour the obvious; we do not need too much detail, e.g. moving folders do not list every file that was moved.\n"
    )
    full_prompt = diff_text + "\n\n" + prompt
    commit_message = process_llm(full_prompt, model_key)

    # Post-processing: Remove code fences and trailing whitespace
    commit_message = '\n'.join(
        line for line in commit_message.splitlines()
        if not line.strip().startswith('```')
    ).strip()

    # Format the message
    commit_message = subprocess.run(['fmt', '-s', '-w', '78'], input=commit_message, capture_output=True, text=True).stdout.strip()

    return commit_message

def check_for_bugs(diff_text, model_key):
    """Check for bugs using the LLM."""
    print(f"Checking for bugs using {model_name(model_key)} ...")
    prompt = (
        "Please carefully review this patch with a fine-tooth comb! "
        "Answer LGTM if bug-free, or list bugs still present in the patched code. "
        "Do NOT list bugs in the original code that are fixed by the patch. "
        "You may also list other issues or suggestions if they are important. "
        "Expected format:\n"
        "```\n"
        "1. bug or issue\n"
        "2. another bug or issue\n"
        "```\n\n"
        "or just LGTM."
    )
    full_prompt = diff_text + "\n\n" + prompt
    review_result = process_llm(full_prompt, model_key)
    review_result = review_result.strip()
    return review_result

def confirm_choice(commit_message_file, review_file, model_key, staged_files):
    """Prompt the user for confirmation and actions."""
    while True:
        if os.path.exists(commit_message_file):
            with open(commit_message_file, 'r') as f:
                message = f.read()
            print("\nCommit Message:\n" + "="*15 + "\n" + message + "\n")
            prompt = "Commit with this message? [y/n/q/e/3/4/c/i/o/M/d/v/b/?]: "
        else:
            prompt = "Action? [y/n/q/e/3/4/c/i/o/M/d/v/b/?]: "

        choice = input(prompt).strip().lower()

        if choice == 'y':
            return 'commit'
        elif choice in ['n', 'q']:
            return 'abort'
        elif choice == 'e':
            editor = os.getenv('EDITOR', 'vi')
            subprocess.run([editor, commit_message_file])
        elif choice in ['3', '4', 'c', 'i', 'o', 'M']:
            generate_commit_message_wrapper(commit_message_file, model_key, choice)
        elif choice == 'd':
            show_diff(staged_files)
        elif choice == 'v':
            show_vimdiff(staged_files)
        elif choice == 'b':
            review = check_for_bugs_wrapper(review_file, model_key)
            if review.lower() == 'lgtm':
                print("LGTM: No bugs found.")
                return 'proceed'
            else:
                print(f"Bugs found:\n{review}")
        elif choice in ['x']:
            cleanup_files([commit_message_file, review_file])
        elif choice in ['?','h']:
            display_help()
        else:
            print("Invalid choice. Type '?' or 'h' for help.")

def generate_commit_message_wrapper(commit_message_file, model_key, choice):
    """Generate commit message based on user choice."""
    model_key_map = {
        '3': '4m',
        '4': '4',
        'c': 'c',
        'i': 'i',
        'o': 'op',
        'M': 'om'
    }
    selected_model = model_key_map.get(choice, DEFAULT_MODEL_KEY)
    diff_text = get_git_diff(get_staged_files())
    commit_message = generate_commit_message(diff_text, selected_model)
    with open(commit_message_file, 'w') as f:
        f.write(commit_message)
    print(f"Commit message generated using {model_name(selected_model)}.")

def check_for_bugs_wrapper(review_file, model_key):
    """Check for bugs and save the review."""
    diff_text = get_git_diff(get_staged_files())
    review = check_for_bugs(diff_text, model_key)
    with open(review_file, 'w') as f:
        f.write(review)
    return review

def show_diff():
    """Show the git diff."""
    diff_text = get_git_diff(get_staged_files(), color=True)
    print(diff_text)

def show_vimdiff():
    """Show the vimdiff of staged changes."""
    files = get_staged_files()
    if files:
        subprocess.run(['git', 'vimdiff'] + files)
    else:
        subprocess.run(['git', 'vimdiff'])

def cleanup_files(files):
    """Remove specified temporary files."""
    for file in files:
        if os.path.exists(file):
            os.remove(file)
            print(f"Removed {file}")

def display_help():
    """Display help information."""
    help_text = """
y: commit with this message
n|q: abort
e: edit the message
3: generate with GPT-4-mini
4: generate with GPT-4
c: generate with Claude
i: generate with Claude Instant
o: generate with OpenAI o1
M: generate with OpenAI o1-mini
d: diff the staged changes
v: vimdiff the staged changes
b: check for bugs with the selected LLM
?: show this help message
x: clean up commit-message.*.txt files
"""
    print(help_text)

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='git commit with a message generated by an LLM.', add_help=False)
    parser.add_argument('-4', '--gpt4', action='store_const', const='4', dest='model', help='Use GPT-4 model')
    parser.add_argument('-n', '--no-generate', action='store_const', const='', dest='model', help='Start at menu without generating a commit message')
    parser.add_argument('-3', '--gpt4-mini', action='store_const', const='4m', dest='model', help='Use GPT-4 Mini model')
    parser.add_argument('-c', '--claude', action='store_const', const='c', dest='model', help='Use Claude model')
    parser.add_argument('-i', '--claude-instant', action='store_const', const='i', dest='model', help='Use Claude Instant model')
    parser.add_argument('-o', '--openai-o1', action='store_const', const='op', dest='model', help='Use OpenAI o1 model')
    parser.add_argument('-M', '--openai-o1-mini', action='store_const', const='om', dest='model', help='Use OpenAI o1-mini model')
    parser.add_argument('-m', '--message', type=str, help='Use the given message instead of generating one')
    parser.add_argument('-e', '--editor', action='store_true', help='Normal git commit using the editor')
    parser.add_argument('-x', '--cleanup', action='store_true', help='Clean up commit-message.*.txt files')
    parser.add_argument('-d', '--diff', action='store_true', help='Show the diff of staged changes')
    parser.add_argument('-v', '--vimdiff', action='store_true', help='Show the vimdiff of staged changes')
    parser.add_argument('-b', '--bug-check', action='store_true', help='Check for bugs using the selected LLM')
    parser.add_argument('-h', '--help', action='store_true', help='Show this help message')
    parser.add_argument('files', nargs='*', help='Files to include in the commit')

    args = parser.parse_args()
    return args

def main():
    args = parse_arguments()

    print(args)

    # Handle help
    if args.help:
        print(__doc__)
        sys.exit(0)

    # Handle cleanup
    if args.cleanup:
        commit_msgs = [f for f in os.listdir('.') if f.startswith('commit-message.') and f.endswith('.txt')]
        reviews = [f for f in os.listdir('.') if f.startswith('review.') and f.endswith('.txt')]
        for f in commit_msgs + reviews:
            try:
                os.remove(f)
                print(f"Removed {f}")
            except OSError as e:
                print(f"Error removing {f}: {e}")
        sys.exit(0)

    # Handle editor commit
    if args.editor:
        run_command(['git', 'commit'])
        sys.exit(0)

    # Determine model
    model_key = args.model if args.model is not None else DEFAULT_MODEL_KEY
    if model_key not in MODEL_CONFIGS and model_key != '':
        print(f"Invalid model option specified.")
        sys.exit(1)

    # Prepare files
    files = []
    for path in args.files:
        if os.path.isdir(path) and not os.path.islink(path):
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    full_path = os.path.join(root, filename)
                    files.append(realpath(full_path))
        else:
            files.append(realpath(path))

    # Change to git root and get relative paths
    git_root = get_git_root()
    os.chdir(git_root)
    if files:
        files = [relative_path(f, git_root) for f in files]

    # Unstage files if already staged
    staged_files = get_staged_files()
    if staged_files:
        unstage_files(staged_files)

    # If message is provided, perform commit directly
    if args.message:
        run_command(['git', 'commit', '-m', args.message])
        sys.exit(0)

    # Generate commit message if a model is selected
    commit_message = ""
    review = ""

    timestamp = generate_timestamp()
    commit_message_file = f"commit-message.{timestamp}.txt"
    review_file = f"review.{timestamp}.txt"

    if model_key:
        # Run bug check
        if args.bug_check:
            diff_text = get_git_diff(staged_files)
            review = check_for_bugs(diff_text, model_key)
            with open(review_file, 'w') as f:
                f.write(review)
            if review.lower() != 'lgtm':
                print(f"Bugs found:\n{review}")

        # Generate commit message
        if not args.model == "" and not args.bug_check:
            diff_text = get_git_diff(staged_files)
            commit_message = generate_commit_message(diff_text, model_key)
            with open(commit_message_file, 'w') as f:
                f.write(commit_message)
            TEMP_FILES.extend([commit_message_file, review_file])

    # Prompt for user confirmation and actions
    action = confirm_choice(commit_message_file, review_file, model_key, staged_files)
    if action == 'commit' or action == 'proceed':
        if os.path.exists(commit_message_file):
            with open(commit_message_file, 'r') as f:
                commit_message = f.read()
        else:
            commit_message = args.message or ""
        # Stage the files again
        stage_files(files)
        # Commit with the generated message
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_msg:
            tmp_msg.write(commit_message)
            tmp_msg_path = tmp_msg.name
        run_command(['git', 'commit', '-F', tmp_msg_path])
        TEMP_FILES.append(tmp_msg_path)
    elif action == 'abort':
        print("Commit aborted.")
        cleanup()
        sys.exit(1)

    # Final cleanup
    cleanup()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cleanup()
        sys.exit(1)
