"""

App that creates published file entities from image sequences on disk, from inside of Shotgun.

"""
import sgtk
import tank
from tank.platform import Application


class PublishRenders(Application):
    
    def init_app(self):

        deny_permissions = self.get_setting("deny_permissions")
        deny_platforms = self.get_setting("deny_platforms")
        
                
        p = {
            "title": "Publish Files",
            "deny_permissions": deny_permissions,
            "deny_platforms": deny_platforms,
            "supports_multiple_selection": True
        }
        
        self.engine.register_command("publish_renders", self.publish_files, p)
        
        p = {
            "title": "Preview Publish Files",
            "deny_permissions": deny_permissions,
            "deny_platforms": deny_platforms,
            "supports_multiple_selection": True
        }
        
        self.engine.register_command("preview_publish", self.preview_publish_files, p)
        
        """ Define templates:
            self.templates is a list of dictionaries.
            dictionary entries:
            self.templates[x]['publish_file']    : template object for filenames we'll be publishing
            self.templates[x]['publish_name']    : template object for 'name' field in shotgun, to group the files in the loader
            self.templates[x]['publish_comment'] : template object for 'comment' field (description) in shotgun
            self.templates[x]['file_type']       : name of published file type for loader hooks
        """
        
        publishes = self.get_setting("publishes")
        self.templates = []
        for publish in publishes:
            self.templates += [
                                {'publish_file': self.tank.templates[publish['template_publish_file']],
                                'publish_name': self.tank.templates[publish['template_publish_name']],
                                'publish_comment': self.tank.templates[publish['template_publish_comment']],
                                'file_type':publish['published_file_type']}
            ]
        
    def _add_plural(self, word, items):
        """
        appends an s if items > 1
        """
        if items > 1:
            return "%ss" % word
        else:
            return word

    def preview_publish_files(self, entity_type, entity_ids):
        
        if len(entity_ids) == 0:
            self.log_info("No entities specified!")
            return
        
        
        try:
            paths = []
            for template in self.templates:
                paths += self._find_renders(template['publish_file'],entity_type, entity_ids)
            
        
        except tank.TankError, tank_error:
            # tank errors are errors that are expected and intended for the user
            self.log_error(tank_error)
        
        except Exception, error:
            # other errors are not expected and probably bugs - here it's useful with a callstack.
            self.log_exception("Error when previewing folders!")
        
        else:            
            # success! report back to user
            if len(paths) == 0:
                self.log_info("<b>No Publishes would be registered for this item!</b>")
    
            else:
                self.log_info("<b>Publishing Files would register %d Published Files on Shotgun:</b>" % len(paths))
                self.log_info("")
                for p in paths:
                    self.log_info(p)
                self.log_info("")
                self.log_info("Note that some of these files may be registered on Shotgun already.")


    def publish_files(self, entity_type, entity_ids):

        if len(entity_ids) == 0:
            self.log_info("No entities specified!")
            return

        entities_processed = 0
        entities_skipped = 0


        try:

            for template in self.templates:
                paths = self._find_renders(template['publish_file'], entity_type, entity_ids)
                
                entities_processed += len(paths)

                
                for path in paths:
                    if len(sgtk.util.find_publish(self.tank,[str(path)])) > 0:
                        entities_skipped += 1
                    else:
                        fields = template['publish_file'].get_fields(path)
                            
                        # construct kwargs for registration.
                        try:
                            comment = template['publish_comment'].apply_fields(fields)
                            publishName = template['publish_name'].apply_fields(fields)
                        except:
                            raise self.tank.TankError("Failed to apply fields to publish templates!")
                        else:
                            kwargs = {
                                "tk": self.tank,
                                "context": self.tank.context_from_path(path),
                                "comment": comment,
                                "path": path,
                                "name": publishName,
                                "version_number": fields['version'],
                                "published_file_type":template['file_type']
                            }
                            # Other potential kwargs could be "thumbnail_path" but it is probably a lot of work to get that added for now.
                            
                            # register publish;
                            publish = sgtk.util.register_publish(**kwargs)
                        

        except tank.TankError, tank_error:
            # tank errors are errors that are expected and intended for the user
            self.log_error(tank_error)

        except Exception, error:
            # other errors are not expected and probably bugs - here it's useful with a callstack.
            self.log_exception("Error when registering Published Files! %s" % error)

        else:
            # report back to user
            self.log_info("%d %s processed - "
                         "Processed %d sequences on disk.\n%d were already registered and were skipped." % (len(entity_ids), 
                                                            self._add_plural(entity_type, len(entity_ids)), 
                                                            entities_processed, entities_skipped))

    def _find_renders(self, template, entity_type, entity_ids):
        """
        template: sg template object to search for
        entity_type: string, should be 'Shot' or 'Asset'
        entity_ids: List of Shotgun IDs
        """
        
        entity_names = []
        for entity_id in entity_ids:
            entity = self.tank.shotgun.find_one(entity_type,[['id','is',entity_id]],['id','code'])
            entity_names.append(entity['code'])

        output_paths = []
        for entity_name in entity_names:
                # Do this because abstract_paths_from_template() returns results if the path exists but not the file.
                paths = self.tank.paths_from_template(template, {entity_type:entity_name})
                for path in paths:
                    # Get fields for each result to search validated fields.
                    path_fields = template.get_fields(path)
                    # Remove abstract fields from path_fields so we only get the number of results we want.
                    for key in template.keys:
                        if template.keys[key].is_abstract:
                            path_fields.pop(key,None)
                    
                    abstract_paths = self.tank.abstract_paths_from_template(template, path_fields)
                    # If abstract path is already in output list then we skip it.
                    for abstract_path in abstract_paths:
                        if not abstract_path in output_paths:
                            output_paths += [abstract_path]

        output_paths.sort()
        return output_paths