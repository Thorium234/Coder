
# Vibe Coder

Vibe Coder is a keyboard automation tool written in Go that simulates the process of writing Python code inside Visual Studio Code. It takes Python project files, opens them in VS Code, and types the code gradually with simulated typing behaviour, including occasional mistakes and corrections.

The goal is to simulate a coding session rather than simply paste code into an editor.

## Features

- Simulated typing of Python source code into VS Code.
- Randomized typing delays to simulate human typing.
- Simulated typing errors and corrections.
- Built-in Python projects.
- Support for local Python project files.
- Optional online mode for fetching public Python files from GitHub.
- Runtime duration control.
- Typing speed adjustment.
- Temporary project directory management.
- Optional preservation of generated project files.
- Best-effort active window focus protection.
- Dry-run mode for testing project selection without keyboard automation.

## Requirements

- Go 1.23 or newer.
- Visual Studio Code.
- VS Code `code` command available in your PATH.
- Robotgo system dependencies required by your operating system.

## Installation

Clone the repository:

```bash
git clone https://github.com/Thorium234/Coder.git
cd Coder
```

Install the dependencies:

```bash
go mod init vibe-coder
go get github.com/go-vgo/robotgo
```

If the repository already contains a `go.mod` file, do not run `go mod init` again.

## Usage

Run the application:

```bash
go run .
```

### Dry Run

Preview a selected project without opening VS Code or simulating keyboard input:

```bash
go run . --dry-run
```

### Runtime

Run the program for three hours:

```bash
go run . --hours 3
```

Run without a time limit:

```bash
go run . --hours 0
```

### Typing Speed

Slow down typing:

```bash
go run . --slowdown 1.5
```

### Local Projects

Load Python files from a custom directory:

```bash
go run . --projects-dir ./my_projects
```

### Online Mode

Attempt to fetch a public Python file from GitHub:

```bash
go run . --online
```

### Preserve Generated Files

Keep generated project files:

```bash
go run . --keep
```

Specify a destination directory:

```bash
go run . --keep --out ~/vibe_projects
```

### Keep VS Code Windows Open

Prevent the application from closing VS Code windows after typing:

```bash
go run . --keep-windows
```

### Window Wait

Specify how long to wait after opening VS Code:

```bash
go run . --window-wait 12
```

### Disable Focus Check

Disable active window title verification:

```bash
go run . --no-focus-check
```

This option is unsafe and should only be used when you understand the risks of keyboard automation.

## Available Options

| Option | Description |
|---|---|
| `--dry-run` | Preview project selection without opening VS Code or typing |
| `--hours` | Specify runtime duration in hours, zero means unlimited |
| `--slowdown` | Adjust typing speed |
| `--projects-dir` | Load Python files from a custom directory |
| `--online` | Attempt to fetch a public Python file from GitHub |
| `--keep` | Preserve generated project files |
| `--out` | Specify output directory for preserved projects |
| `--keep-windows` | Keep VS Code windows open |
| `--window-wait` | Specify the delay after opening VS Code |
| `--no-focus-check` | Disable focus verification |

## Safety

Keyboard automation can type into the wrong application if focus is lost or misidentified.

Start with dry-run mode before using keyboard simulation:

```bash
go run . --dry-run
```

The active window focus check is best-effort and is not a complete guarantee of safety.

The `--no-focus-check` option bypasses the focus safeguard.

Use this software responsibly and monitor automated typing sessions.

## Limitations

- The pause and resume hotkeys from the original Python implementation are not currently ported.
- Online mode fetches public Python files and does not implement Anthropic API code generation.
- Active window detection depends on operating system support.
- This version has not been fully build-verified in every operating system environment.

## License

See the repository for licensing information.
