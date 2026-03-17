from pathlib import Path

base_dir = Path('./public')

def list_files() -> list[str]:
    """
    列出公共目录下的所有文件名称
    
    :return: 文档目录下的所有文件名称
    :rtype: list[str]
    """
    files = []
    for item in base_dir.rglob('*'):
        if item.is_file():
            files.append(item.relative_to(base_dir))
    print(files)
    return files

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


def search_real_estate_price(city: str, district: str = None) -> str:
    """
    搜索指定城市和区域的房价信息。如果没有指定区域，则返回该城市的整体房价信息。
    
    :param city: 城市名称，例如 "北京"、"上海"、"深圳"
    :type city: str
    :param district: 区域名称，例如 "朝阳区"、"浦东新区"（可选）
    :type district: str
    :return: 房价信息，包括平均价格、走势等
    :rtype: str
    """
    query = f"{city} {district if district else ''} 房价 {2025}年"
    print(f"搜索房价: {query}")
    return f"正在搜索 {city} {' ' + district if district else ''} 的房价信息..."
