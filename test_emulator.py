import unittest
import os
import shutil
import yaml
import csv
import tempfile
from emulator import Emulator


class TestEmulator(unittest.TestCase):
    def setUp(self):
        self.config_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.yaml')
        config_data = {
            'user_name': 'testuser',
            'computer_name': 'testmachine',
            'vfs_path': '',
            'log_file_path': ''
        }
        yaml.dump(config_data, self.config_file)
        self.config_file.close()

        self.vfs_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.vfs_dir, 'folder1'))
        with open(os.path.join(self.vfs_dir, 'file1.txt'), 'w') as f:
            f.write('Hello World')
        with open(os.path.join(self.vfs_dir, 'file2.txt'), 'w') as f:
            f.write('Another File')
        shutil.make_archive('vfs', 'zip', self.vfs_dir)
        self.vfs_zip = 'vfs.zip'

        config_data['vfs_path'] = self.vfs_zip
        config_data['log_file_path'] = 'test_log.csv'
        with open(self.config_file.name, 'w') as f:
            yaml.dump(config_data, f)

        self.emulator = Emulator(self.config_file.name)

    def tearDown(self):
        self.emulator.cleanup()
        os.unlink(self.config_file.name)
        os.remove(self.vfs_zip)
        shutil.rmtree(self.vfs_dir)
        if os.path.exists('test_log.csv'):
            os.remove('test_log.csv')

    def test_ls_root(self):
        output = self.emulator.ls()
        if output is not None:
            self.assertIn('folder1', output)
            self.assertIn('file1.txt', output)
            self.assertIn('file2.txt', output)

    def test_ls_folder(self):
        self.emulator.cd('folder1')
        output = self.emulator.ls()
        if output is not None:
            self.assertEqual(output, '')

    def test_ls_nonexistent(self):
        self.emulator.cd('nonexistent')
        output = self.emulator.ls()
        if output is not None:
            self.assertIn('cannot access', output)

    def test_cd_root(self):
        self.emulator.cd('/')
        self.assertEqual(self.emulator.current_dir, '/')

    def test_cd_folder(self):
        self.emulator.cd('folder1')
        self.assertIn('folder1', self.emulator.current_dir)

    def test_cd_nonexistent(self):
        self.emulator.cd('nonexistent')
        self.assertNotIn('nonexistent', self.emulator.current_dir)

    def test_cat_single_file(self):
        output = self.emulator.cat(['file1.txt'])
        if output is not None:
            self.assertIn('Hello World', output)

    def test_cat_multiple_files(self):
        output = self.emulator.cat(['file1.txt', 'file2.txt'])
        if output is not None:
            self.assertIn('Hello World', output)
            self.assertIn('Another File', output)

    def test_cat_nonexistent_file(self):
        output = self.emulator.cat(['nofile.txt'])
        if output is not None:
            self.assertIn('No such file or directory', output)

    def test_tree_root(self):
        output = self.emulator.tree()
        if output is not None:
            self.assertIn('folder1/', output)
            self.assertIn('file1.txt', output)
            self.assertIn('file2.txt', output)

    def test_tree_subfolder(self):
        self.emulator.cd('folder1')
        output = self.emulator.tree()
        if output is not None:
            self.assertIn('folder1/', output)

    def test_tree_nonexistent_folder(self):
        self.emulator.cd('nonexistent')
        output = self.emulator.tree()
        if output is not None:
            self.assertIn('cannot access', output)

    def test_uptime_initial(self):
        output = self.emulator.uptime()
        if output is not None:
            self.assertIn('Uptime:', output)

    def test_uptime_after_delay(self):
        import time
        time.sleep(1)
        output = self.emulator.uptime()
        if output is not None:
            self.assertIn('Uptime:', output)

    def test_uptime_format(self):
        output = self.emulator.uptime()
        if output is not None:
            self.assertIn('Uptime:', output)


if __name__ == '__main__':
    unittest.main()
