tk-shotgun-publishrenders
=========================

This app searches the directory structure of a project to find existing published files or file sequences, then registers them in Shotgun as published files if the published file objects don't already exist. It's not just for renders anymore, but that was the scope when I first made it. The app was adapted from tk-shotgun-folders for the overall structure, and its interface is similar.

Generally speaking, it should be installed into the **shotgun_shot** or **shotgun_asset** contexts, with each type of item you want to publish defined in a list. A typical dictionary item in the publishes list would look like this:

```
publishes:
- {published_file_type: Rendered Image, template_publish_comment: rendered_image_publish_comment,
  template_publish_file: shot_render_output, template_publish_name: rendered_image_publish_name}
```

The keys in the dictionary are as follows:

* **published_file_type:** *(string)* The *Published File Type* attribute as it will appear in Shotgun.
* **template_publish_comment:** *(string template)* Name of the template defining the structure of the Published File's *Description* field in Shotgun.
* **template_publish_file:** *(path template)* Name of the template defining the path structure we will search for existing files.
* **template_publish_name:** *(string template)* Name of the template defining what will go in the *Name* field in Shotgun.

All templates must be able to be resolved from the path.
