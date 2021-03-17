import json
import requests
import pywikibot
import tqdm
site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

def main():
    with open('data/composition/52.json', 'r') as fp:
        members = json.load(fp)
        for member in tqdm.tqdm(members):
            wiki_slug = member['wiki'].replace('https://nl.wikipedia.org/wiki/', '').replace('https://fr.wikipedia.org/wiki/', '')
            r = requests.get(f'https://nl.wikipedia.org/w/api.php?action=query&prop=pageprops&titles={wiki_slug}&format=json').json()
            pages = r["query"]["pages"]
            if pages.keys():
                page_zero_props = pages[list(pages.keys())[0]]['pageprops']
                if 'wikibase_item' in page_zero_props:
                    item = pywikibot.ItemPage(repo, page_zero_props['wikibase_item'])
                    member['wikibase_item'] = page_zero_props['wikibase_item']
                    if 'P21' in item.get()['claims']:
                        gender = item.get()['claims']['P21'][0].getTarget().get()['labels']['en']
                        member['gender'] = gender
                        continue
            member['gender'] = 'X'
        with open('outfile.json', 'w+') as op:
            json.dump(members, op, ensure_ascii=False)
                    
if __name__ == "__main__":
    main()