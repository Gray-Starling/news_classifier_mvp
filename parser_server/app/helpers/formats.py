def human_readable_size(bytes_size: int) -> str:
    """Преобразует размер файла в человекочитаемый формат."""
    if bytes_size < 1e9:
        return f"{bytes_size / 1e6:.2f} МБ"
    return f"{bytes_size / 1e9:.2f} ГБ"