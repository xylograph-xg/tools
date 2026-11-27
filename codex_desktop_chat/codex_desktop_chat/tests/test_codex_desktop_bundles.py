import tempfile,unittest,zipfile,json
from pathlib import Path
from codex_desktop_chat import prepare_upload_bundle,DesktopChatError
from codex_desktop_chat.bundles import verify_bundle,MANIFEST

class BundleTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.out=self.root/'zips'
  self.a=self.root/'原文.txt';self.a.write_text('原文证据');self.b=self.root/'image.png';self.b.write_bytes(b'example image bytes')
 def pack(self,files):return prepare_upload_bundle(files,bundle_dir=self.out)
 def test_exact_content_manifest_and_content_address_reuse(self):
  first=self.pack([self.a,self.b]);second=self.pack([self.b,self.a]);self.assertEqual(first['zip_path'],second['zip_path']);self.assertTrue(second['reused'])
  self.assertEqual(len(list(self.out.glob('*.zip'))),1)
  with zipfile.ZipFile(first['zip_path']) as z:
   self.assertEqual(z.read(self.a.name).decode(),self.a.read_text());self.assertEqual(z.read(self.b.name),self.b.read_bytes());self.assertEqual(len(json.loads(z.read(MANIFEST))['files']),2)
 def test_changed_content_gets_new_bundle(self):
  a=self.pack([self.a]);self.a.write_text('new evidence');b=self.pack([self.a]);self.assertNotEqual(a['zip_path'],b['zip_path']);verify_bundle(a['zip_path'])
 def test_existing_zip_is_staged_without_nesting(self):
  external=self.root/'external.zip'
  with zipfile.ZipFile(external,'w') as z:z.writestr('file.txt','hello')
  r=self.pack([external]);self.assertEqual(Path(r['zip_path']).parent,self.out.resolve());self.assertEqual(r['entries'],['file.txt']);self.assertTrue(self.pack([r['zip_path']])['reused'])
 def test_corrupt_existing_package_rejected(self):
  r=self.pack([self.a]);Path(r['zip_path']).write_bytes(b'broken')
  with self.assertRaises(DesktopChatError):self.pack([self.a])
 def test_unsafe_zip_and_reserved_manifest_rejected(self):
  p=self.root/'bad.zip'
  with zipfile.ZipFile(p,'w') as z:z.writestr('../escape','bad')
  with self.assertRaises(DesktopChatError):self.pack([p])
  p=self.root/MANIFEST;p.write_text('collision')
  with self.assertRaises(ValueError):self.pack([p])
 def test_no_app_needed_and_temp_files_cleaned(self):
  r=self.pack([self.a]);self.assertTrue(Path(r['zip_path']).is_file());self.assertEqual(list(self.out.glob('.packing-*')),[])

if __name__=='__main__':unittest.main()
