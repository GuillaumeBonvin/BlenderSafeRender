# BlenderSafeRender

This is a simple addon for blender which prevents time loss during long animation rendering, due to crashes.
It simply works by creating a subprocess checking if Blender is still alive. In case of crash, communication is interrupted and blender is automatically reopened, and rendering is resumed from the last rendered frame.
This addon also generates a simple log file showing each frame's render DateTime as well as crashes and time completion.
