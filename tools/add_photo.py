import json
import requests
import pywikibot
import tqdm
site = pywikibot.Site("nl", "wikipedia")
repo = site.data_repository()

def main():
    filename = 'data/composition/55.json'
    with open(filename, 'r') as fp:
        members = json.load(fp)
    for member in tqdm.tqdm(members):
        if 'photo_url' in member:
            continue
        # First try wikipedia, then wikidata
        wiki_slug = member['wiki'].replace('https://nl.wikipedia.org/wiki/', '').replace('https://fr.wikipedia.org/wiki/', '')
        r = requests.get(f'https://nl.wikipedia.org/w/api.php?action=query&prop=pageprops&titles={wiki_slug}&format=json').json()
        pages = r["query"]["pages"]
        if pages.keys():
            page = pages[list(pages.keys())[0]]['pageprops']
            #print(page)
            if 'page_image_free' in page:
                member['photo_url'] = f'https://upload.wikimedia.org/wikipedia/commons/b/bf/{page["page_image_free"]}'

        if 'photo_url' not in member and 'wikibase_item' in member:
            item = pywikibot.ItemPage(repo, member['wikibase_item'])
            image_object = item.page_image()
            if image_object:
                member['photo_url'] = image_object.full_url()

        with open(filename, 'w') as fp:
            json.dump(members, fp, ensure_ascii=False)

if __name__ == "__main__":
    main()