from application.helpers import parse
from application.modules.job_types import get_job_type_paths


class TaskCompiler:
    def __init__(self):
        pass

    @staticmethod
    def compile(task, add_file=None, worker=None):

        paths = get_job_type_paths('blender_resume_render', worker)

        def _compile_blender_render(cmd_settings):
            """Build the blender render command. Strings that are checked for remapping are:
            - blender_cmd
            - filepath
            - render_output
            """

            # Check if a command has been defined, or use the default definition.
            try:
                blender_cmd = cmd_settings['blender_cmd']
            except KeyError:
                blender_cmd = '{blender_render}'
            # Do path remapping
            blender_cmd = blender_cmd.format(**paths)

            # Parse the file path. This property is required, so we crash if not set.
            filepath = cmd_settings['filepath']
            # Do path remapping
            filepath = filepath.format(**paths)

            # render_output is always required for render_resume
            render_output = cmd_settings['render_output']
            # Do path remapping
            render_output = render_output.format(**paths)

            cmd = [
                blender_cmd,
                '--enable-autoexec',
                '-noaudio',
                '--background',
                filepath,
                '--render-output',
                render_output,
                '--render-format',
                cmd_settings['format']
            ]

            # TODO: handle --python script path
            cmd += parse(cmd_settings['frames'])

            # special options for resume render
            cmd += [
                '--',
                '--cycles-resumable-num-chunks',
                str(cmd_settings['cycles_num_chunks']),
                '--cycles-resumable-current-chunk',
                str(cmd_settings['cycles_chunk']),
                ]

            return cmd

        def _compile_image_convert(cmd_settings):
            """Build the imagemagick convert command. Strings that are checked for remapping are:
            - convert_cmd
            - input_image
            - output_imagee
            """
            # Check if a command has been defined, or use the default definition.
            try:
                convert_cmd = cmd_settings['convert_cmd']
            except KeyError:
                convert_cmd = '{imagemagick_convert}'

            input_image = cmd_settings['input_image']
            output_image = cmd_settings['output_image']

            # Do path remapping
            convert_cmd = convert_cmd.format(**paths)
            input_image = input_image.format(**paths)
            output_image = output_image.format(**paths)

            cmd = [
                convert_cmd,
                input_image,
                output_image,
                ]

            return cmd

        def _compile_image_merge(cmd_settings):
            """Build the imagemagick merge command. Strings that are checked for remapping are:
            - convert_cmd
            - input_image_render
            - input_image_merge
            - output_image_merge
            """
            # Check if a command has been defined, or use the default definition.
            try:
                convert_cmd = cmd_settings['convert_cmd']
            except KeyError:
                convert_cmd = '{imagemagick_convert}'

            input_image_render = cmd_settings['input_image_render']
            input_image_merge = cmd_settings['input_image_merge']
            output_image_merge = cmd_settings['output_image_merge']

            # Do path remapping
            convert_cmd = convert_cmd.format(**paths)
            input_image_render = input_image_render.format(**paths)
            input_image_merge = input_image_merge.format(**paths)
            output_image_merge = output_image_merge.format(**paths)

            # calculate the contributions of the individual images
            cycles_chunk = cmd_settings['cycles_chunk']
            factor = 1.0 / cycles_chunk

            cmd = [
                convert_cmd,
                input_image_render,
                '-evaluate',
                'Multiply',
                "{0:4.2f}".format(factor),
                input_image_merge,
                '-evaluate',
                'Multiply',
                "{0:4.2f}".format(1.0 - factor),
                '-evaluate-sequence',
                'add',
                output_image_merge,
                ]

            return cmd

        def _compile_move_file(cmd_settings):
            """Move a file. Strings that are checked for remapping are:
            - input_file
            - output_file
            """
            # Parse the file patha. These property are required, so we crash if not set.
            input_file = cmd_settings['input_file']
            output_file = cmd_settings['output_file']
            # Do path remapping
            input_file = input_file.format(**paths)
            output_file = output_file.format(**paths)

            # Check if a command has been defined, or use the default definition.
            try:
                move_cmd = cmd_settings['move_cmd']
            except KeyError:
                move_cmd = '{move_file}'

            # Do path remapping
            move_cmd = move_cmd.format(**paths)

            cmd = [
                move_cmd,
                input_file,
                output_file,
                ]

            return cmd

        def _compile_copy_file(cmd_settings):
            """Copy a file. Strings that are checked for remapping are:
            - input_file
            - output_file
            """
            # Parse the file patha. These property are required, so we crash if not set.
            input_file = cmd_settings['input_file']
            output_file = cmd_settings['output_file']
            # Do path remapping
            input_file = input_file.format(**paths)
            output_file = output_file.format(**paths)

            # Check if a command has been defined, or use the default definition.
            try:
                copy_cmd = cmd_settings['copy_cmd']
            except KeyError:
                copy_cmd = '{copy_file}'

            # Do path remapping
            copy_cmd = copy_cmd.format(**paths)

            cmd = [
                copy_cmd,
                input_file,
                output_file,
                ]

            return cmd

        def _compile_delete_file(cmd_settings):
            """Delete a file. Strings that are checked for remapping are:
            - filepath
            """
            # Parse the file path. These property are required, so we crash if not set.
            filepath = cmd_settings['filepath']
            # Do path remapping
            filepath = filepath.format(**paths)

            # Check if a command has been defined, or use the default definition.
            try:
                delete_cmd = cmd_settings['delete_cmd']
            except KeyError:
                delete_cmd = '{delete_file}'

            # Do path remapping
            delete_cmd = delete_cmd.format(**paths)

            cmd = [
                delete_cmd,
                filepath,
                ]

            return cmd

        command_map = {
            'blender_render': _compile_blender_render,
            'copy_file': _compile_copy_file,
            'delete_file': _compile_delete_file,
            'imagemagick_convert': _compile_image_convert,
            'imagemagick_merge': _compile_image_merge,
            'move_file': _compile_move_file,
        }

        commands = []

        for command in task['commands']:
            cmd_dict = dict(
                name=command['name'],
                command=command_map[command['name']](command['settings'])
            )
            commands.append(cmd_dict)

        return commands

