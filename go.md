# Vibe Coder Rust Guide

This document explains how to build, run, inspect, and extend the Rust version of Vibe Coder.

## 1. What the project does

Vibe Coder automates a coding session in Visual Studio Code by opening Python project files and simulating keyboard input. The controller is written in Rust, while the sample projects it types remain Python source files.

The Rust rewrite aims to retain the original tool's main workflow:

- Select built-in or local Python projects.
- Optionally retrieve public source files online.
- Open files in Visual Studio Code.
- Simulate typing with configurable delays.
- Manage runtime limits and project folders.
- Preserve or clean up generated files.

Keyboard automation is inherently risky. Start with a dry run and supervise any session that sends keystrokes.

## 2. Requirements

Install:

- Rust and Cargo, using the official Rust installation instructions: https://www.rust-lang.org/tools/install
- Visual Studio Code: https://code.visualstudio.com/
- The `code` command in your shell's `PATH`, if the application uses it to launch VS Code.

Check the installation:

```bash
rustc --version
cargo --version
code --version
```

## 3. Project layout

The exact layout may evolve. The initial rewrite is intended to use a small CLI structure:

```text
vibe_coder_rust/
├── Cargo.toml
├── README.md
└── src/
    ├── main.rs
    └── projects.json
```

- `Cargo.toml`: package metadata and dependencies.
- `src/main.rs`: CLI entry point and controller logic.
- `src/projects.json`: embedded project data.

As the code grows, consider splitting functionality into modules such as `cli`, `projects`, `typing`, `editor`, `online`, and `cleanup`.

## 4. Build

From the project directory:

```bash
cargo build
```

Build an optimized executable:

```bash
cargo build --release
```

The release executable is written under `target/release/`.

## 5. Run

Start the program:

```bash
cargo run
```

Or use the release build:

```bash
cargo run --release
```

### Dry run

Use dry-run mode first, if supported, to inspect project selection without launching keyboard automation:

```bash
cargo run -- --dry-run
```

### Runtime

Set a runtime limit in hours, if supported:

```bash
cargo run -- --hours 1
```

A value of `0` may represent unlimited runtime, depending on the implementation. Verify the CLI help before relying on that behavior.

### Typing speed

Adjust the typing speed factor, if supported:

```bash
cargo run -- --slowdown 1.5
```

### Local projects

Provide a folder containing Python files, if supported:

```bash
cargo run -- --projects-dir ./my_projects
```

### Online mode

Enable the online source retrieval mode, if supported:

```bash
cargo run -- --online
```

Only retrieve files from sources you trust. Review retrieved code before running it.

### Keep files

Retain generated project files, if supported:

```bash
cargo run -- --keep
```

### Keep VS Code windows open

```bash
cargo run -- --keep-windows
```

### Window wait

```bash
cargo run -- --window-wait 10
```

### Disable focus checks

```bash
cargo run -- --no-focus-check
```

Disabling focus checks increases the risk of typing into an unintended window. Avoid this option unless you understand the consequences and are supervising the session.

## 6. Discover CLI options

The exact flags depend on the implementation. Use:

```bash
cargo run -- --help
```

Do not assume a flag exists merely because it is described in an older version of this guide.

## 7. Troubleshooting

### Cargo cannot download dependencies

Check your internet connection, then retry:

```bash
cargo build
```

### VS Code does not open

Check that VS Code is installed and that the `code` command works:

```bash
code --version
```

If the command is not available, configure your operating system's VS Code command-line launcher or update the implementation to use the correct executable path.

### Keystrokes go to the wrong window

Stop the program immediately. Use dry-run mode first, supervise sessions, and avoid disabling focus checks. Window-title checks are not a guarantee that the intended editor or file has focus.

### Keyboard automation fails on Linux

Keyboard automation libraries can depend on desktop environment, display server, permissions, and native system libraries. Consult the documentation for the automation dependency used by the project and the requirements for your Linux session.

### Compilation errors

Run:

```bash
cargo check
cargo test
```

Read the first compiler error carefully. Fix the underlying issue before attempting a full automation session.

## 8. Development workflow

Before submitting a change:

```bash
cargo fmt --check
cargo check
cargo test
cargo clippy -- -D warnings
```

If formatting is needed:

```bash
cargo fmt
```

Test non-automation functionality before testing keyboard control. Avoid running automation tests that type into a real desktop unattended.

## 9. Safety and limitations

- Keyboard automation can send input to the wrong application.
- Focus detection is best-effort and should not be treated as a security boundary.
- Online source retrieval should not be considered safe execution of downloaded code.
- Some features of the original Python implementation may not yet exist in the Rust rewrite.
- Pause and resume controls, API-based code generation, and OS-specific window handling should be considered incomplete unless the implementation and tests demonstrate otherwise.

## 10. Rust resources

- Rust language: https://www.rust-lang.org/
- The Rust Book: https://doc.rust-lang.org/book/
- Cargo documentation: https://doc.rust-lang.org/cargo/
- Rust standard library: https://doc.rust-lang.org/std/
- Rust compiler error index: https://doc.rust-lang.org/error_codes/

## 11. Contributing

1. Open an issue describing the bug or proposed change.
2. Keep changes focused and avoid silently changing the original tool's behavior.
3. Run formatting, checks, tests, and Clippy.
4. Document platform-specific behavior and limitations.
5. Submit a pull request with a clear summary.

