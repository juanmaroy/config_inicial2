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
import maya.mel as mel

import tank
from tank import Hook
from tank import TankError

class PrePublishHook(Hook):
    """
    Single hook that implements pre-publish functionality
    """
    def execute(self, tasks, work_template, progress_cb, user_data, **kwargs):
        """
        Main hook entry point
        :param tasks:           List of tasks to be pre-published.  Each task is be a
                                dictionary containing the following keys:
                                {
                                    item:   Dictionary
                                            This is the item returned by the scan hook
                                            {
                                                name:           String
                                                description:    String
                                                type:           String
                                                other_params:   Dictionary
                                            }

                                    output: Dictionary
                                            This is the output as defined in the configuration - the
                                            primary output will always be named 'primary'
                                            {
                                                name:             String
                                                publish_template: template
                                                tank_type:        String
                                            }
                                }

        :param work_template:   template
                                This is the template defined in the config that
                                represents the current work file

        :param progress_cb:     Function
                                A progress callback to log progress during pre-publish.  Call:

                                    progress_cb(percentage, msg)

                                to report progress to the UI

        :param user_data:       A dictionary containing any data shared by other hooks run prior to
                                this hook. Additional data may be added to this dictionary that will
                                then be accessible from user_data in any hooks run after this one.

        :returns:               A list of any tasks that were found which have problems that
                                need to be reported in the UI.  Each item in the list should
                                be a dictionary containing the following keys:
                                {
                                    task:   Dictionary
                                            This is the task that was passed into the hook and
                                            should not be modified
                                            {
                                                item:...
                                                output:...
                                            }

                                    errors: List
                                            A list of error messages (strings) to report
                                }
        """
        results = []

        # validate tasks:
        for task in tasks:
            item = task["item"]
            output = task["output"]
            errors = []

            # report progress:
            progress_cb(0, "Validating", task)

            # pre-publish ALEMBIC CACHE output
            if output["name"] == "alembic_cache":
                errors.extend(self.__validate_item_for_alembic_cache_publish(item))
            # pre-publish RENDER output
            elif output["name"] == "rendered_image":
                errors.extend(self.__validate_item_for_rendered_image_publish(item))
            # pre-publish CAMERA output
            elif output["name"] == "camera":
                errors.extend(self.__validate_item_for_camera(item))
            else:
                # don't know how to publish this output types!
                errors.append("Don't know how to publish this item!")

            # if there is anything to report then add to result
            if len(errors) > 0:
                # add result:
                results.append({"task":task, "errors":errors})

            progress_cb(100)

        return results

    def __validate_item_for_alembic_cache_publish(self, item):
        """
        Validate that the item is valid to be exported to an alembic cache

        :param item:    The item to validate
        :returns:       A list of any errors found during validation that should be reported
                        to the artist
        """
        errors = []

        # check that the AbcExport command is available!
        if not mel.eval("exists \"AbcExport\""):
            errors.append("Could not find the AbcExport command needed to publish Alembic caches!")

        # check that there is still geometry in the scene:
        if not cmds.ls(geometry=True, noIntermediate=True):
            errors.append("The scene does not contain any geometry!")

        # Esta parte viene del tutorial de Alembic
        # check that the group still exists:
        if not cmds.objExists(item["name"]):
            errors.append("This group couldn't be found in the scene!")

        # and that it still contains meshes:
        elif not cmds.ls(item["name"], dag=True, type="mesh"):
            errors.append("This group doesn't appear to contain any meshes!")

        # finally return any errors
        return errors

    # validate rendered images...
    def __validate_item_for_rendered_image_publish(self, item):

        """
        Validate that the item is valid to be exported as a rendered image

        :param item:    The item to validate
        :returns:       A list of any errors found during validation
        """

        # add error checking here. here you can validate the rendered images in
        # whatever way you need to. right number of frames, no missing frames,
        # able to generate a thumbnail, all expected layers present, whatever
        # else you need.
        errors = []

        # Se puede comprobar que:
        # All frames exist
        # File sizes are consistent
        # Permissions are correct
        # Secondary files exist (thumbnails or quicktimes, for example)

        # finally return any errors
        return errors
        
    def __validate_item_for_camera(self, item):
        """
        Validate that the item is valid to be exported to a camera

        :param item:    The item to validate
        :returns:       A list of any errors found during validation

        """

        # add error checking here!
        errors = []

        return errors
