# -*- coding: utf-8 -*-
# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import maya.cmds as cmds

import tank
from tank import Hook
from tank import TankError

class ScanSceneHook(Hook):
    """
    Hook to scan scene for items to publish
    """

    def execute(self, **kwargs):
        """
        Main hook entry point
        :returns:       A list of any items that were found to be published.
                        Each item in the list should be a dictionary containing
                        the following keys:
                        {
                            type:   String
                                    This should match a scene_item_type defined in
                                    one of the outputs in the configuration and is
                                    used to determine the outputs that should be
                                    published for the item

                            name:   String
                                    Name to use for the item in the UI

                            description:    String
                                            Description of the item to use in the UI

                            selected:       Bool
                                            Initial selected state of item in the UI.
                                            Items are selected by default.

                            required:       Bool
                                            Required state of item in the UI.  If True then
                                            item will not be deselectable.  Items are not
                                            required by default.

                            other_params:   Dictionary
                                            Optional dictionary that will be passed to the
                                            pre-publish and publish hooks
                        }
        """

        items = []

        # get the main scene:
        scene_name = cmds.file(query=True, sn=True)
        if not scene_name:
            raise TankError("Please Save your file before Publishing")

        scene_path = os.path.abspath(scene_name)
        name = os.path.basename(scene_path)

        # create the primary item - this will match the primary output 'scene_item_type':
        items.append({"type": "work_file", "name": name})

        # if there is any geometry in the scene (poly meshes or nurbs patches), then
        # add a geometry item to the list:
        if cmds.ls(geometry=True, noIntermediate=True):
            items.append({"type":"geometry", "name":"All Scene Geometry"})

        # Modificacion para publicar CAMARAS
        # look for cameras to publish
        for camera in cmds.listCameras(perspective=True):
            # aqui meter la condicion de que esten marcadas como renderable
            items.append({"type": "camera", "name": camera})

        # Modificacion para publicar ALEMBIC
        # look for root level groups that have meshes as children:
        for grp in cmds.ls(assemblies=True, long=True):
            if cmds.ls(grp, dag=True, type="mesh"):
                # include this group as a 'mesh_group' type
                items.append({"type":"mesh_group", "name":grp})

        # Modificacion para publicar RENDER
        # we'll use the engine to get the templates
        engine = tank.platform.current_engine()

        # get the current app
        app = self.parent

        # look up the template for the work file in the configuration
        # will get the proper template based on context (Asset, Shot, etc)
        work_template = app.get_template("template_work")
        work_template_fields = work_template.get_fields(scene_name)
        version = work_template_fields["version"]

        # get all the secondary output render templates and match them against
        # what is on disk
        secondary_outputs = app.get_setting("secondary_outputs")
        render_outputs = [out for out in secondary_outputs if out["tank_type"] == "Rendered Image"]
        for render_output in render_outputs:

            # AQUI ESTA EL ERROR!!!!
            # render_template = app.get_template(render_output["publish_template"])

            # Copiado del blog Two guys and a Toolkit
            # Es una forma tosca de resolverlo
            # se supone que lo anterior es mas elaborado
            render_template = engine.tank.templates.get("maya_shot_render")

            # now look for rendered images. note that the cameras returned from
            # listCameras will include full DAG path. You may need to account
            # for this in your, more robust solution, if you want the camera name
            # to be part of the publish path. For my simple test, the cameras
            # are not parented, so there is no hierarchy.

            # iterate over all cameras and layers
            for camera in cmds.listCameras():
                for layer in cmds.ls(type="renderLayer"):

                    # apparently maya has 2 names for the default layer. I'm
                    # guessing it actually renders out as 'masterLayer'.
                    layer = layer.replace("defaultRenderLayer", "masterLayer")

                    # these are the fields to populate into the template to match
                    # against
                    fields = {
                        'maya.camera_name': camera,
                        'maya.layer_name': layer,
                        # codigo original:
                        # 'name': layer,
                        # 'name': name.version
                        # 'name': os.path.splitext(name)[0],
                        'name': name.split('.')[0],
                        # si pongo 'name' en lugar de 'layer' da error
                        # <Sgtk StringKey name> Illegal value 'scene.v008.ma' does not fit filter_by 'alphanumeric'
                        'version': version,
                    }

                    # match existing paths against the render template
                    paths = engine.tank.abstract_paths_from_template(
                        render_template, fields)

                    # if there's a match, add an item to the render
                    if paths:
                        items.append({
                            "type": "rendered_image",
                            # OJO OJO OJO     HE CAMBIADO PARA PROBAR     OJO OJO OJO
                            # "name": layer,
                            "name": camera+"_"+layer+"_"+os.path.splitext(name)[0],
                            # Ahora aparece en el menu de publicacion
                            # el nombre del fichero como identificador de la capa
                            # para elegir cuales se publican

                            # since we already know the path, pass it along for
                            # publish hook to use
                            "other_params": {
                                # just adding first path here. may want to do some
                                # additional validation if there are multiple.
                                'path': paths[0],
                            }
                        })

        return items
