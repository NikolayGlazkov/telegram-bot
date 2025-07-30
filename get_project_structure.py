#!/usr/bin/env python3
"""
Скрипт для получения структуры проекта в формате дерева
"""

import os
import argparse
from pathlib import Path

def get_project_structure(root_dir: str = ".", ignore_patterns: list = None) -> str:
    """
    Получает структуру проекта в виде дерева
    
    Args:
        root_dir: Корневая директория проекта
        ignore_patterns: Список паттернов для игнорирования
    
    Returns:
        str: Структура проекта в виде строки
    """
    if ignore_patterns is None:
        ignore_patterns = [
            '__pycache__', '*.pyc', '*.pyo', '*.pyd', '.git', '.idea', 
            '.vscode', '.DS_Store', 'node_modules', '.env', '*.log',
            'venv', 'env', '.venv'
        ]
    
    def should_ignore(path: Path, patterns: list) -> bool:
        """Проверяет, нужно ли игнорировать путь"""
        for pattern in patterns:
            if path.name == pattern or path.match(pattern):
                return True
        return False
    
    def build_tree(directory: Path, prefix: str = "", is_last: bool = True) -> list:
        """Рекурсивно строит дерево файлов"""
        lines = []
        
        # Получаем список файлов и директорий
        try:
            items = sorted([item for item in directory.iterdir() 
                          if not should_ignore(item, ignore_patterns)])
        except PermissionError:
            return [f"{prefix}{'└── ' if is_last else '├── '} [Permission Denied]"]
        
        for i, item in enumerate(items):
            is_last_item = i == len(items) - 1
            connector = "└── " if is_last_item else "├── "
            
            if item.is_dir():
                lines.append(f"{prefix}{connector}{item.name}/")
                extension = "    " if is_last_item else "│   "
                lines.extend(build_tree(item, prefix + extension, is_last_item))
            else:
                lines.append(f"{prefix}{connector}{item.name}")
        
        return lines
    
    root_path = Path(root_dir)
    structure_lines = [f"{root_path.name}/"]
    structure_lines.extend(build_tree(root_path))
    
    return "\n".join(structure_lines)

def save_structure_to_file(structure: str, filename: str = "project_structure.txt"):
    """Сохраняет структуру в файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(structure)
    print(f"Структура проекта сохранена в {filename}")

def main():
    parser = argparse.ArgumentParser(description="Получить структуру проекта")
    parser.add_argument(
        "-d", "--directory", 
        default=".", 
        help="Директория проекта (по умолчанию текущая)"
    )
    parser.add_argument(
        "-o", "--output", 
        help="Файл для сохранения структуры"
    )
    parser.add_argument(
        "--ignore", 
        nargs="*", 
        help="Дополнительные паттерны для игнорирования"
    )
    
    args = parser.parse_args()
    
    # Добавляем пользовательские паттерны игнорирования
    ignore_patterns = None
    if args.ignore:
        ignore_patterns = [
            '__pycache__', '*.pyc', '*.pyo', '*.pyd', '.git', '.idea', 
            '.vscode', '.DS_Store', 'node_modules', '.env', '*.log',
            'venv', 'env', '.venv'
        ] + args.ignore
    
    structure = get_project_structure(args.directory, ignore_patterns)
    
    # Выводим в консоль
    print(structure)
    
    # Сохраняем в файл если указан
    if args.output:
        save_structure_to_file(structure, args.output)

if __name__ == "__main__":
    main()