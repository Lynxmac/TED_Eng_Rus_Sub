# -*- coding:utf-8 -*-
from bs4 import BeautifulSoup
import urllib2
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

RU_UPPER = u'АБВГДЕЁЖЗИЙКЛМН'\
        u"ОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
RU_CHC = u'АБВГДЕЁЖЗИЙКЛМН'\
        u"ОПРСТУФХЦЧШЩЪЫЬЭЮЯ"\
        u'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
EN_UPPER = u"ABCDEFGHIJKLMNOPQRSTUVWXYZ"



def paras_soup(url):
    en_html = urllib2.urlopen(url+"/transcript?language=en").read()
    rus_html = urllib2.urlopen(url+"/transcript?language=ru").read()
    en_soup = BeautifulSoup(en_html)
    ru_soup = BeautifulSoup(rus_html)
    en_paras = en_soup.findAll('p', 'talk-transcript__para')
    ru_paras = ru_soup.findAll('p', 'talk-transcript__para')
    return en_paras, ru_paras


def check(substring,string):
    sublist = list(substring)
    for sub in sublist:
        if sub in string:
            return True
    return False

def is_RUS(max_items, max_timestamps):
    max_list = list(max_items[max_timestamps])
    for chc in max_list:
        if chc in RU_CHC:
            return  True
    return False

def extract_paras(paras_soup):
    speach = {}
    num = 0
    timestamps = []
    for para in paras_soup:
        num += 1
        timestamp = para.data.getText().strip(u'\n')
        p = {}
        for span in para.findAll('span',"talk-transcript__fragment"):
            time = int(span['data-time'])
            text = span.getText() if '\n' not in span.getText() else span.getText().replace("\n"," ")
            if (len(text)!=0) and ((text[0] in EN_UPPER ) \
                or (text[0] in RU_UPPER)):
                p[time] = text.replace(u'\n', u' ')
                last_time = time
            elif check(".?!;", text):
                try:
                    p[last_time] = p[last_time] + ' %s'%text
                    last_time = time
                except KeyError:
                    pass
            else:
                try:
                    p[last_time] = p[last_time] + ' %s '%text
                except KeyError:
                    pass
        speach[num] = {float(timestamp.replace(':', '.')): p}
        timestamps.append(float(timestamp.replace(':', '.')))
    return speach, timestamps


def extract_paras_fragments(speach,timestamps):
    left = 0
    final = {}
    for value in speach.values():
        # print timestamps[left]
        time = value.keys()[0]
        if left ==len(timestamps):
            final[left-1] = {timestamps[left-1]: dict(final[left-1][timestamps[left-1]], **value.values()[0])}
        elif time == timestamps[left]:
            final[left] = {timestamps[left]: value.values()[0]}
            left += 1
        elif (timestamps[left-1] < time) and (time < timestamps[left]) and left > 0:
            final[left-1] = {timestamps[left-1]: dict(final[left-1][timestamps[left-1]], **value.values()[0])}
        elif  1 < left < len(timestamps):
            final[left-1] = {timestamps[left-1]: dict(final[left-1][timestamps[left-1]], **value.values()[0])}
            print "left is %s ,else:%s ,value:%s"%(timestamps[left],time,value)
    return final

#print en_final


def merge_rus_eng(en_final,ru_final):
    merge = []
    for key ,text in en_final.iteritems():

        en_items = text.values()[0]
        ru_items = ru_final[key].values()[0]
        if len(en_items) == len(ru_items):
            min_items = en_items
            max_items = ru_items
        else:
            min_items = en_items if len(en_items) < len(ru_items) else ru_items
            max_items = en_items if len(en_items) > len(ru_items) else ru_items
        max_timestamps = sorted(max_items.keys())
        min_timestamps = sorted(min_items.keys())
        for idx, min_time in enumerate(min_timestamps):
            if idx+1 == len(min_timestamps):
                if is_RUS(max_items,max_timestamps[-1]):
                    min_items[min_time] = min_items[min_time] + u"\n" +max_items[max_timestamps[-1]]+' '
                else:
                    min_items[min_time] = max_items[max_timestamps[-1]] + u"\n" + min_items[min_time]+' '
            else:
                for max_time in max_timestamps:
                    if  max_time==min_time:
                        if is_RUS(max_items,max_time):
                            min_items[min_time] = min_items[min_time] + u"\n" + max_items[max_time]+' '
                        else:
                            min_items[min_time] = max_items[max_time] + u"\n" + min_items[min_time]+' '
                    elif (abs(max_time - min_time ) <= 1000) and \
                         (abs(max_time-min_timestamps[idx+1]) <= 1000) and\
                        (max_items[max_time]  not in min_items[min_time]):
                        if is_RUS(max_items,max_time):
                            min_items[min_time] = min_items[min_time] + u"\n" + max_items[max_time]+' '
                        else:
                            min_items[min_time] = max_items[max_time] + u"\n" + min_items[min_time]+' '
                    elif min_time < max_time < min_timestamps[idx+1] and\
                            (max_items[max_time] not in min_items[min_time]):
                        if is_RUS(max_items,max_time):
                            min_items[min_time] = min_items[min_time] + u"\n" + max_items[max_time]+' '
                        else:
                            min_items[min_time] = max_items[max_time] + u"\n" + min_items[min_time]+' '

                         #print max_time
        min_items = sorted(min_items.iteritems(), key=lambda d: d[0])
        merge.append(min_items)
    return merge


def generatefile(merge,url):
    filename = url.replace("http://www.ted.com/talks/",'')
    with open("%s.txt"%filename,"wb") as f:
        for text in merge:
            f.write("\n\n\n")
            for txt in text:
                txt[1].strip()
                f.write(txt[1] + u"\n\n")


def main():
    url = raw_input("Input url(e.g:http://www.ted.com/talks/keith_barry_does_brain_magic):")
    print "Downloading page"
    en_paras, ru_paras = paras_soup(url)
    print "Extracting paras "
    en_speach, en_timestamps = extract_paras(en_paras)
    ru_speach, ru_timestamps = extract_paras(ru_paras)
    timestamps = sorted(list(set(ru_timestamps) & set(en_timestamps)))
    print "Extracting fragments "
    en_final = extract_paras_fragments(en_speach, timestamps)
    ru_final = extract_paras_fragments(ru_speach, timestamps)
    print "Merging rus and eng fragments"
    merge = merge_rus_eng(en_final,ru_final)
    print "Generating file"
    generatefile(merge, url)

if __name__=="__main__":
    main()
    print "Done!"

