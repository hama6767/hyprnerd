import hashlib,importlib.util,json,pathlib,tarfile,tempfile,unittest
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('kitty_installer',pathlib.Path(__file__).resolve().parents[1]/'scripts/install-kitty.py')
installer=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(installer)
class KittyInstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name);self.home=self.root/'home';self.home.mkdir()
        self.repo=self.root/'repo';(self.repo/'.cache').mkdir(parents=True)
        payload=self.root/'payload';(payload/'bin').mkdir(parents=True)
        for name in ['kitty','kitten']:
            p=payload/'bin'/name;p.write_text('#!/bin/sh\nexit 0\n');p.chmod(0o755)
        archive=self.repo/'.cache/kitty.txz'
        with tarfile.open(archive,'w:xz') as t:t.add(payload/'bin',arcname='bin')
        self.spec={'version':'test','url':'https://example.invalid/kitty.txz','sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
        self.save()
        self.patches=[patch.object(installer,'R',self.repo),patch.object(pathlib.Path,'home',return_value=self.home),patch.object(installer.platform,'system',return_value='Linux'),patch.object(installer.platform,'machine',return_value='x86_64')]
        for p in self.patches:p.start();self.addCleanup(p.stop)
    def save(self):(self.repo/'dependencies.lock.json').write_text(json.dumps({'kitty_binary':self.spec}))
    def test_install_is_idempotent_and_preserves_previous_launcher(self):
        bindir=self.home/'.local/bin';bindir.mkdir(parents=True);(bindir/'kitty').write_text('previous launcher')
        installer.main();installer.main()
        backups=list(bindir.glob('kitty.before-hyprnerd-*'));self.assertEqual(len(backups),1);self.assertEqual(backups[0].read_text(),'previous launcher')
        self.assertTrue((bindir/'kitty').is_symlink());self.assertTrue((bindir/'kitten').resolve().is_file())
        self.assertTrue((bindir/'kitty').stat().st_mode & 0o111)
    def test_bad_checksum_cannot_change_launchers(self):
        self.spec['sha256']='bad';self.save()
        with self.assertRaises(SystemExit):installer.main()
        self.assertFalse((self.home/'.local').exists())
if __name__=='__main__':unittest.main()
