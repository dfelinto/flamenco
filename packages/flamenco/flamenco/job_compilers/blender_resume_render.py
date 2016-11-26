from flamenco.utils import frame_range_parse
from flamenco.utils import frame_range_merge


def compile_blender_resume_render(job, create_task):
    """The Blender render job with resume options."""
    job_settings = job['settings']
    parsed_frames = frame_range_parse(job_settings['frames'])
    chunk_size = job_settings['chunk_size']
    file_format = job_settings['format']

    try:
        render_output = job_settings['render_output']
    except KeyError:
        render_output = render_output_from_filepath(job_settings['filepath'])

    task_parents = {}
    cycles_num_chunks = job_settings['cycles_num_chunks']
    for cycles_chunk in range(1, cycles_num_chunks + 1):

        for i in range(0, len(parsed_frames), chunk_size):
            # each chunk is parent of its own other chunk renders
            if task_parents.get(i) == None:
                task_parents[i] = []

            commands = []

            frames = frame_range_merge(parsed_frames[i:i + chunk_size])
            cmd_render = {
                'name': 'blender_render',
                'settings': {
                    'filepath': job_settings['filepath'],
                    'format': job_settings['format'],
                    'frames': frames,
                    'cycles_num_chunks': cycles_num_chunks,
                    'cycles_chunk': cycles_chunk,
                }
            }

            # we force the render_output to be specified at all times
            cmd_render['settings']['render_output'] = render_output

            commands.append(cmd_render)

            # merge the files together
            if cycles_chunk == 1:
                for frame in parsed_frames[i:i + chunk_size]:
                    input_image_render = filepath_from_frame(render_output, frame, file_format)
                    output_image_merge = merge_filepath_from_filepath(input_image_render)

                    cmd_move = {
                        'name': 'move_file',
                        'settings': {
                            'input_file': input_image_render,
                            'output_file': output_image_merge,
                            },
                        }
                    commands.append(cmd_move)

            else:
                for frame in parsed_frames[i:i + chunk_size]:
                    input_image_render = filepath_from_frame(render_output, frame, file_format)
                    output_image_merge = merge_filepath_from_filepath(input_image_render)
                    input_image_merge = merge_filepath_from_filepath(input_image_render, "_merge_temp")

                    cmd_move = {
                        'name': 'move_file',
                        'settings': {
                            'input_file': output_image_merge,
                            'output_file': input_image_merge,
                            },
                        }
                    commands.append(cmd_move)

                    cmd_merge = {
                        'name': 'imagemagick_convert',
                        'settings': {
                            'input_image_render': input_image_render,
                            'input_image_merge': input_image_merge,
                            'output_image_merge': output_image_merge,
                            'cycles_chunk': cycles_chunk,
                            }
                        }
                    commands.append(cmd_merge)

                    cmd_delete = {
                        'name': 'delete_file',
                        'settings': {
                            'filepath': input_image_merge,
                            },
                        }
                    commands.append(cmd_delete)

            # assuming a single task per chunk render (for a cycles chunk)
            task = create_task(job, commands, frames, parents=task_parents[i])
            task_parents[i] = [task]

    # move the merged images to the correct location
    # only do this for the final step
    commands = []
    for i in range(0, len(parsed_frames), chunk_size):
        for frame in parsed_frames[i:i + chunk_size]:
            input_image_render = filepath_from_frame(render_output, frame, file_format)
            output_image_merge = merge_filepath_from_filepath(input_image_render)

            cmd_move = {
                'name': 'move_file',
                        'settings': {
                            'input_file': output_image_merge,
                            'output_file': input_image_render,
                            },
                        }
            commands.append(cmd_move)

        frames = frame_range_merge(parsed_frames[i:i + chunk_size])
        create_task(job, commands, frames, parents=task_parents[i])


def filepath_from_frame(render_output, frame, file_format):
    import os
    # TODO do it for real, with smart path handling or call blender and get it from it
    formats = {
            'JPEG': 'jpg',
            'PNG': 'png',
            }

    extension = formats.get(file_format, "jpg")
    # TODO - assert if extension doesn't match?
    return os.path.join(render_output, "{0:04d}.{1}".format(frame, extension))


def render_output_from_filepath(filepath):
    # TODO use BAM, or blender output
    return "/tmp/"


def merge_filepath_from_filepath(filepath, merge="_merge"):
    """Add _merge before file suffix"""
    return "{0}{1}.{2}".format(filepath[:-4], merge, filepath[-3:])

