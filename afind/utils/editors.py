import os
import sys

def onen_in_editor(editor_title, editor_cmd, filenames):
    """
    :param: editor_title - string
    :param: editor_cmd   - string
    :param: filenames    - SearchResults instance
    """
    if len(filenames) > 15:
        msg = '\nDo you want to open {} files? [y/n]: '.format(len(filenames))
        if raw_input(msg).strip().lower() != 'y':
            return

    files = filenames.get_filenames(only_first_line=True)

    sys.stdout.write('@afind open: {}...\n'.format(editor_title))
    cmd = "echo {} | xargs {}".format(files, editor_cmd)
    os.system(cmd)
