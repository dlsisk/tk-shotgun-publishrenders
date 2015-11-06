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
            "title": "Publish Rendered Images",
            "deny_permissions": deny_permissions,
            "deny_platforms": deny_platforms,
            "supports_multiple_selection": True
        }
        
        self.engine.register_command("publish_renders", self.publish_renders, p)
        
        p = {
            "title": "Preview Publish Rendered Images",
            "deny_permissions": deny_permissions,
            "deny_platforms": deny_platforms,
            "supports_multiple_selection": True
        }
        
        self.engine.register_command("preview_publish", self.preview_publish_renders, p)
    
    def _add_plural(self, word, items):
        """
        appends an s if items > 1
        """
        if items > 1:
            return "%ss" % word
        else:
            return word

    def preview_publish_renders(self, entity_type, entity_ids):
        
        if len(entity_ids) == 0:
            self.log_info("No entities specified!")
            return
        
        
        try:
            paths = self._find_renders(entity_type, entity_ids)
            
        
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
                self.log_info("<b>Publishing Rendered Images would register %d Published Files on Shotgun:</b>" % len(paths))
                self.log_info("")
                for p in paths:
                    self.log_info(p)
                self.log_info("")
                self.log_info("Note that some of these files may be registered on Shotgun already.")


    def publish_renders(self, entity_type, entity_ids):

        if len(entity_ids) == 0:
            self.log_info("No entities specified!")
            return

        entities_processed = 0
        entities_skipped = 0


        try:
            paths = self._find_renders(entity_type, entity_ids)
            
            entities_processed = len(paths)

            template_sg_publish_name = self.tank.templates[self.get_setting("template_sg_publish_name")]
            template_sg_publish_comment = self.tank.templates[self.get_setting("template_sg_publish_comment")]
            template_rendered_image = self.tank.templates[self.get_setting("template_rendered_image")]
            
            for path in paths:
                if len(sgtk.util.find_publish(self.tank,[str(path)])) > 0:
                    entities_skipped += 1
                else:
                    fields = template_rendered_image.get_fields(path)
                    
                    # construct kwargs for registration.
                    try:
                        comment = template_sg_publish_comment.apply_fields(fields)
                        publishName = template_sg_publish_name.apply_fields(fields)
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
                            "published_file_type":'Rendered Image'
                        }
                        # Other potential kwargs could be "thumbnail_path" but it is probably a lot of work to get that added for now.
                        
                        # register publish;
                        publish = sgtk.util.register_publish(**kwargs)
                    

        except tank.TankError, tank_error:
            # tank errors are errors that are expected and intended for the user
            self.log_error(tank_error)

        except Exception, error:
            # other errors are not expected and probably bugs - here it's useful with a callstack.
            self.log_exception("Error when creating folders!")

        else:
            # report back to user
            self.log_info("%d %s processed - "
                         "Processed %d sequences on disk.\n%d were already registered and were skipped." % (len(entity_ids), 
                                                            self._add_plural(entity_type, len(entity_ids)), 
                                                            entities_processed, entities_skipped))

    def _find_renders(self, entity_type, entity_ids):

        template_rendered_image = self.tank.templates[self.get_setting("template_rendered_image")]
        
        entity_names = []
        for entity_id in entity_ids:
            entity = self.tank.shotgun.find_one(entity_type,[['id','is',entity_id]],['id','code'])
            entity_names.append(entity['code'])

        paths = []
        for entity_name in entity_names:
                paths += self.tank.abstract_paths_from_template(template_rendered_image, {entity_type:entity_name})
        return paths