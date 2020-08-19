def extension_to_media_type(extension):
    if extension == 'gif':
        return 'image/gif'
    elif extension == 'html':
        return 'application/xhtml+xml'
    elif extension == 'jpg' or extension == 'jpeg':
        return 'image/jpeg'
    elif extension == 'png':
        return 'image/png'
    elif extension == 'ncx':
        return 'application/x-dtbncx+xml'
    else:
        raise Exception("Unknown extension: " + extension)

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
