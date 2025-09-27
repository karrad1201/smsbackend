import os

def count_lines_in_py_files(directory="."):
    total_lines = 0
    file_count = 0
    file_results = {}

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        line_count = len(lines)
                        total_lines += line_count
                        file_count += 1
                        file_results[file_path] = line_count
                        print(f"{file_path}: {line_count} строк")
                except Exception as e:
                    print(f"Ошибка при чтении файла {file_path}: {e}")

    return total_lines, file_count, file_results

def main():
    directory = input("Введите путь к директории (или нажмите Enter для текущей): ").strip()
    if not directory:
        directory = "."

    if not os.path.exists(directory):
        print("Указанная директория не существует!")
        return

    print(f"\nПоиск .py файлов в директории: {os.path.abspath(directory)}")
    print("-" * 50)

    total_lines, file_count, file_results = count_lines_in_py_files(directory)

    print("-" * 50)
    print(f"РЕЗУЛЬТАТ:")
    print(f"Найдено .py файлов: {file_count}")
    print(f"Общее количество строк: {total_lines}")

    if file_results:
        max_lines_file = max(file_results, key=file_results.get)
        min_lines_file = min(file_results, key=file_results.get)
        avg_lines = total_lines / file_count if file_count > 0 else 0

        print(f"Среднее количество строк на файл: {avg_lines:.1f}")
        print(f"Файл с наибольшим количеством строк: {max_lines_file} ({file_results[max_lines_file]} строк)")
        print(f"Файл с наименьшим количеством строк: {min_lines_file} ({file_results[min_lines_file]} строк)")

if __name__ == "__main__":
    main()