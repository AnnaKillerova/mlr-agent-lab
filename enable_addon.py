import addon_utils
import bpy

addon_utils.enable("blender_mcp", default_set=True, persistent=True)
print("ENABLED_MODULES:", [m.__name__ for m in addon_utils.modules() if m.bl_info.get("name", "").startswith("MCP")])
print("PREF_ENABLED:", bpy.context.preferences.addons.get("blender_mcp") is not None)

bpy.ops.wm.save_userpref()
print("PREFS_SAVED")
