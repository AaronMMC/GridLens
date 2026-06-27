import os
import glob

# Files to rename
files = []
files.extend(glob.glob('*.py'))
files.extend(glob.glob('core/*.py'))
files.extend(glob.glob('core/backends/*.py'))
files.extend(glob.glob('ui/*.py'))
files.extend(glob.glob('*.md'))
files.extend(glob.glob('.agents/*.md'))
files.extend(glob.glob('*.bat'))
files.extend(glob.glob('*.ps1'))
files.extend(glob.glob('*.nsi'))
files.extend(glob.glob('*.spec'))

for f in files:
    if not os.path.isfile(f): continue
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    if 'GridLens' in content or 'GridLens' in content:
        content = content.replace('GridLens', 'GridLens')
        content = content.replace('GridLens', 'GridLens')
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)

if os.path.exists('GridLens.spec'):
    os.rename('GridLens.spec', 'GridLens.spec')

print("Rename complete.")
