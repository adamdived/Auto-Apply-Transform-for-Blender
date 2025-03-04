bl_info = {
    "name": "Auto Apply Scale",
    "author": "Your Name",
    "version": (1, 3),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Auto Apply Scale",
    "description": "Automatically applies transforms to objects after modification",
    "category": "Object",
}

import bpy
from bpy.app.handlers import persistent
import gpu
from gpu_extras.batch import batch_for_shader

# Track objects that have been processed to avoid infinite loops
processed_objects = set()

# For the status indicator
draw_handler = None

class AUTO_APPLY_SCALE_PT_panel(bpy.types.Panel):
    bl_label = "Auto Apply Transform"
    bl_idname = "AUTO_APPLY_SCALE_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Main toggle
        row = layout.row()
        row.prop(scene, "auto_apply_enabled", text="Auto Apply Transform")
        
        # Create a box for the options
        box = layout.box()
        col = box.column(align=True)
        
        # What to apply
        col.label(text="Apply:")
        row = col.row(align=True)
        row.prop(scene, "auto_apply_location", text="Location")
        row.prop(scene, "auto_apply_rotation", text="Rotation")
        row.prop(scene, "auto_apply_scale", text="Scale")
        
        # Axis-specific scale options
        if scene.auto_apply_scale:
            row = col.row(align=True)
            row.label(text="Scale Axes:")
            row = col.row(align=True)
            row.prop(scene, "auto_apply_scale_x", text="X")
            row.prop(scene, "auto_apply_scale_y", text="Y")
            row.prop(scene, "auto_apply_scale_z", text="Z")
        
        # Status indicator toggle
        col.separator()
        col.prop(scene, "auto_apply_show_indicator", text="Show Status Indicator")
        
        # Hotkey info
        if not scene.auto_apply_hotkey_registered:
            col.separator()
            col.operator("object.register_auto_apply_hotkey", text="Register Alt+A Hotkey")

class AUTO_OT_apply_transform(bpy.types.Operator):
    """Apply selected transformations to the active object"""
    bl_idname = "object.auto_apply_transform"
    bl_label = "Apply Transform"
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.mode == 'OBJECT'
        
    def execute(self, context):
        scene = context.scene
        active_obj = context.active_object
        
        if active_obj and (active_obj.type == 'MESH' or active_obj.type == 'CURVE' or 
                         active_obj.type == 'ARMATURE' or active_obj.type == 'EMPTY'):
            # Store the current selection state
            was_selected = active_obj.select_get()
            original_active = context.view_layer.objects.active
            
            # Determine what needs to be applied
            apply_loc = scene.auto_apply_location
            apply_rot = scene.auto_apply_rotation
            apply_scale = scene.auto_apply_scale
            
            # Check if there's anything to apply
            needs_apply = False
            
            # Check location
            if apply_loc and (active_obj.location.x != 0 or 
                             active_obj.location.y != 0 or 
                             active_obj.location.z != 0):
                needs_apply = True
                
            # Check rotation
            if apply_rot and (active_obj.rotation_euler.x != 0 or 
                             active_obj.rotation_euler.y != 0 or 
                             active_obj.rotation_euler.z != 0):
                needs_apply = True
                
            # Check scale (taking into account axis-specific options)
            if apply_scale:
                check_x = scene.auto_apply_scale_x and active_obj.scale.x != 1.0
                check_y = scene.auto_apply_scale_y and active_obj.scale.y != 1.0
                check_z = scene.auto_apply_scale_z and active_obj.scale.z != 1.0
                
                if check_x or check_y or check_z:
                    needs_apply = True
            
            # Only apply if something needs to be applied
            if needs_apply:
                # For axis-specific scale application
                if apply_scale and not (scene.auto_apply_scale_x and scene.auto_apply_scale_y and scene.auto_apply_scale_z):
                    # Save original scale
                    original_scale = active_obj.scale.copy()
                    
                    # Set scale to 1 for axes we don't want to apply
                    if not scene.auto_apply_scale_x:
                        active_obj.scale.x = 1.0
                    if not scene.auto_apply_scale_y:
                        active_obj.scale.y = 1.0
                    if not scene.auto_apply_scale_z:
                        active_obj.scale.z = 1.0
                    
                    # Apply transformation
                    bpy.ops.object.transform_apply(location=apply_loc, rotation=apply_rot, scale=apply_scale)
                    
                    # Restore scale for axes we didn't apply
                    if not scene.auto_apply_scale_x:
                        active_obj.scale.x = original_scale.x
                    if not scene.auto_apply_scale_y:
                        active_obj.scale.y = original_scale.y
                    if not scene.auto_apply_scale_z:
                        active_obj.scale.z = original_scale.z
                else:
                    # Apply transformation (all axes for scale)
                    bpy.ops.object.transform_apply(location=apply_loc, rotation=apply_rot, scale=apply_scale)
                
                # Force robust UI update by toggling selection
                # This trick helps ensure the transform UI updates properly
                active_obj.select_set(False)
                context.view_layer.update()
                active_obj.select_set(True)
                context.view_layer.update()
                
                # Force a redraw of the interface
                for window in bpy.context.window_manager.windows:
                    for area in window.screen.areas:
                        area.tag_redraw()
                
                # Schedule a timer to do another refresh after a very short delay
                # This helps catch cases where the UI needs more time to update
                bpy.app.timers.register(
                    lambda: refresh_ui() or None,
                    first_interval=0.1
                )
            
        return {'FINISHED'}

def refresh_ui():
    """Force a complete UI refresh"""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()
    return None  # Return None to prevent the timer from repeating

class AUTO_OT_toggle_enabled(bpy.types.Operator):
    """Toggle auto apply transform"""
    bl_idname = "object.toggle_auto_apply"
    bl_label = "Toggle Auto Apply Transform"
    
    def execute(self, context):
        context.scene.auto_apply_enabled = not context.scene.auto_apply_enabled
        return {'FINISHED'}

class AUTO_OT_register_hotkey(bpy.types.Operator):
    """Register the Alt+A hotkey for toggling auto apply"""
    bl_idname = "object.register_auto_apply_hotkey"
    bl_label = "Register Auto Apply Hotkey" 
    
    def execute(self, context):
        wm = context.window_manager
        kc = wm.keyconfigs.addon
        if kc:
            km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
            kmi = km.keymap_items.new(
                AUTO_OT_toggle_enabled.bl_idname, 
                type='A', 
                value='PRESS', 
                alt=True
            )
            context.scene.auto_apply_hotkey_registered = True
        return {'FINISHED'}

@persistent
def check_apply_transform(scene):
    # Skip if auto apply is disabled
    if not scene.auto_apply_enabled:
        return
        
    # Only proceed in Object Mode
    if bpy.context.mode != 'OBJECT':
        return
        
    active_obj = bpy.context.active_object
    if active_obj and active_obj.name not in processed_objects:
        # Check if there's anything to apply
        needs_apply = False
        
        # Check if any transformation needs to be applied based on settings
        if scene.auto_apply_location and any(abs(getattr(active_obj.location, axis)) > 0.0001 for axis in 'xyz'):
            needs_apply = True
            
        if scene.auto_apply_rotation and any(abs(getattr(active_obj.rotation_euler, axis)) > 0.0001 for axis in 'xyz'):
            needs_apply = True
            
        if scene.auto_apply_scale:
            check_x = scene.auto_apply_scale_x and abs(active_obj.scale.x - 1.0) > 0.0001
            check_y = scene.auto_apply_scale_y and abs(active_obj.scale.y - 1.0) > 0.0001
            check_z = scene.auto_apply_scale_z and abs(active_obj.scale.z - 1.0) > 0.0001
            if check_x or check_y or check_z:
                needs_apply = True
        
        # Only proceed if something needs to be applied
        if needs_apply:
            # Add to processed set to prevent loops
            processed_objects.add(active_obj.name)
            
            # Use the operator to apply transform
            bpy.ops.object.auto_apply_transform()
            
            # After a short delay, remove from processed set to allow future changes
            bpy.app.timers.register(
                lambda: processed_objects.discard(active_obj.name) or None, 
                first_interval=0.5
            )

def draw_status_indicator():
    if not bpy.context.scene.auto_apply_enabled or not bpy.context.scene.auto_apply_show_indicator:
        return
    
    # Get viewport dimensions
    region = bpy.context.region
    if not region:
        return
        
    # Set indicator position at top-left
    text_x, text_y = 20, region.height - 60
    
    # Prepare text
    text = "Auto Apply: ON"
    
    # Import BLF module
    import blf
    
    # Draw text with shadow for better visibility
    blf.size(0, 16)
    blf.enable(0, blf.SHADOW)
    blf.shadow(0, 5, 0.0, 0.0, 0.0, 0.8)
    blf.position(0, text_x, text_y, 0)
    blf.color(0, 1.0, 0.5, 0.0, 1.0)  # Orange color
    blf.draw(0, text)
    blf.disable(0, blf.SHADOW)

def register():
    bpy.types.Scene.auto_apply_enabled = bpy.props.BoolProperty(
        name="Auto Apply Transform",
        description="Automatically apply transformations after modifications",
        default=False,
        update=lambda self, context: refresh_ui()
    )
    
    bpy.types.Scene.auto_apply_location = bpy.props.BoolProperty(
        name="Apply Location",
        description="Apply location transformation",
        default=False,
    )
    
    bpy.types.Scene.auto_apply_rotation = bpy.props.BoolProperty(
        name="Apply Rotation",
        description="Apply rotation transformation",
        default=False,
    )
    
    bpy.types.Scene.auto_apply_scale = bpy.props.BoolProperty(
        name="Apply Scale",
        description="Apply scale transformation",
        default=True,
    )
    
    bpy.types.Scene.auto_apply_scale_x = bpy.props.BoolProperty(
        name="X",
        description="Apply scale on X axis",
        default=True,
    )
    
    bpy.types.Scene.auto_apply_scale_y = bpy.props.BoolProperty(
        name="Y",
        description="Apply scale on Y axis",
        default=True,
    )
    
    bpy.types.Scene.auto_apply_scale_z = bpy.props.BoolProperty(
        name="Z",
        description="Apply scale on Z axis",
        default=True,
    )
    
    bpy.types.Scene.auto_apply_show_indicator = bpy.props.BoolProperty(
        name="Show Status Indicator",
        description="Show a status indicator in the 3D viewport when auto apply is active",
        default=False,
    )
    
    bpy.types.Scene.auto_apply_hotkey_registered = bpy.props.BoolProperty(
        default=False
    )
    
    bpy.utils.register_class(AUTO_APPLY_SCALE_PT_panel)
    bpy.utils.register_class(AUTO_OT_apply_transform)
    bpy.utils.register_class(AUTO_OT_toggle_enabled)
    bpy.utils.register_class(AUTO_OT_register_hotkey)
    bpy.app.handlers.depsgraph_update_post.append(check_apply_transform)
    
    # Add the viewport indicator
    global draw_handler
    if draw_handler is None:
        draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            draw_status_indicator, (), 'WINDOW', 'POST_PIXEL')

def unregister():
    # Remove the viewport indicator
    global draw_handler
    if draw_handler:
        bpy.types.SpaceView3D.draw_handler_remove(draw_handler, 'WINDOW')
        draw_handler = None
    
    bpy.utils.unregister_class(AUTO_APPLY_SCALE_PT_panel)
    bpy.utils.unregister_class(AUTO_OT_apply_transform)
    bpy.utils.unregister_class(AUTO_OT_toggle_enabled)
    bpy.utils.unregister_class(AUTO_OT_register_hotkey)
    
    if check_apply_transform in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(check_apply_transform)
    
    del bpy.types.Scene.auto_apply_enabled
    del bpy.types.Scene.auto_apply_location
    del bpy.types.Scene.auto_apply_rotation
    del bpy.types.Scene.auto_apply_scale
    del bpy.types.Scene.auto_apply_scale_x
    del bpy.types.Scene.auto_apply_scale_y
    del bpy.types.Scene.auto_apply_scale_z
    del bpy.types.Scene.auto_apply_show_indicator
    del bpy.types.Scene.auto_apply_hotkey_registered
    
    # Clear the processed objects set
    processed_objects.clear()

if __name__ == "__main__":
    register()
