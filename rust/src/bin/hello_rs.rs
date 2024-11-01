// This program is a simple example program that greets the user and optionally
// builds a shopping list. The program can optionally use AI.

use std::env;
use std::io::{self, Write};
use std::process::{Command, Stdio};

struct Options {
    language: String,
    name: String,
    shopping_items: Vec<String>,
    use_ai: bool,
}

/// Generates a greeting using AI based on the given options
fn ai_get_greeting(opts: &Options) -> io::Result<String> {
    let query = format!(
        "Please greet {} in LANG={}. Be creative, but not more than 50 words. Don't translate back to English.",
        opts.name, opts.language
    );
    llm_query(&query)
}

/// Builds a simple shopping list from the given options
fn build_shopping_list_simple(opts: &Options) -> String {
    let mut buffer = String::from("\nShopping list:\n");
    for item in &opts.shopping_items {
        buffer.push_str(&format!("- {}\n", item));
    }
    buffer
}

/// Prints the usage information for the program
fn usage(stream: &mut dyn Write, program: &str) -> io::Result<()> {
    writeln!(stream, "Usage: {} [OPTIONS]", program)?;
    writeln!(stream, "Options:")?;
    writeln!(stream, "  -h, --help            Print this help message")?;
    writeln!(
        stream,
        "  -l, --language=LANG   Set the language (default: en)"
    )?;
    writeln!(
        stream,
        "  -n, --name=NAME       Set the name (default: world)"
    )?;
    writeln!(
        stream,
        "  -s, --shopping=ITEM   Add an item to the shopping list"
    )?;
    writeln!(
        stream,
        "  -a, --use-ai          Use AI to help with the shopping list"
    )?;
    Ok(())
}

/// Parses command-line arguments and returns an Options struct
fn get_options() -> Options {
    let mut opts = Options {
        language: String::from("en"),
        name: String::from("world"),
        shopping_items: Vec::new(),
        use_ai: false,
    };

    let args: Vec<String> = env::args().collect();
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "-h" | "--help" => {
                usage(&mut io::stdout(), &args[0]).unwrap();
                std::process::exit(0);
            }
            "-l" | "--language" => {
                if i + 1 < args.len() {
                    opts.language.clone_from(&args[i + 1]);
                    i += 1;
                }
            }
            "-n" | "--name" => {
                if i + 1 < args.len() {
                    opts.name.clone_from(&args[i + 1]);
                    i += 1;
                }
            }
            "-s" | "--shopping" => {
                if i + 1 < args.len() {
                    opts.shopping_items.push(args[i + 1].clone());
                    i += 1;
                }
            }
            "-a" | "--use-ai" => opts.use_ai = true,
            _ => {
                eprintln!("Unknown option: {}", args[i]);
                usage(&mut io::stderr(), &args[0]).unwrap();
                std::process::exit(1);
            }
        }
        i += 1;
    }

    opts
}

fn main() -> io::Result<()> {
    let opts = get_options();

    let greeting = if opts.use_ai {
        ai_get_greeting(&opts)?
    } else {
        match opts.language.as_str() {
            "fr" => "Bonjour",
            "es" => "Hola",
            "de" => "Hallo",
            "jp" => "こんにちは",
            "cn" => "你好",
            "en" => "Hello",
            _ => "Whoops, I don't know your language without AI!  Hi",
        }
        .to_string()
    };

    if opts.use_ai {
        print!("{}", greeting);
    } else {
        println!("{}, {}", greeting, opts.name);
    }

    if !opts.shopping_items.is_empty() {
        let mut shopping_list = build_shopping_list_simple(&opts);
        if opts.use_ai {
            let prompt = format!(
                "Please echo the input and add any extra items we might need, in LANG={}. Don't translate back to English.",
                opts.language
            );
            shopping_list = llm_process(&prompt, &shopping_list)?;
        }
        print!("{}", shopping_list);
    }

    Ok(())
}

/// Sends a query to the LLM and returns the response
fn llm_query(query: &str) -> io::Result<String> {
    let output = Command::new("llm").arg("query").arg(query).output()?;
    Ok(String::from_utf8_lossy(&output.stdout).into_owned())
}

/// Processes input through the LLM with a given prompt
fn llm_process(prompt: &str, input: &str) -> io::Result<String> {
    let mut child = Command::new("llm")
        .arg("process")
        .arg(prompt)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()?;

    child.stdin.as_mut().unwrap().write_all(input.as_bytes())?;

    let output = child.wait_with_output()?;
    Ok(String::from_utf8_lossy(&output.stdout).into_owned())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_build_shopping_list_simple() {
        let opts = Options {
            language: "en".to_string(),
            name: "Test".to_string(),
            shopping_items: vec!["apples".to_string(), "bananas".to_string()],
            use_ai: false,
        };
        let list = build_shopping_list_simple(&opts);
        assert_eq!(list, "\nShopping list:\n- apples\n- bananas\n");
    }
}
