from matplotlib import interactive
import gradio as gr
import os
import importlib
import iodp
import pandas as pd
import json


systems_graph = {}

def get_laboratories():
    return systems_graph.keys()


def get_system_types(laboratory):
    print(laboratory)
    items = systems_graph.get(laboratory, [])
    print(items)
    return gr.update(choices=items.keys(), value=items[0] if items else None)


def get_instrument_files(laboratory, system):
    
    items = systems_graph[laboratory].get(system,[])
    return gr.update(choices=items, value=items[0] if items else None)
    
    
def clear_files_dropdown(_):
    return gr.update(choices=[], value=None)


def main():
    # Gradio UI
    with gr.Blocks() as demo:
        gr.Markdown("# SOD-Laboratory File Converter")

        with gr.Row():
            laboratory_dropdown = gr.Dropdown(label="Laboratory", choices = get_laboratories(), interactive=True)
            systems_dropdown = gr.Dropdown(label='Analyses')
           # files_dropdown = gr.Dropdown(label='Files', multiselect=True, interactive=True)


        # Events
        laboratory_dropdown.change(fn=get_system_types, inputs=[laboratory_dropdown], outputs=systems_dropdown)
       # systems_dropdown.change(fn=get_instrument_files, inputs=[laboratory_dropdown, systems_dropdown], outputs=files_dropdown)
        #files_dropdown.change(fn=get_instrument_files, inputs=[systems_dropdown], outputs=files_dropdown)
        
        #laboratory_dropdown.change(
         #   fn=clear_files_dropdown,
          #  inputs=[laboratory_dropdown],
          #  outputs=files_dropdown
#)


    demo.launch()



if __name__ == "__main__":
    with open("UI/systems.json", "r") as f:
        config = json.load(f)
        
    systems_graph = config
    
    print(systems_graph)
    main()