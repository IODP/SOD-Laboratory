# sodlab_gradio_ui.py
"""
Gradio UI wrapper to build & run sodlab CLI commands.

Usage:
    python sodlab_gradio_ui.py

This will launch a local Gradio app where you can pick commands and flags,
preview the constructed command, and run sodlab locally.

Security note: This UI will execute the local executable you point it to.
Only run commands you trust.
"""

import shlex
import subprocess
import sys
import os
from pathlib import Path
from typing import List, Tuple

import gradio as gr


# Helper: safely build command as a list for subprocess
def build_sodlab_command(
    sodlab_path: str,
    do_archive: bool,
    do_transform: bool,
    do_compile: bool,
    archive_mode: str,  # "copy", "move", "hardlink" or empty
    systems_list: List[str],
    extra_systems_text: str,
    input_dir: str,
    output_dir: str,
    recursive: bool,
    force_relative_paths: bool,
    step: bool,
    logfile: bool,
    force: bool,
    settings_path: str,
    dry_run: bool,
) -> Tuple[List[str], str]:
    """
    Returns (cmd_list, cmd_preview_str).
    cmd_list is suitable to pass to subprocess (list form).
    cmd_preview_str is a shell-style string for display / copy.
    """

    # normalize sodlab path
    sodlab_path = sodlab_path.strip() or "sodlab"
    cmd = [sodlab_path]

    # mutually exclusive check: compile cannot combine with transform/archive
    if do_compile and (do_archive or do_transform):
        raise ValueError("The --compile command cannot be used with --archive or --transform in the same invocation.")

    # Add main actions
    if do_archive:
        cmd.append("--archive")
    if do_transform:
        cmd.append("--transform")
    if do_compile:
        cmd.append("--compile")

    # archive mode (only valid if archive is on)
    if do_archive and archive_mode:
        if archive_mode not in ("copy", "move", "hardlink"):
            raise ValueError("Invalid archive mode")
        cmd.append(f"--{archive_mode}")

    # Systems: combine CheckboxGroup selections and any custom text
    systems = []
    if systems_list:
        systems = [s.strip() for s in systems_list if s.strip()]
    if extra_systems_text:
        # Accept comma, space or newline separated
        for tok in shlex.split(extra_systems_text):
            if tok.strip():
                systems.append(tok.strip())
    if not systems:
        raise ValueError("At least one system must be specified (e.g. GRA MS PWAVE_L).")
    cmd.append("--system")
    cmd.extend(systems)

    # Required input/output
    if not input_dir:
        raise ValueError("--input is required.")
    if not output_dir:
        raise ValueError("--output is required.")
    cmd.extend(["--input", input_dir])
    cmd.extend(["--output", output_dir])

    # Optional flags
    if recursive:
        cmd.append("--recursive")
    if force_relative_paths:
        cmd.append("--force_relative_paths")
    if step:
        cmd.append("--step")
    if logfile:
        cmd.append("--logfile")
    if force:
        cmd.append("--force")
    if settings_path:
        cmd.extend(["--settings", settings_path])

    # Build a shell preview string (quoting paths sensibly)
    def quote_for_preview(token: str) -> str:
        # Use shlex.quote for POSIX; on Windows this also provides a reasonable quoting for display.
        return shlex.quote(token)

    # preview = " ".join(quote_for_preview(t) for t in cmd)

    preview = " ".join(t for t in cmd)
    return cmd, preview


# Execute command and capture output
def run_subprocess_and_capture(cmd_list: List[str], capture_logfile: bool = True, logfile_path: str = None) -> Tuple[int, str, str]:
    """
    Runs subprocess.run with the given list. Returns (returncode, stdout, stderr).
    If logfile_path is given, write stdout+stderr to that file as well.
    """
    # Ensure Popen uses list form.
    try:
        # Use subprocess.run to wait until completion
        completed = subprocess.run(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
        stdout = completed.stdout or ""
        # stderr = completed.stderr or ""
        stderr = ""
        rc = completed.returncode
    except Exception as e:
        # Could not run (executable not found, permission, etc.)
        stdout = ""
        stderr = f"Failed to execute command: {e}"
        rc = -1

    # strip terminal painting characters:
    GREEN = "\033[92m"
    RESET = "\033[0m"
    stdout = stdout.replace(GREEN,"")
    stdout = stdout.replace(RESET,"")
    
    if capture_logfile and logfile_path:
        try:
            p = Path(logfile_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("w", encoding="utf-8") as fh:
                fh.write(f"Command: {' '.join(shlex.quote(x) for x in cmd_list)}\n\n")
                fh.write("=== STDOUT ===\n")
                fh.write(stdout)
                fh.write("\n\n=== STDERR ===\n")
                fh.write(stderr)
                fh.write(f"\n\nReturn code: {rc}\n")
        except Exception as e:
            # if writing logfile fails, append to stderr
            stderr += f"\n(Note: failed to write UI logfile: {e})"

    return rc, stdout, stderr

def strip_gradio_quotes(path: str) -> str:
    if not isinstance(path, str):
        return path
    path = path.strip()
    # Remove surrounding single quotes if present
    if path.startswith("'") and path.endswith("'"):
        return path[1:-1]
    # Remove surrounding double quotes if somehow present
    if path.startswith('"') and path.endswith('"'):
        return path[1:-1]
    return path


# Gradio action: build preview only (dry run)
def preview_command(
    sodlab_path,
    do_archive,
    do_transform,
    do_compile,
    archive_copy,
    archive_move,
    archive_hardlink,
    systems_checked,
    systems_custom_text,
    input_dir,
    output_dir,
    recursive,
    force_relative_paths,
    step,
    logfile,
    force,
    settings_path,
):
    # Determine archive_mode
    archive_mode = ""
    if archive_copy:
        archive_mode = "copy"
    if archive_move:
        # prefer move if multiple selected (mutually exclusive in UI)
        archive_mode = "move"
    if archive_hardlink:
        archive_mode = "hardlink"

    try:
        cmd_list, preview = build_sodlab_command(
            sodlab_path=sodlab_path,
            do_archive=do_archive,
            do_transform=do_transform,
            do_compile=do_compile,
            archive_mode=archive_mode,
            systems_list=systems_checked or [],
            extra_systems_text=systems_custom_text or "",
            input_dir=input_dir or "",
            output_dir=output_dir or "",
            recursive=recursive,
            force_relative_paths=force_relative_paths,
            step=step,
            logfile=logfile,
            force=force,
            settings_path=settings_path or "",
            dry_run=True,
        )
    except Exception as e:
        return f"Error building command: {e}"

    return preview


# Gradio action: run the command
def run_command(
    sodlab_path,
    do_archive,
    do_transform,
    do_compile,
    archive_copy,
    archive_move,
    archive_hardlink,
    systems_checked,
    systems_custom_text,
    input_dir,
    output_dir,
    recursive,
    force_relative_paths,
    step,
    logfile,
    force,
    settings_path,
    ui_logfile_dir,
    dry_run,
):
    """
    Execute the command and return a result block containing:
    - constructed command
    - return code
    - stdout
    - stderr
    If dry_run is True, do not execute and just return the preview.
    """

    archive_mode = ""
    if archive_copy:
        archive_mode = "copy"
    if archive_move:
        archive_mode = "move"
    if archive_hardlink:
        archive_mode = "hardlink"

    try:
        cmd_list, preview = build_sodlab_command(
            sodlab_path=sodlab_path,
            do_archive=do_archive,
            do_transform=do_transform,
            do_compile=do_compile,
            archive_mode=archive_mode,
            systems_list=systems_checked or [],
            extra_systems_text=systems_custom_text or "",
            input_dir=input_dir or "",
            output_dir=output_dir or "",
            recursive=recursive,
            force_relative_paths=force_relative_paths,
            step=step,
            logfile=logfile,
            force=force,
            settings_path=settings_path or "",
            dry_run=dry_run,
        )
    except Exception as e:
        return "", -1, f"Error building command: {e}" 
    
        #{"cmd": "", "rc": -1, "stdout": "", "stderr": f"Error building command: {e}"}

    if dry_run:
        # return {"cmd": preview, "rc": 0, "stdout": "Dry-run: command not executed.", "stderr": ""}
        return preview, 0, "Dry-run: command not executed."

    # Decide UI logfile (store captured output of subprocess) if user asked for a UI logfile location
    ui_logfile_path = None
    if ui_logfile_dir:
        # name logfile with timestamp
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ui_logfile_path = str(Path(ui_logfile_dir) / f"sodlab_ui_capture_{timestamp}.log")

    rc, stdout, stderr = run_subprocess_and_capture(cmd_list, capture_logfile=bool(ui_logfile_path), logfile_path=ui_logfile_path)

    # If user enabled the sodlab --logfile option (which causes the executable to write a logfile inside --output),
    # mention where that logfile will appear (best-effort).
    sodlab_logfile_msg = ""
    if logfile:
        sodlab_logfile_msg = f"\nNote: sodlab was invoked with --logfile; sodlab's own logfile (if created) will be placed inside the output folder: {output_dir}"

    # Put together return dict for Gradio components to display
    # return {
    #     "cmd": preview,
    #     "rc": rc,
    #     "stdout": stdout,
    #     "stderr": stderr + sodlab_logfile_msg,
    # }
    
    return preview, rc, stdout # stderr + sodlab_logfile_msg


# Build Gradio UI
def create_ui():
    with gr.Blocks(title="SOD-Laboratory (sodlab) Gradio UI") as demo:
        gr.Markdown("## SOD-Laboratory CLI — Gradio front-end\n"
                    "Build commands for `sodlab` and run them locally. **Make sure you trust the executable you point to.**")

        with gr.Row():
            with gr.Column(scale=2):
                sodlab_path = strip_gradio_quotes(gr.Textbox(label="sodlab executable (path or name)", value="sodlab", info="Path to sodlab executable (e.g. C:\\sodlab\\sodlab.exe) or just 'sodlab' if on PATH."))
                gr.Markdown("### Actions")
                with gr.Row():
                    do_archive = gr.Checkbox(label="Archive", value=False)
                    do_transform = gr.Checkbox(label="Transform", value=False)
                    do_compile = gr.Checkbox(label="Compile", value=False)
                gr.Markdown("Archive mode (choose one if Archive enabled)")
                with gr.Row():
                    archive_copy = gr.Checkbox(label="Copy", value=True)
                    archive_move = gr.Checkbox(label="Move", value=False)
                    archive_hardlink = gr.Checkbox(label="Hardlink", value=False)

                gr.Markdown("### Systems (required)")
                # Provide some common systems in a checkbox group; user may add custom tokens
                systems_checked = gr.CheckboxGroup(
                    label="Common systems (click to include)",
                    choices=["GRA", "MS", "PWAVE_L", "NGR", "RGB", "ROI", "RSC", "MSLOOP", "PROFILE", "XSCAN", "SRM", "DSC"],
                    #value=["GRA"],
                    interactive=True,
                )
                systems_custom_text = gr.Textbox(label="Extra / custom systems (space or comma separated)", placeholder="e.g. GRA MS PWAVE_L")

                gr.Markdown("### Paths (required)")
                input_dir = strip_gradio_quotes(gr.Textbox(label="Input directory (--input)", placeholder=r"C:\data\in", value=""))
                output_dir = strip_gradio_quotes(gr.Textbox(label="Output directory (--output)", placeholder=r"C:\data\projects", value=""))

                gr.Markdown("### Optional flags")
                with gr.Row():
                    recursive = gr.Checkbox(label="--recursive", value=False)
                    force_relative_paths = gr.Checkbox(label="--force_relative_paths", value=False)
                with gr.Row():
                    step = gr.Checkbox(label="--step", value=False, interactive=False)
                    logfile = gr.Checkbox(label="--logfile (place sodlab logfile in output)", value=False)
                with gr.Row():
                    force = gr.Checkbox(label="--force (overwrites existing files for archive)", value=False)
                    settings_path = strip_gradio_quotes(gr.Textbox(label="--settings (optional path to settings.json)", placeholder=r"C:\sodlab\settings.json", value=""))

                gr.Markdown("### UI logging & execution")
                ui_logfile_dir = strip_gradio_quotes(gr.Textbox(label="Save UI-captured logfile to (optional)", placeholder=r"C:\temp", value="", info="If set, the UI will save a copy of stdout+stderr to this folder."))

                dry_run = gr.Checkbox(label="Dry run (show command but do not execute)", value=False)

                with gr.Row():
                    preview_btn = gr.Button("Preview command")
                    run_btn = gr.Button("Run command")

            # Right column: outputs
            with gr.Column(scale=3):
                cmd_preview = gr.Textbox(label="Command preview (copyable)", interactive=False)
                rc_out = gr.Number(label="Return code", value=0, interactive=False)
                stdout_out = gr.Textbox(label="STDOUT", lines=40, interactive=False)
                #stderr_out = gr.Textbox(label="STDERR", lines=12, interactive=False)

        # Wire preview button
        preview_btn.click(
            fn=preview_command,
            inputs=[
                sodlab_path,
                do_archive,
                do_transform,
                do_compile,
                archive_copy,
                archive_move,
                archive_hardlink,
                systems_checked,
                systems_custom_text,
                input_dir,
                output_dir,
                recursive,
                force_relative_paths,
                step,
                logfile,
                force,
                settings_path,
            ],
            outputs=[cmd_preview],
        )

        # Wire run button
        def _run_and_return(outputs):
            # small wrapper to unpack dict be returned to gradio outputs
            return outputs["cmd"], outputs["rc"], outputs["stdout"], outputs["stderr"]

        run_btn.click(
            fn=run_command,
            inputs=[
                sodlab_path,
                do_archive,
                do_transform,
                do_compile,
                archive_copy,
                archive_move,
                archive_hardlink,
                systems_checked,
                systems_custom_text,
                input_dir,
                output_dir,
                recursive,
                force_relative_paths,
                step,
                logfile,
                force,
                settings_path,
                ui_logfile_dir,
                dry_run,
            ],
            outputs=[cmd_preview, rc_out, stdout_out],
        )

        gr.Markdown(
            "### Tips\n"
            "- Use the `sodlab executable` field to point to `sodlab.exe` if it is not on PATH (e.g. `C:\\sodlab\\sodlab.exe`).\n"
            "- `--compile` is mutually exclusive with `--archive`/`--transform` (the UI will raise an error if you try to mix them).\n"
            "- If your systems use unusual tokens, add them in the 'Extra / custom systems' box separated by spaces or commas.\n"
            "- The UI writes a captured logfile only if you supply the 'Save UI-captured logfile to' folder.\n"
        )

    return demo


if __name__ == "__main__":
    app = create_ui()
    app.launch(share=False)
