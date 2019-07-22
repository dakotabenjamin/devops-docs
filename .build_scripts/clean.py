import os
import re
import shutil
import pathlib

import frontmatter
import toml



def main():
    extensions = {}
    with open('config.toml', 'r') as f:
        config = toml.loads(f.read())
        default_lang = config['DefaultContentLanguage']
        site_name = config['title'].replace(' ', '_')
        site_name = site_name.replace("'", "")
        site_name = site_name.replace('"', '')
        site_name = site_name.replace(',', '')
        site_name = site_name.replace('.', '')
        if 'languages' in config:
            for key in config['languages']:
                extensions[config['languages'][key]['contentDir'].split('/')[-1]] = key
                if key != default_lang:
                    os.mkdir(os.path.join('pdf-build', key))
    guides = []
    if 'pages' in os.listdir('content'):
        # single language
        contents = []
        for item in os.listdir('content'):
            if os.path.isfile(os.path.join('content',item)):
                ext = os.path.splitext(item)[1]
                if ext != '.md':
                    copyfile(os.path.join('content', item), os.path.join('pdf-build',item))
        # move image files
        for path, _, files in os.walk('content/pages'):
            for filename in files:
                ext = os.path.splitext(filename)[1]
                if ext != '.md':
                    copyfile(os.path.join(path, filename), os.path.join('pdf-build',filename))
        for path, _, files in os.walk('static/'):
            p = pathlib.Path(path)
            cleaned_path = p.relative_to(*p.parts[:2])
            pdf_path = pathlib.Path('pdf-build').joinpath(p.relative_to(*p.parts[:2]))
            if not os.path.exists(pdf_path):
                os.makedirs(pdf_path)
            for filename in files:
                ext = os.path.splitext(filename)[1]
                if ext.lower() in ['.jpg','.jpeg','.png','.gif']:
                    copy_parents(os.path.join(path, filename),'pdf-build', 1)
            images = []
        for path, d, f in os.walk('pdf-build'):
            p = pathlib.Path(*pathlib.Path(path).parts[1:])
            for file in f:
                if re.search(r'.*\.(jpe?g|png|gif)$', file):
                    images.append(os.path.join(p, file))
        for path, _, files in os.walk('content/pages'):
            for filename in files:
                ext = os.path.splitext(filename)[1]
                if ext == '.md':
                    content = clean_markdown(path, filename, images, default_lang=default_lang)
                    if content:
                        contents.append({'name':filename, 'content': content})
                else:
                    continue
        full_pdf_content = "\n\n\pagebreak\n\n"
        content = clean_markdown("content", "_index.md", images)
        if content:
            full_pdf_content += content
            full_pdf_content += "\n\n\pagebreak\n\n"
        for item in sorted(contents, key=lambda k: k['name']):
            full_pdf_content += item['content']
            full_pdf_content += "\n\n\pagebreak\n\n"
        with open('pdf-build/' + site_name + ".fullsite.md", 'w') as f:
            f.write(full_pdf_content)
        
    else:
        # multiple languages
        for lang in os.listdir('content'):
            contents = []
            lang_key = extensions[lang]
            lang_path = os.path.join('content', lang)
            for path, _, files in os.walk(lang_path):
                if lang_key == default_lang:
                    lang_key = ''
                for filename in files:
                    ext = os.path.splitext(filename)[1]
                    if ext == '.md':
                        content = clean_markdown(path, filename, lang_key, default_lang)
                        if content:
                            contents.append({'name':filename, 'content': content})
                    else:
                        copyfile(os.path.join(path,filename), os.path.join('pdf-build',lang_key,filename))
            full_pdf_content = "\n\n\pagebreak\n\n"
            for item in sorted(contents, key=lambda k: k['name']):
                full_pdf_content += item['content']
                full_pdf_content += "\n\n\pagebreak\n\n"
            with open('pdf-build/' + site_name + ".md", 'w') as f:
                f.write(full_pdf_content)

def copy_parents(src, dest_folder, dir_offset=0):
    prev_offset = 0 if dir_offset == 0 else src.replace('/', '%', dir_offset - 1).find('/') + 1
    post_offset = src.rfind('/')

    src_dirs = '' if post_offset == -1 else src[prev_offset:post_offset]
    src_filename = src[post_offset + 1:]

    os.makedirs(f'{dest_folder}/{src_dirs}', exist_ok=True)
    shutil.copy(src, f'{dest_folder}/{src_dirs}/{src_filename}')


def clean_markdown(path, filename, images, lang="", default_lang = "en"):
    post = frontmatter.load(os.path.join(path, filename))
    if post.content:
        title = post.metadata.get('title', '')
        guide = {}
        guide['filename'] = filename
        content = post.content
        for image in images:
            replace_regex = r'(\!\[.*\]).*(\()(.*\/)(' + re.escape(str(image)) + r')([A-Za-z\s\"\'\-\,\.\;\:]*)(\))'
            content = re.sub(replace_regex, r'\1\2\4\5\6', content)
        guide['content'] = ''
        if title:
            guide['content'] += '# {0} \n\n'.format(title)
        guide['content'] += content
        if lang and lang != default_lang:
            out_file = os.path.join('pdf-build', lang, guide['filename'])
        else: 
            out_file = os.path.join('pdf-build', guide['filename'])
        with open(out_file, 'w') as f:
            f.write(guide['content'])
        return guide['content']
    return ''

if __name__ == "__main__":
    main()