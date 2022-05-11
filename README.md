# Blueprinter
Blender addon to automatic render blueprints.
User have to set up camera and directory path.

At the beggining press button on top of the panel, to set global variables. 
**This action will remove from scene all LIGHT-type objects.**

Second step is set up variables avaliable in panel.
It have few limits. You can easily change limits in source code, 212-218 lines are responsible for this limits.

When everything is setted up, press "Start render" button.
This addon do a lot of single renders, so result files names will be all ends on 0001.
Crease angle (start and stop value) is static in time, and user can't set keyframes for it.
