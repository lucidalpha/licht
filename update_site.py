import os
import re
import json

VAULT_ROOT = "X:/Licht"
PODCASTS_MD_DIR = "X:/Licht/7 - Social Media/Youtube/AI Podcasts/Interessante Themen"
PUBLISH_DIR = "X:/Licht/Publish"
PUBLISH_PODCASTS_DIR = "X:/Licht/Publish/Youtube Quellen/Podcast Quellen"

EXCEPTIONS = {
    "Wie wir unsere Nutztiere domestizierten - Podcast-Erklärung.md": "Der Ursprung der Nutztiere.html"
}

def clean_title(title):
    # Split title if it contains long dash or similar and keep the main part
    for delimiter in [" — ", " – ", " - "]:
        if delimiter in title:
            title = title.split(delimiter)[0]
    return title.strip()

def parse_markdown(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse YAML frontmatter
    frontmatter = {}
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        for line in fm_text.split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                frontmatter[key.strip()] = val.strip()
    
    # Get title and thema
    title = frontmatter.get("title", "")
    if title:
        title = clean_title(title)
    else:
        # Fallback to filename
        filename = os.path.basename(filepath)
        title = filename.replace(" - Podcast-Erklärung.md", "").replace(".md", "")
        
    thema = frontmatter.get("thema", title)
    
    # Parse sources
    sources = []
    # Match various forms of sources header
    sources_match = re.search(r'##\s*(?:Quellen und Studien|Quellen|Literatur).*?\n(.*)', content, re.DOTALL | re.IGNORECASE)
    if sources_match:
        sources_text = sources_match.group(1)
        for line in sources_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Match list items starting with -, *, or number.
            item_match = re.match(r'^(?:[-*]|\d+\.)\s*(.*)', line)
            if item_match:
                item_text = item_match.group(1).strip()
                # Extract URL if present at the end
                url_match = re.search(r'(https?://\S+)', item_text)
                url = ""
                if url_match:
                    url = url_match.group(1).strip()
                    # Clean URL from text
                    item_text = item_text.replace(url, "").strip()
                    # Strip brackets or parenthesis around URL
                    item_text = re.sub(r'[\(\[\)\]\s\-\:]+$', '', item_text).strip()
                
                # Format text (simple markdown bold/italic parsing)
                # Bold
                item_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', item_text)
                # Italic
                item_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', item_text)
                
                sources.append({
                    "text": item_text,
                    "url": url
                })
    
    return title, thema, sources

def get_html_filename(md_filename):
    if md_filename in EXCEPTIONS:
        return EXCEPTIONS[md_filename]
    
    # Remove suffix
    name = md_filename
    for suffix in [" - Podcast-Erklärung.md", " - Podcast-Erklärung Probe.md", " - Podcast-Erklärung"]:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    if name.endswith(".md"):
        name = name[:-3]
        
    return name.strip() + ".html"

def get_skeletons(publish_dir):
    ref_path = os.path.join(publish_dir, "Youtube Quellen", "Podcast Quellen", "Der Ursprung der Nutztiere.html")
    with open(ref_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Split using the hero header start
    parts_before = html.split('<header class="hero">')
    header_skeleton = parts_before[0]
    
    # Split using the article end tag
    parts_after = html.split('</article>')
    footer_skeleton = parts_after[1]
    
    # Normalisiere assets-Pfade im Skelett (entferne relative Präfixe)
    header_skeleton = re.sub(r'(?:\.\./)+assets/', 'assets/', header_skeleton)
    footer_skeleton = re.sub(r'(?:\.\./)+assets/', 'assets/', footer_skeleton)
    
    return header_skeleton, footer_skeleton

def create_podcast_html(filepath, title, thema, sources, header_skeleton, footer_skeleton):
    sources_html = []
    for src in sources:
        text = src["text"]
        url = src["url"]
        if url:
            sources_html.append(f'<li><a href="{url}" target="_blank" rel="noopener noreferrer">{text}</a></li>')
        else:
            sources_html.append(f'<li>{text}</li>')
    
    sources_list_str = "\n".join(sources_html)
    description = f"Quellen und wissenschaftliche Literatur zur Podcast-Erklärung über {thema}."
    slug = re.sub(r'[^a-z0-9\-]+', '-', title.lower()).strip('-')
    
    hero_header = f'<header class="hero"><div class="folder-label">Podcast Quellen</div><h1>{title}</h1></header>'
    
    article_content = f'''<article class="content"><h1 id="{slug}">{title}</h1>
<p>{description}</p>
<h2 id="quellen-und-studien">Quellen und Studien</h2>
<ul>
{sources_list_str}
</ul>'''
    
    clean_header = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', header_skeleton, flags=re.IGNORECASE)
    
    # Podcasts liegen in Youtube Quellen/Podcast Quellen/ -> depth=2, also prefix='../../'
    prefix = "../../"
    clean_header = clean_header.replace('assets/', prefix + 'assets/')
    clean_footer = footer_skeleton.replace('assets/', prefix + 'assets/')
    
    html_content = f'{clean_header}{hero_header}<div class="site-shell"><nav class="site-nav"></nav>{article_content}</article></div></main>{clean_footer}'
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

def update_site_index(publish_dir, html_filename):
    index_path = os.path.join(publish_dir, "site-index.json")
    with open(index_path, 'r', encoding='utf-8') as f:
        site_index = json.load(f)
    
    html_val = f"Youtube Quellen/Podcast Quellen/{html_filename}"
    source_val = f"Youtube Quellen/Podcast Quellen/{html_filename[:-5]}.md"
    
    exists = any(entry.get("html") == html_val for entry in site_index)
    if not exists:
        site_index.append({
            "source": source_val,
            "html": html_val
        })
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(site_index, f, ensure_ascii=False, indent=2)
        print(f"Added {html_filename} to site-index.json")

def scan_site_pages(publish_dir):
    pages = {
        "Startseite": [],
        "Licht": [],
        "Meine Gedanken": [],
        "Mathematik": [],
        "Obsidian": [],
        "Trading": [],
        "Youtube Quellen": [],
        "Podcast Quellen": []
    }
    
    folders = {
        "Licht": "Licht",
        "Meine Gedanken": "Meine Gedanken",
        "Mathematik": "Mathematik",
        "Obsidian": "Obsidian",
        "Trading": "Trading",
        "Youtube Quellen": "Youtube Quellen",
        "Youtube Quellen/Podcast Quellen": "Podcast Quellen"
    }
    
    index_path = os.path.join(publish_dir, "index.html")
    if os.path.exists(index_path):
        pages["Startseite"].append({
            "title": "Startseite",
            "path": "index.html",
            "rel_dir": ""
        })
        
    for folder_rel, key in folders.items():
        folder_path = os.path.join(publish_dir, folder_rel)
        if not os.path.exists(folder_path):
            continue
        for filename in os.listdir(folder_path):
            if filename.endswith(".html"):
                filepath = os.path.join(folder_path, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
                title = title_match.group(1) if title_match else filename[:-5]
                pages[key].append({
                    "title": title,
                    "path": f"{folder_rel}/{filename}",
                    "rel_dir": folder_rel
                })
        pages[key].sort(key=lambda x: x["title"])
        
    return pages

def generate_nav_html(pages, depth):
    prefix = "../" * depth
    
    lines = []
    lines.append(f'<a class="nav-link" href="{prefix}index.html">Startseite</a>')
    
    folders_order = ["Licht", "Meine Gedanken", "Mathematik", "Obsidian", "Trading", "Youtube Quellen", "Podcast Quellen"]
    for folder in folders_order:
        folder_pages = pages.get(folder, [])
        if not folder_pages:
            continue
            
        is_open = "" if folder in ["Youtube Quellen", "Podcast Quellen"] else " open"
        lines.append(f'<details class="nav-folder"{is_open}><summary>{folder}</summary>')
        for page in folder_pages:
            path = prefix + page["path"]
            lines.append(f'<a class="nav-link nav-child" href="{path}">{page["title"]}</a>')
        lines.append('</details>')
        
    nav_inner = "\n".join(lines)
    return f'<details class="mobile-nav" open><summary>Inhalte</summary><div class="site-nav-body">\n{nav_inner}\n</div></details>'

def update_nav_in_all_files(publish_dir, pages):
    for root, dirs, files in os.walk(publish_dir):
        if ".git" in root or "assets" in root:
            continue
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(root, file)
                
                rel_path = os.path.relpath(filepath, publish_dir)
                parts = rel_path.replace("\\", "/").split("/")
                depth = len(parts) - 1
                
                target_nav = '<nav class="site-nav">' + generate_nav_html(pages, depth) + '</nav>'
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = re.sub(
                    r'<nav class="site-nav">.*?</nav>',
                    target_nav.replace('\\', '\\\\'),
                    content,
                    flags=re.DOTALL
                )
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)

def main():
    print("Starting website update process...")
    header_skeleton, footer_skeleton = get_skeletons(PUBLISH_DIR)
    
    # Process all markdown files in Interesting Themes
    for filename in os.listdir(PODCASTS_MD_DIR):
        if not filename.endswith(".md") or "Conflicted copy" in filename:
            continue
            
        filepath = os.path.join(PODCASTS_MD_DIR, filename)
        title, thema, sources = parse_markdown(filepath)
        
        # Determine output html filename
        html_filename = get_html_filename(filename)
        output_filepath = os.path.join(PUBLISH_PODCASTS_DIR, html_filename)
        
        # Check if sources exist (some probe files might not have sources)
        if not sources:
            print(f"Skipping {filename} (no sources found)")
            continue
            
        # Create or update HTML file
        create_podcast_html(output_filepath, title, thema, sources, header_skeleton, footer_skeleton)
        print(f"Generated/Updated {html_filename} for podcast: '{title}'")
        
        # Update site-index.json
        update_site_index(PUBLISH_DIR, html_filename)
        
    # Re-scan pages and synchronize navigation on all HTML files
    print("Scanning site pages to rebuild navigation...")
    pages = scan_site_pages(PUBLISH_DIR)
    
    print("Synchronizing navigation across all HTML files...")
    update_nav_in_all_files(PUBLISH_DIR, pages)
    
    print("Website update completed successfully!")

if __name__ == "__main__":
    main()
