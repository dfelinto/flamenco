from flamenco.utils import frame_range_parse
from flamenco.utils import frame_range_merge
import os

KEEP_PARTIAL_IMAGES = True

def compile_blender_resume_render(job, create_task):
    """The Blender render job with resume options."""
    job_settings = job['settings']
    parsed_frames = frame_range_parse(job_settings['frames'])
    chunk_size = job_settings['chunk_size']
    file_format = job_settings['format']
    is_exr = file_format == 'EXR'
    file_path = job_settings['filepath']
    # temporary "job" folder where we render to - TODO needs implementation from @fsiddi
    # job_folder = job_settings['job_folder']
    job_folder = "/tmp/"
    # filepath that is used as blender --render-output
    render_filepath = get_render_filepath(job_folder)

    # render_output is used for the final and partial files
    # only - we render in different folders
    render_output = job_settings['render_output']

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
                    'filepath': file_path,
                    'format': 'EXR',
                    'frames': frames,
                    'cycles_num_chunks': cycles_num_chunks,
                    'cycles_chunk': cycles_chunk,
                    'render_output': render_filepath,
                }
            }
            commands.append(cmd_render)

            # debug option
            if KEEP_PARTIAL_IMAGES:
                for frame in parsed_frames[i:i + chunk_size]:
                    published_file = get_render_filepath_from_frame(render_filepath, frame)
                    debug_file = get_debug_filepath_from_frame_chunk(job_folder, frame, cycles_chunk)

                    if is_exr:
                        cmd_copy = {
                            'name': 'copy_file',
                            'settings': {
                                'input_file': published_file,
                                'output_file': debug_file,
                                },
                            }
                        commands.append(cmd_copy)
                    else:
                        cmd_convert = {
                            'name': 'imagemagick_convert',
                            'settings': {
                                'input_image': published_file,
                                'output_image': debug_file,
                                }
                            }
                        commands.append(cmd_convert)

            # merge the files together
            if cycles_chunk == 1:
                for frame in parsed_frames[i:i + chunk_size]:
                    rendered_file = get_render_filepath_from_frame(render_filepath, frame)
                    partial_file = get_partial_filepath_from_frame(job_folder, frame)
                    published_file = get_output_filepath_from_frame(render_output, file_format, frame)

                    # "publish" preview image
                    if is_exr:
                        cmd_copy = {
                            'name': 'copy_file',
                            'settings': {
                                'input_file': rendered_file,
                                'output_file': published_file,
                                },
                            }
                        commands.append(cmd_copy)
                    else:
                        cmd_convert = {
                            'name': 'imagemagick_convert',
                            'settings': {
                                'input_image': rendered_file,
                                'output_image': published_file,
                                }
                            }
                        commands.append(cmd_convert)

                    # store accumulated result so far
                    cmd_move = {
                        'name': 'move_file',
                        'settings': {
                            'input_file': rendered_file,
                            'output_file': partial_file,
                            },
                        }
                    commands.append(cmd_move)

            else:
                for frame in parsed_frames[i:i + chunk_size]:
                    rendered_file = get_render_filepath_from_frame(render_filepath, frame)
                    partial_file = get_partial_filepath_from_frame(job_folder, frame)
                    published_file = get_output_filepath_from_frame(render_output, file_format, frame)

                    if is_exr:
                        published_exr_file = published_file
                    else:
                        published_exr_file = get_output_filepath_from_frame(job_folder, 'EXR', frame)

                    # convert and automatically "publish" preview image
                    cmd_merge = {
                        'name': 'imagemagick_merge',
                        'settings': {
                            'input_image_render': rendered_file,
                            'input_image_merge': partial_file,
                            'output_image_merge': published_exr_file,
                            'cycles_chunk': cycles_chunk,
                            }
                        }
                    commands.append(cmd_merge)

                    # keep local partial copy of published image
                    cmd_copy = {
                        'name': 'copy_file',
                        'settings': {
                            'input_file': published_exr_file,
                            'output_file': partial_file,
                            },
                        }
                    commands.append(cmd_copy)

                    if not is_exr:
                        cmd_convert = {
                            'name': 'imagemagick_convert',
                            'settings': {
                                'input_image': partial_file,
                                'output_image': published_file,
                                }
                            }
                        commands.append(cmd_convert)

            # assuming a single task per chunk render (for a cycles chunk)
            task = create_task(job, commands, frames, parents=task_parents[i])
            task_parents[i] = [task]


def get_extension(file_format):
    """Get the file extension based on the file format
    """
    formats = {
            'TGA': 'tga',
            'RAWTGA': 'tga',
            'JPEG': 'jpg',
            'IRIS': 'rgb',
            'IRIZ': 'rgb',
            'PNG': 'png',
            'BMP': 'bmp',
            'HDR': 'hdr',
            'TIFF': 'tif',
            'EXR': 'exr',
            'MULTILAYER': 'exr',
            'CINEON': 'cin',
            'DPX': 'dpx',
            'JP2': 'jp2',
            }

    extension = formats.get(file_format, "tga")
    return extension


def get_render_filepath(basedir):
    """Get filepath used to render from Blender"""
    extension = 'exr'
    return os.path.join(basedir, "######.{0}".format(extension))


def get_render_filepath_from_frame(render_filepath, frame):
    """Get filepath of rendered frame from Blender"""
    basedir, basename = os.path.split(render_filepath)

    start = basename.find("#")
    end = basename.rfind("#")

    if start == -1:
        start = 0
        end = 1

    string = "{{0}}{{1:0{digits}d}}{{2}}".format(digits=(end - start + 1))
    filepath = string.format(basename[:start], frame, basename[end + 1:])

    return os.path.join(basedir, filepath)


def strip_extension(basename):
    """Return stripped string
    remove extension of file (up to 4 letters)
    foobar.abcde > foobar.abcde
    foobar.jpeg > foobar
    foobar.jpg > foobar
    foobar.jp > foobar
    foobar.j > foobar
    foobar. > foobar
    foobar > foobar
    """
    len_basename = len(basename)
    period = basename.rfind('.')

    if len_basename - period <= 5:
        return basename[:-(len_basename - period)]
    else:
        return basename


def get_output_filepath_from_frame(render_output, file_format, frame):
    """Get filepath used to output/publish partial or final frames"""
    basedir, basename = os.path.split(render_output)

    if not basename:
        basename = "######"
    else:
        basename = strip_extension(basename)

    extension = get_extension(file_format)
    basename = "{0}.{1}".format(basename, extension)

    filepath = os.path.join(basedir, basename)
    return get_render_filepath_from_frame(filepath, frame)


def get_debug_filepath_from_frame_chunk(basedir, frame, cycles_chunk):
    """Get filepath for individual rendered images"""
    basename = "######-{0:02d}".format(cycles_chunk)

    extension = get_extension('EXR')
    basename = "{0}.{1}".format(basename, extension)

    filepath = os.path.join(basedir, basename)
    return get_render_filepath_from_frame(filepath, frame)


def get_partial_filepath_from_frame(basedir, frame):
    """Get filepath with accumulated render results"""
    basename = get_render_filepath(basedir)
    basename = get_render_filepath_from_frame(basename, frame)
    filepath = "{0:}_partial.{1}".format(basename[:-4], basename[-3:])
    return os.path.join(basedir, filepath)

