from pathlib import Path

base_dir = Path('./public')

def list_files() -> list[str]:
    """
    列出公共目录下的所有文件名称
    
    :return: 文档目录下的所有文件名称
    :rtype: list[str]
    """
    list = []
    for item in base_dir.rglob('*'):
        if item.is_file():
            list.append(item.relative_to(base_dir))
    print(list)
    return list

def read_file(path: str) -> str:
    """
    读取指定文件路径file_path的内容

    :param file_path: 文件路径
    :type file_path: Path
    :return: 返回文件内容
    :rtype: str
    """
    file_path = Path(base_dir / path)
    print(f"读取文件: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return f"文件 {file_path} 不存在"

def write_file(path: str, content: str) -> None:
    """
    写入指定文件路径file_path的内容为content
    
    :param file_path: 文件路径
    :type file_path: Path
    :param content: 文件内容
    :type content: str
    :return: None
    :rtype: None
    """
    file_path = Path(base_dir / path)
    print(f"写入文件: {file_path}")
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
    except PermissionError:
        print(f"权限错误，无法写入文件 {file_path}")


def rename_file(path: str, new_name: str) -> None:
    """
    重命名指定文件路径file_path的文件为new_name
    
    :param file_path: 文件路径
    :type file_path: Path
    :param new_name: 新文件名
    :type new_name: str
    :return: None
    :rtype: None
    """
    file_path = Path(base_dir / path)
    print(f"重命名文件: {file_path} 为 {new_name}")
    try:
        new_file_path = file_path.with_name(new_name)
        file_path.rename(new_file_path)
    except FileNotFoundError:
        print(f"文件 {file_path} 不存在")
    except PermissionError:
        print(f"权限错误，无法重命名文件 {file_path}")
