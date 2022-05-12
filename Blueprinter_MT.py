bl_info = {
    "name": "Blueprinter",
    "author": "Shocik",
    "version": (1,0),
    "blender": (3, 0, 40),
    "location": "View3D > Sidebar > Misc" 
}

import bpy
import os
import math
import threading


class SetterOperator(bpy.types.Operator):
    """It set all of important variables."""
    bl_idname = "object.setter_operator"
    bl_label = "Set global variables"

    def execute(self, context):
        setter_button(context)
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(SetterOperator.bl_idname, text=SetterOperator.bl_label)


def setter_button(context):
        # enable variables
        bpy.context.scene.render.use_freestyle = True
        bpy.context.view_layer.freestyle_settings.as_render_pass = True
        bpy.context.view_layer.freestyle_settings.use_culling = True
        bpy.context.scene.render.image_settings.file_format = 'PNG'

        # compositor node - enable
        bpy.context.scene.use_nodes = True
        # blank nodes
        bpy.context.scene.node_tree.nodes.clear()
        # render layers set
        render_layer = bpy.context.scene.node_tree.nodes.new(type="CompositorNodeRLayers")
        render_layer.location = (-400, 0)
        # mix RGB set
        mix_RGB = bpy.context.scene.node_tree.nodes.new("CompositorNodeMixRGB")
        mix_RGB.location = (-100, 0)
        mix_RGB.inputs[2].default_value = (0, 0, 0, 1)
        # alpha over set
        alpha_over = bpy.context.scene.node_tree.nodes.new("CompositorNodeAlphaOver")
        alpha_over.location = (150, 0)
        alpha_over.use_premultiply = True
        alpha_over.inputs[0].default_value = 0
        alpha_over.inputs[2].default_value = (1, 1, 1, 1)
        # composite node set
        output_file = bpy.context.scene.node_tree.nodes.new(type="CompositorNodeOutputFile")
        if not bpy.context.scene.render.filepath.endswith("\\Blueprints\\"):
            bpy.context.scene.render.filepath = bpy.context.scene.render.filepath + "\\Blueprints\\"
        bpy.context.scene.node_tree.nodes['File Output'].base_path = bpy.context.scene.render.filepath
        output_file.location = (500, 0)
        # linking compositor nodes
        bpy.context.scene.node_tree.links.new(render_layer.outputs['Freestyle'], mix_RGB.inputs[1])
        bpy.context.scene.node_tree.links.new(mix_RGB.outputs[0], alpha_over.inputs[1])
        
        if not bpy.data.materials.get('Blueprint'):
            bpy.data.materials.new('Blueprint')
        material = bpy.data.materials['Blueprint']
            
        objects = bpy.context.scene.objects
        for obj in objects:
            if obj.type == 'MESH':
                obj.data.materials.append(material)
                obj.active_material = material
                obj.active_material.use_nodes = True
            elif obj.type == 'LIGHT':
                bpy.data.objects.remove(obj)
                    
        # making material
        material.use_nodes = True
        material.node_tree.nodes.clear()
        # emission shader
        emission = material.node_tree.nodes.new(type="ShaderNodeEmission")
        emission.location = (-300, 0)
        emission.inputs[0].default_value = (0, 0, 0, 1)
        emission.inputs[1].default_value = 0
        # output shader
        output = material.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
        output.location = (0,0)
        # link shaders
        material.node_tree.links.new(material.node_tree.nodes['Emission'].outputs[0], material.node_tree.nodes['Material Output'].inputs[0])
        bpy.context.scene.is_set = True
          
            
class RenderOperator(bpy.types.Operator):
    """Start render, but first check how long it will take.\n\nRender first time by yourself.\n\nEstimate time and then set avaliable variables up in panel, as you need."""
    bl_idname = "object.render_operator"
    bl_label = "Start render"

    def execute(self, context):
        val = render_button(context)
        if val == 'RESET':
            self.report({'ERROR'}, "Reset global variables, and do not change them")
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(RenderOperator.bl_idname, text=RenderOperator.bl_label)
    
    
def render_button(context):
    # validation 
    if (bpy.context.scene.render.use_freestyle == False or
        bpy.context.view_layer.freestyle_settings.as_render_pass == False or
        bpy.context.view_layer.freestyle_settings.use_culling == False or
        bpy.context.scene.use_nodes == False or 
        bpy.data.materials['Blueprint'].use_nodes == False or
        not (len(bpy.context.scene.node_tree.nodes) == 3 or len(bpy.context.scene.node_tree.nodes) == 4) or
        len(bpy.data.materials['Blueprint'].node_tree.nodes) != 2):
        bpy.context.scene.is_set = False        
        return 'RESET'
    
    shader_nodes = bpy.data.materials['Blueprint'].node_tree.nodes
    for node in shader_nodes:
        if not (node.name == 'Emission' or node.name == 'Material Output'):
            bpy.context.scene.is_set = False
            return 'RESET'
    
    compositor_nodes = bpy.context.scene.node_tree.nodes
    for node in compositor_nodes:
        if not (node.name == 'Alpha Over' or
            node.name == 'File Output' or
            node.name == 'Mix' or
            node.name == 'Render Layers'):
            bpy.context.scene.is_set = False
            return 'RESET'
    
    bpy.context.scene.is_rendering = True
    
    # reuse validation
    if len(bpy.context.scene.node_tree.nodes['File Output'].inputs) > 1:
        bpy.context.scene.node_tree.nodes.remove(bpy.context.scene.node_tree.nodes['File Output'])
        output_file = bpy.context.scene.node_tree.nodes.new(type="CompositorNodeOutputFile")
        bpy.context.scene.node_tree.nodes['File Output'].base_path = bpy.context.scene.render.filepath
        output_file.location = (500, 0)
    
    # first > last value validation
    if bpy.context.scene.start_value > bpy.context.scene.stop_value:
        tmp = bpy.context.scene.start_value
        bpy.context.scene.start_value = bpy.context.scene.stop_value
        bpy.context.scene.stop_value = tmp
        
    # first == last value validation    
    if bpy.context.scene.start_value == bpy.context.scene.stop_value:
        bpy.context.scene.steps = 1
        
    # thickness validation
    if bpy.context.scene.render_thickness == 0:
        bpy.context.scene.render.line_thickness = 0.1
    else:
        bpy.context.scene.render.line_thickness = bpy.context.scene.render_thickness    
        
    thread = threading.Thread(target=thread_menager)    
    thread.start()
    
        
def thread_menager():
    output_alpha = bpy.context.scene.node_tree.nodes['Alpha Over'].outputs[0]
    node_tree = bpy.context.scene.node_tree
    
    path = bpy.context.scene.render.filepath
    crease_value = bpy.context.scene.start_value
    
    # enable engine settings
    if bpy.context.scene.use_cycles:
        bpy.context.scene.render.engine = 'CYCLES'
        if bpy.context.scene.use_gpu:
            bpy.context.scene.cycles.device = 'GPU'
        else:
            bpy.context.scene.cycles.device = 'CPU'
    else:
         bpy.context.scene.render.engine = 'BLENDER_EEVEE' 
         
    if bpy.context.scene.steps > 1:
        step = (bpy.context.scene.stop_value - crease_value) / (bpy.context.scene.steps - 1)
    else:
        step = 0
    
    for i in range(bpy.context.scene.steps):
        inputs = node_tree.nodes['File Output'].inputs
        for link in output_alpha.links:
            for input in inputs:
                if link.to_socket == input:
                    node_tree.links.remove(link)
        bpy.context.view_layer.freestyle_settings.crease_angle = math.radians(crease_value + i * step)
        node_tree.nodes['File Output'].file_slots.new(str(round((crease_value + i * step), 2)).replace(".","_") +"_")
        node_tree.links.new(node_tree.nodes['Alpha Over'].outputs[0], node_tree.nodes['File Output'].inputs[1 + i])
        
        thread = threading.Thread(target = rendering_thread)
        thread.start()
        thread.join()
    bpy.context.scene.is_rendering = False
    
    
def rendering_thread():
    bpy.ops.render.render(write_still = True)
    return    


class BlueprintPanel(bpy.types.Panel):
    bl_idname = 'SCENE_PT_BP'
    bl_label = 'Blueprint'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        
        cycles = layout.row()
        cycles.prop(scene, "use_cycles", text = "CYCLES")
        
        gpu = layout.row()
        gpu.prop(scene, "use_gpu", text = "GPU")
        
        setter_button = layout.row()
        setter_button.operator("object.setter_operator")
        
        layout.label(text = "Crease angle value on:")
        sta = layout.row()
        sta.prop(scene, "start_value", text = "First frame")
        sto = layout.row()
        sto.prop(scene, "stop_value", text = "Last frame")
        
        ste = layout.row()
        ste.prop(scene, "steps", text = "Amount of steps")
        
        thick = layout.row()
        thick.prop(scene, "render_thickness", text = "Thickness")

        render_button = layout.row()
        render_button.scale_y = 2.0
        render_button.operator("object.render_operator")
        
        if bpy.context.scene.is_set == False or bpy.context.scene.is_rendering == True:
            render_button.enabled = False   
            
        if bpy.context.scene.use_cycles:
            gpu.enabled = True
        else:
            gpu.enabled = False
        
        if bpy.context.scene.is_rendering == True:
            setter_button.enabled = False
            sta.enabled = False
            sto.enabled = False
            ste.enabled = False
            thick.enabled = False
            cycles.enabled = False
            gpu.enabled = False
            
        if bpy.context.scene.is_rendering == False:
            setter_button.enabled = True
            sta.enabled = True
            sto.enabled = True
            ste.enabled = True
            thick.enabled = True
            cycles.enabled = True
            if bpy.context.scene.use_cycles:
                gpu.enabled = True
            else:
                gpu.enabled = False


def register():
    bpy.utils.register_class(BlueprintPanel)
    bpy.utils.register_class(SetterOperator)
    bpy.utils.register_class(RenderOperator)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.Scene.start_value = bpy.props.FloatProperty(default=120, min = 0, max = 180)
    bpy.types.Scene.stop_value = bpy.props.FloatProperty(default = 150, min = 0, max = 180)
    bpy.types.Scene.steps = bpy.props.IntProperty(default = 10, min = 1, max = 50)
    bpy.types.Scene.render_thickness = bpy.props.FloatProperty(default = 1, min = 0)     
    bpy.types.Scene.is_set = bpy.props.BoolProperty(default = False)
    bpy.types.Scene.is_rendering = bpy.props.BoolProperty(default = False)
    bpy.types.Scene.use_cycles = bpy.props.BoolProperty(
        description = "Use it to render big projects.\nEEVEE is good enough to draw few lines.",
        default = False,)
    bpy.types.Scene.use_gpu = bpy.props.BoolProperty(
        description = "Use it if your GPU is strong,\notherwise this will elongate render process",
        default = False)
         
            
def unregister():
    bpy.utils.unregister_class(BlueprintPanel)
    bpy.utils.unregister_class(SetterOperator)
    bpy.utils.unregister_class(RenderOperator)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
    register()
