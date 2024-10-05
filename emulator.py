import os
import sys
import yaml
import csv
import zipfile
import tempfile
import shutil
import time
from datetime import datetime


def format_uptime(uptime_seconds):
    days = uptime_seconds // (24 * 3600)
    hours = (uptime_seconds % (24 * 3600)) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    if days > 0:
        return f"{days} days, {hours:02}:{minutes:02}:{seconds:02}"
    else:
        return f"{hours:02}:{minutes:02}:{seconds:02}"


class Emulator:
    def __init__(self, config_path):
        self.load_config(config_path)
        self.start_time = time.time()
        self.current_dir = '/'
        self.temp_dir = tempfile.mkdtemp()
        self.load_filesystem()
        self.log_file = open(self.config['log_file_path'], 'w', newline='')
        self.log_writer = csv.writer(self.log_file)
        self.log_writer.writerow(['Timestamp', 'User', 'Action'])

    def load_config(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def load_filesystem(self):
        with zipfile.ZipFile(self.config['vfs_path'], 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)

    def save_log(self, action):
        timestamp = datetime.now().isoformat()
        self.log_writer.writerow([timestamp, self.config['user_name'], action])

    def run(self):
        try:
            while True:
                prompt = f"{self.config['user_name']}@{self.config['computer_name']}:{self.current_dir}$ "
                command = input(prompt)
                self.parse_command(command.strip())
        except KeyboardInterrupt:
            self.exit_shell()
        finally:
            self.cleanup()

    def parse_command(self, command):
        if not command:
            return
        args = command.split()
        cmd = args[0]
        if cmd == 'exit':
            self.save_log('exit')
            self.exit_shell()
        if cmd == 'ls':
            long_format = '-l' in args
            self.save_log('ls')
            self.ls(long_format=long_format)
        elif cmd == 'cd':
            path = args[1] if len(args) > 1 else '/'
            self.save_log(f'cd {path}')
            self.cd(path)
        elif cmd == 'cat':
            if len(args) < 2:
                print("cat: missing operand")
            else:
                self.save_log(f'cat {" ".join(args[1:])}')
                self.cat(args[1:])
        elif cmd == 'tree':
            self.save_log('tree')
            self.tree()
        elif cmd == 'uptime':
            self.save_log('uptime')
            self.uptime()
        else:
            print(f"{cmd}: command not found")

    def get_abs_path(self, path):
        if os.path.isabs(path):
            abs_path = os.path.normpath(os.path.join(self.temp_dir, path.lstrip('/')))
        else:
            abs_path = os.path.normpath(os.path.join(self.temp_dir, self.current_dir.lstrip('/'), path))
        return abs_path

    def ls(self, long_format=False):
        abs_path = self.get_abs_path(self.current_dir)
        try:
            entries = os.listdir(abs_path)
            if long_format:
                for entry in entries:
                    entry_path = os.path.join(abs_path, entry)
                    stats = os.stat(entry_path)
                    file_size = stats.st_size
                    modified_time = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                    print(f"{modified_time} {file_size} {entry}")
            else:
                print('  '.join(entries))
        except FileNotFoundError:
            print("ls: cannot access: No such file or directory")

    def cd(self, path):
        new_dir = self.get_abs_path(path)
        if os.path.isdir(new_dir):
            self.current_dir = os.path.relpath(new_dir, self.temp_dir)
            if self.current_dir == '.':
                self.current_dir = '/'
            else:
                self.current_dir = '/' + self.current_dir
        else:
            print(f"cd: no such file or directory: {path}")

    def cat(self, files):
        for filename in files:
            file_path = self.get_abs_path(filename)
            if os.path.isfile(file_path):
                with open(file_path, 'r') as f:
                    print(f"\n---- {filename} ----\n")
                    print(f.read())
            else:
                print(f"cat: {filename}: No such file or directory")

    def tree(self):
        for root, dirs, files in os.walk(self.get_abs_path(self.current_dir)):
            level = root.replace(self.get_abs_path(self.current_dir), '').count(os.sep)
            indent = ' ' * 4 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                print(f"{subindent}{f}")

    def uptime(self):
        uptime_seconds = int(time.time() - self.start_time)
        uptime_string = format_uptime(uptime_seconds)

        current_time = datetime.now().strftime('%H:%M:%S')

        load_averages = (0.15, 0.10, 0.05)

        user_sessions = 1

        print(
            f" {current_time} up {uptime_string},  {user_sessions} user,  load average: {load_averages[2]}")

    def exit_shell(self):
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        self.log_file.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python emulator.py <config.yaml>")
        sys.exit(1)
    emulator = Emulator(sys.argv[1])
    emulator.run()
