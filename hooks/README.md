
# Hooks

V.Percuoco 11/20/2025

Note: These 'hooks' are references to resources Gradio uses at runtime. Pyinstaller has issues finding them when building an executable so we are explicitly listing them here.

They are python modules which pyinstaller will collect and store in the executable output build package.

In the future if a FileNotFound error occurs when starting up the .exe, it typically means a library reference is missing here.

