# ------------------------ Add-on definition ------------------------

bl_info = {
    "name": "Safe Render",
    "author": "Guillaume Bonvin",
    "version": (1, 0),
    "blender": (3, 2, 0),
    "description": "Resumes animation rendering in case of crash",
    "warning": "",
    "doc_url": "",
    "category": "Render",
}


# ------------------------ Imports ------------------------

import bpy
from bpy.app.handlers import persistent
import subprocess
import datetime
import os
 
 
# ------------------------ Safe Render Operator ------------------------

class SafeRender(bpy.types.Operator):
    """Enables safe animation rendering"""
    bl_idname = "render.saferender"
    bl_label = "Safe Rendering"
    bl_description = "Allows blender to launch again and resume from last frame in case of crash while rendering an animation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    directoryPath = ""
    fileName = ""
    
    
    safe = False
    p = None
    
    def onLoad(self):
        self.directoryPath = bpy.path.abspath("//")
        self.fileName = bpy.path.basename(bpy.context.blend_data.filepath)
        self.checkStatus(self)
        SafeRenderPanel.update()
        
    def onFrame(self):
        if self.safe == False:
            return None
        renderedFrame = bpy.context.scene.frame_current
        self.writeTxt("\nRendered frame at: " + str(datetime.datetime.now()))
        self.writeTxt(str(renderedFrame))
        SafeRenderPanel.update()
        
    def onRenderDone(self):
        if self.safe == False:
            return None
        self.sendComplete()
        self.writeTxt("\n----------------------------------------------\nRender Job Completed at "+str(datetime.datetime.now()))
        return None

    def execute(self, context):
        if self.safe:
            subprocess.Popen.kill(SafeRender.p)
            SafeRender.safe = False
            bpy.app.timers.unregister(SafeRender.sendAlive)
            self.cleanBatch()
        else:
            if not os.path.isfile(self.directoryPath+"BlenderCrashRecovery.bat"):
                self.generateBatch()
            if not os.path.isfile(self.directoryPath+"RenderState.txt"):
                self.generateLog()
                
            SafeRender.p = subprocess.Popen(["BlenderCrashRecovery.bat",self.directoryPath, self.fileName],
                cwd=self.directoryPath,
                shell=False,
                close_fds=True,
                stdin=subprocess.PIPE)
                
            SafeRender.safe = True
            bpy.app.timers.register(SafeRender.sendAlive)
            
        print("Safe mode enabled: "+str(self.safe))
        SafeRenderPanel.update()

        return {'FINISHED'}
    
    def checkStatus(self):
        if not os.path.isfile(self.directoryPath+"BlenderCrashRecovery.bat"):
            return None
        frame = self.readTxt()
        # No file exists, new instance of blender
        if frame == None:
            print("no file found")
        else:
            self.resumeCrash(int(frame)+1)
        
        print("Status checked !")
        return None
    
    def resumeCrash(frame):
        bpy.context.scene.frame_set(frame)
        bpy.context.scene.frame_start = frame
        bpy.context.scene.render.use_lock_interface = True
        
        SafeRender.writeTxt("\n--------CRASH RECOVERY--------\nRestart at: " + str(datetime.datetime.now()) + "\nLast frame detected!\n" + str(frame-1))
        
        SafeRender.execute(SafeRender, bpy.context)
        
        bpy.ops.render.render('INVOKE_DEFAULT', animation=True)
    
    def sendAlive():
        print("1")
        
        return 2.0
    
    def sendComplete():
        print("2")
    
    def readTxt():
        try:
            with open(SafeRender.directoryPath+'RenderState.txt', 'r') as f:
                for line in f:
                    pass
                last_line = line
                f.close()
            return last_line
        
        except FileNotFoundError:
            return None
    
    def writeTxt(text):
        with open(SafeRender.directoryPath+'RenderState.txt', 'a') as f:
            f.write('\n'+text)
            f.close()
            
    def generateLog(self):
        SafeRender.writeTxt("New render job initiated at: "+str(datetime.datetime.now())+"\n-------------------------------------\n")
        startFrame = bpy.context.scene.frame_start
        SafeRender.writeTxt(str(startFrame-1))
                
    def generateBatch(self):
        with open(SafeRender.directoryPath+'BlenderCrashRecovery.bat', 'a') as f:
            f.write(
            '''@ECHO OFF
            set dirpath=%1
            set blendfile=%2
            :BEGIN
            CHOICE /N /C:123 /M "Waiting for communication..."%1  /T 5 /D 3
            IF ERRORLEVEL ==3 GOTO CRASH
            IF ERRORLEVEL ==2 GOTO OPT
            IF ERRORLEVEL ==1 GOTO ALIVE
            GOTO END

            :CRASH
            ECHO PROCESS FAILED - Launching new instance
            GOTO RUN

            :OPT
            ECHO Alternative option
            GOTO BEGIN

            :ALIVE
            ECHO Alive !
            GOTO BEGIN

            :END
            pause

            :RUN
            start "" "%dirpath%%blendfile%"'''
            )
            f.close()
            print("Batch file generated")
        
    def cleanBatch(self):
        bat = self.directoryPath+"BlenderCrashRecovery.bat"
        
        # remove batch
        if os.path.isfile(bat):
            os.remove(bat)
        else:
            print("Error: %s file not found" % bat)
            
        print("Cleaned")
    
    def cleanAll(self):
        log = self.directoryPath+"RenderState.txt"
        
        # remove Log
        if os.path.isfile(log):
            os.remove(log)
        else:
            print("Error: %s file not found" % log)
            
        # remove batch
        self.cleanBatch(self)
        SafeRenderPanel.update()
            
        print("Cleaned")


# ------------------------ Clean Operator ------------------------

class SafeRenderClean(bpy.types.Operator):
    """Enables safe animation rendering"""
    bl_idname = "render.saferenderclean"
    bl_label = "Safe Rendering"

    def execute(self, context):
        SafeRender.cleanAll(SafeRender)

        return {'FINISHED'}

# ------------------------ Visual UI ------------------------
     
class SafeRenderPanel(bpy.types.Panel):
    bl_idname = "RENDER_PT_saferender"
    bl_label = "Safe rendering"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    
    safe = SafeRender.safe
    jobstate=None
    
    def update():
        SafeRenderPanel.safe=SafeRender.safe
        SafeRenderPanel.checkState(SafeRenderPanel)
        return {'FINISHED'}
    
    def checkState(self):
        frame=SafeRender.readTxt()
        if frame == None:
            self.jobstate=None
        else:
            self.jobstate=int(frame)
 
    def draw(self, context):
        self.layout.label(text="Automatically resumes animation rendering in case of crash")
        row = self.layout.row()
        row.scale_y = 2.0
        
        if self.safe:
            row.operator("render.saferender", text="Cancel", icon='SEQUENCE_COLOR_01')
            self.layout.label(text="Your rendering is safe...", icon='GP_MULTIFRAME_EDITING')
            if self.jobstate == None:
                self.layout.label(text="You can now start rendering your animation !")
            else:
                self.layout.label(text="Next frame: "+str(self.jobstate+1))
        else:
            row.operator("render.saferender", text="Enable safe rendering")
            if not self.jobstate == None:
                self.layout.label(text="A reset point already exist. Resumes from frame "+str(self.jobstate+1), icon='INFO')
                self.layout.operator("render.saferenderclean", text="Clear reset point")
                


# ------------------------ Menu item ------------------------

def menu_func(self, context):
    self.layout.operator(SafeRender.bl_idname)


# ------------------------ Event Handlers ------------------------

@persistent
def load_handler(dummy):
    SafeRender.onLoad(SafeRender)
    
@persistent
def frame_handler(dummy):
    SafeRender.onFrame(SafeRender)

@persistent
def done_handler(dummy):
    SafeRender.onRenderDone(SafeRender)
    

bpy.app.handlers.load_post.append(load_handler)
bpy.app.handlers.render_write.append(frame_handler)
bpy.app.handlers.render_complete.append(done_handler)


# ------------------------ Registration ------------------------

CLASSES = [
    SafeRender,
    SafeRenderClean,
    SafeRenderPanel
]
    
def register():
    for cName in CLASSES:
        bpy.utils.register_class(cName)
    #bpy.app.handlers.save_post.append(SafeRender)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    for cName in CLASSES:
        bpy.utils.unregister_class(cName)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


# ------------------------ Main ------------------------   
 
if __name__ == "__main__":
    register()