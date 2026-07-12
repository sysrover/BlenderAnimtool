import bpy

bpy.ops.preferences.addon_enable(module="bld_remote_mcp")
import bld_remote_mcp

bld_remote_mcp.start_mcp_service()
