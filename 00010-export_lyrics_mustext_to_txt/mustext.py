from bs4 import BeautifulSoup
import urllib.request as r

the_url = input()

page = r.urlopen(the_url)

page_in_html = page.read().decode('utf8')
page_in_soup = BeautifulSoup(page_in_html, features="lxml")

tmp_lyrics = page_in_soup.find("p", {"style": "text-align: center;"})
the_title = str(page_in_soup.find("h2"))
the_title=the_title.replace('<h2>','')
the_title=the_title.replace('</h2>','')

the_lyrics = []

for i in tmp_lyrics:
    the_lyrics.append(str(i))

del the_lyrics[0]
del the_lyrics[-1]

html_tags = ['<br>', '<br/>', '<strong>', '</strong>']

my_flie = open('output.txt', 'w', encoding="utf8")

new_lines = []
new_lines.append(the_title)

for i in the_lyrics:
    tmp_x = i
    for j in html_tags:
        tmp_x = tmp_x.replace(j, '')
    new_lines.append(tmp_x)

my_flie.writelines(new_lines)

my_flie.close()
