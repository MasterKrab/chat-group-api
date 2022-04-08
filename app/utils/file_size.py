def get_is_max_size(file, max_size):
    size = 0

    for chunk in file:
        size += len(chunk)

        if size > max_size:
            return True

    return False
